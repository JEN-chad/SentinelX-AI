"""Tests for Threat Detection Schemas and Inference Contracts."""

from datetime import datetime, timezone
import pytest
from pydantic import ValidationError
from app.schemas.detections import DetectionResult


def test_valid_detection_parses(valid_detection_dict):
    detection = DetectionResult.model_validate(valid_detection_dict)
    assert detection.detection_id == "det-demo-0001"
    assert detection.predicted_class == "suspicious"
    assert detection.class_scores["suspicious"] == 0.92
    assert detection.anomaly_score == 0.85
    assert detection.inference_duration_ms == 1.45
    assert detection.created_at.tzinfo == timezone.utc


def test_reject_unnormalized_probabilities(valid_detection_dict):
    """Reject probabilities that do not sum approximately to 1.0."""
    invalid_dict = valid_detection_dict.copy()
    invalid_dict["class_scores"] = {
        "benign": 0.50,
        "suspicious": 0.80  # Sum is 1.30, violating probability definition
    }
    with pytest.raises(ValidationError, match="Sum of class probabilities must be approximately 1.0"):
        DetectionResult.model_validate(invalid_dict)


def test_reject_out_of_bounds_scores(valid_detection_dict):
    invalid_dict = valid_detection_dict.copy()
    invalid_dict["class_scores"] = {
        "benign": -0.1,
        "suspicious": 1.1
    }
    with pytest.raises(ValidationError, match="must be between 0.0 and 1.0"):
        DetectionResult.model_validate(invalid_dict)


def test_reject_missing_predicted_class_in_scores(valid_detection_dict):
    invalid_dict = valid_detection_dict.copy()
    invalid_dict["predicted_class"] = "malicious"  # Not in class_scores (benign, suspicious)
    with pytest.raises(ValidationError, match="must be present in class_scores"):
        DetectionResult.model_validate(invalid_dict)


def test_reject_anomaly_score_out_of_range(valid_detection_dict):
    invalid_dict = valid_detection_dict.copy()
    invalid_dict["anomaly_score"] = 1.5
    with pytest.raises(ValidationError):
        DetectionResult.model_validate(invalid_dict)


def test_reject_negative_inference_duration(valid_detection_dict):
    invalid_dict = valid_detection_dict.copy()
    invalid_dict["inference_duration_ms"] = -5.0
    with pytest.raises(ValidationError):
        DetectionResult.model_validate(invalid_dict)
