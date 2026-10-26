"""SentinelX AI - Threat Detection Schemas

Contracts for ML inference outputs, anomaly detectors, and feature attributions.
"""

from datetime import datetime
import math
from typing import Dict, List, Optional
from pydantic import Field, field_validator, model_validator
from .common import SentinelBaseModel, ensure_utc_datetime
from .events import ID_PATTERN


class DetectionResult(SentinelBaseModel):
    """Output contract produced by Threat Detection Service."""
    detection_id: str = Field(
        ...,
        description="Unique detection record identifier (e.g. det-0001)"
    )
    event_id: str = Field(
        ...,
        description="Reference to the analyzed normalized event"
    )
    predicted_class: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="Predicted threat class (e.g. 'benign', 'suspicious', 'ddos', 'portscan')"
    )
    class_scores: Dict[str, float] = Field(
        ...,
        description="Class probability distribution mapping class name to score in [0.0, 1.0]"
    )
    anomaly_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Unsupervised anomaly detector score in [0.0, 1.0], if available"
    )
    model_version: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="Model architecture and version tag (e.g. 'rf-baseline-v1.0')"
    )
    evidence_feature_names: List[str] = Field(
        default_factory=list,
        description="Key features that contributed to this prediction"
    )
    inference_duration_ms: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Inference execution latency in milliseconds"
    )
    calibrated: bool = Field(
        default=False,
        description="Flag indicating whether model probability has been empirically calibrated"
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp when detection result was generated in UTC"
    )

    @field_validator("detection_id", "event_id")
    @classmethod
    def validate_ids(cls, value: str) -> str:
        if not ID_PATTERN.match(value):
            raise ValueError(f"Invalid identifier format '{value}'.")
        return value

    @field_validator("created_at")
    @classmethod
    def validate_utc(cls, value: datetime) -> datetime:
        return ensure_utc_datetime(value)

    @field_validator("class_scores")
    @classmethod
    def validate_scores_bounds(cls, value: Dict[str, float]) -> Dict[str, float]:
        if not value:
            raise ValueError("class_scores dictionary cannot be empty.")
        for class_name, score in value.items():
            if not isinstance(score, (int, float)):
                raise ValueError(f"Score for class '{class_name}' must be numeric.")
            if score < 0.0 or score > 1.0:
                raise ValueError(f"Score for class '{class_name}' ({score}) must be between 0.0 and 1.0.")
            if math.isnan(score) or math.isinf(score):
                raise ValueError(f"Score for class '{class_name}' cannot be NaN or Infinite.")
        return value

    @model_validator(mode="after")
    def validate_probability_sum(self) -> "DetectionResult":
        # Check that class probabilities sum approximately to 1.0 (with tolerance for floating point)
        total_prob = sum(self.class_scores.values())
        if abs(total_prob - 1.0) > 0.08:
            raise ValueError(
                f"Sum of class probabilities must be approximately 1.0. Current sum: {total_prob:.4f}"
            )
        if self.predicted_class not in self.class_scores:
            raise ValueError(
                f"predicted_class '{self.predicted_class}' must be present in class_scores."
            )
        return self
