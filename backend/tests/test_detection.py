"""Tests for Phase 3: Feature Engineering and Baseline Threat Detector."""

from datetime import datetime, timezone
import pytest
import numpy as np

from app.detection.feature_schema import CANONICAL_FEATURES, extract_feature_vector
from app.detection.preprocessing import FeaturePreprocessor
from app.detection.train import train_baseline_model
from app.detection.inference import ThreatDetectionService
from app.schemas.detections import DetectionResult
from app.schemas.events import NormalizedEvent


@pytest.fixture
def sample_normalized_event():
    return NormalizedEvent(
        event_id="evt-test-0001",
        event_time=datetime.now(timezone.utc),
        ingested_at=datetime.now(timezone.utc),
        source="test_source",
        source_asset="192.168.10.50",
        target_asset="192.168.10.5",
        event_type="flow_record",
        features={
            "flow_duration": 124800.0,
            "total_fwd_packets": 68,
            "total_bwd_packets": 1,
            "flow_bytes_per_sec": 14820.5,
            "fwd_packet_length_mean": 42.0,
            "syn_flag_count": 1,
            "rst_flag_count": 0,
            "bwd_packets_per_sec": 8.0,
            "destination_port": 80,
        },
        schema_version="v1",
    )


def test_feature_vector_extraction(sample_normalized_event):
    """Ensure vector is extracted in exact canonical order."""
    vec = extract_feature_vector(sample_normalized_event.features)
    assert isinstance(vec, np.ndarray)
    assert len(vec) == len(CANONICAL_FEATURES)
    assert vec[0] == 124800.0
    assert vec[-1] == 80.0


def test_feature_vector_missing_feature():
    """Ensure missing canonical features raise controlled validation error."""
    bad_features = {"flow_duration": 100}
    with pytest.raises(ValueError, match="Missing required canonical features"):
        extract_feature_vector(bad_features)


def test_preprocessor_fit_transform():
    """Verify preprocessor normalizes cleanly without errors."""
    X = np.array([
        [100.0, 10.0, 5.0, 500.0, 40.0, 1.0, 0.0, 2.0, 80.0],
        [200.0, 20.0, 10.0, 1000.0, 80.0, 0.0, 0.0, 4.0, 443.0],
    ], dtype=np.float32)

    preproc = FeaturePreprocessor()
    X_norm = preproc.fit_transform(X)
    assert X_norm.shape == X.shape
    assert preproc.is_fitted

    # Single vector transform
    single_norm = preproc.transform(X[0])
    assert single_norm.shape == (9,)


def test_training_and_inference(tmp_path, sample_normalized_event):
    """Verify training a baseline model and scoring an event."""
    artifact_path = tmp_path / "test_detector.joblib"
    bundle = train_baseline_model(output_path=artifact_path)

    assert artifact_path.exists()
    assert "model" in bundle
    assert "metrics" in bundle
    assert bundle["model_version"] == "rf-baseline-v1.0.0"

    # Load in inference service
    service = ThreatDetectionService(artifact_path=artifact_path)
    result = service.score_event(sample_normalized_event)

    assert isinstance(result, DetectionResult)
    assert result.event_id == sample_normalized_event.event_id
    assert result.predicted_class in service.classes
    assert 0.0 <= result.anomaly_score <= 1.0
    assert len(result.evidence_feature_names) > 0
    assert result.inference_duration_ms > 0
