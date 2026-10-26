"""SentinelX AI - Threat Detection Inference Service

Loads versioned model artifacts and scores normalized events with full schema validation.
"""

from datetime import datetime, timezone
from pathlib import Path
import time
from typing import Any, Dict, Optional, Union
import joblib
import numpy as np

from app.schemas.detections import DetectionResult
from app.schemas.events import NormalizedEvent
from .explainability import rank_explanatory_features
from .feature_schema import CANONICAL_FEATURES, extract_feature_vector
from .train import DEFAULT_ARTIFACT_PATH, train_baseline_model


class ThreatDetectionService:
    """Service executing trained threat classification models on normalized events."""

    def __init__(self, artifact_path: Optional[Union[str, Path]] = None):
        self.artifact_path = Path(artifact_path or DEFAULT_ARTIFACT_PATH)
        self.bundle: Optional[Dict[str, Any]] = None
        self._load_or_train()

    def _load_or_train(self) -> None:
        """Load model bundle from disk; if missing, train a baseline artifact automatically."""
        if not self.artifact_path.exists():
            train_baseline_model(output_path=self.artifact_path)

        self.bundle = joblib.load(self.artifact_path)
        self.model = self.bundle["model"]
        self.preprocessor = self.bundle["preprocessor"]
        self.classes = list(self.bundle["classes"])
        self.model_version = self.bundle.get("model_version", "rf-baseline-v1.0.0")
        self.feature_names = self.bundle.get("feature_names", CANONICAL_FEATURES)
        self.feature_importances = self.bundle.get("feature_importances", [])

    def score_event(self, event: NormalizedEvent) -> DetectionResult:
        """Score a NormalizedEvent and return a validated DetectionResult schema instance."""
        start_time = time.perf_counter()

        # 1. Enforce feature ordering and completeness
        raw_vector = extract_feature_vector(event.features)

        # 2. Apply preprocessing fitted on training set
        norm_vector = self.preprocessor.transform(raw_vector)
        matrix = norm_vector.reshape(1, -1)

        # 3. Predict class and class probabilities
        predicted_class = str(self.model.predict(matrix)[0])
        probabilities = self.model.predict_proba(matrix)[0]

        class_scores: Dict[str, float] = {}
        for cls_name, prob in zip(self.classes, probabilities):
            class_scores[cls_name] = float(round(prob, 4))

        # 4. Anomaly score: 1.0 - p(BENIGN) if BENIGN in classes, else max attack probability
        if "BENIGN" in class_scores:
            anomaly_score = float(round(1.0 - class_scores["BENIGN"], 4))
        else:
            anomaly_score = float(round(max(probabilities), 4))

        # 5. Extract top explanatory feature names
        evidence_features = rank_explanatory_features(
            feature_vector=raw_vector,
            feature_names=self.feature_names,
            feature_importances=self.feature_importances,
            top_k=3,
        )

        duration_ms = float(round((time.perf_counter() - start_time) * 1000.0, 3))
        now = datetime.now(timezone.utc)

        return DetectionResult(
            detection_id=f"det-{event.event_id.replace('evt-', '')}",
            event_id=event.event_id,
            predicted_class=predicted_class,
            class_scores=class_scores,
            anomaly_score=anomaly_score,
            model_version=self.model_version,
            evidence_feature_names=evidence_features,
            inference_duration_ms=duration_ms,
            calibrated=True,
            created_at=now,
        )
