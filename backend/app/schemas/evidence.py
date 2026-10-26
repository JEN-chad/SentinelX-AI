"""SentinelX AI - Evidence Reference Schemas

Formal provenance tracking ensuring all agent reasoning and risk assessments
are backed by traceable event IDs and explicit distinction between observed
facts and inferred findings.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import Field, field_validator, model_validator
from .common import EvidenceType, SentinelBaseModel, ensure_utc_datetime
from .events import ID_PATTERN


class EvidenceReference(SentinelBaseModel):
    """Traceable unit of evidence backing an alert, investigation, or risk claim."""
    evidence_id: str = Field(
        ...,
        description="Unique identifier for this evidence item (e.g. evd-0001)"
    )
    event_id: Optional[str] = Field(
        default=None,
        description="Primary normalized event ID directly linked to this evidence"
    )
    supporting_event_ids: List[str] = Field(
        default_factory=list,
        description="Additional event IDs forming the chain of evidence (e.g. for correlation clusters)"
    )
    evidence_type: EvidenceType = Field(
        ...,
        description="Classification of evidence (e.g. observed_event, anomaly_signal, timeline_cluster)"
    )
    is_inferred: bool = Field(
        ...,
        description="CRITICAL PROVENANCE: True if derived via agent reasoning/model; False if raw observed fact"
    )
    description: str = Field(
        ...,
        min_length=5,
        max_length=500,
        description="Human-readable explanation of the evidence"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence level in [0.0, 1.0] for this evidence item"
    )
    source_component: str = Field(
        ...,
        min_length=2,
        max_length=64,
        description="Agent or subsystem that recorded or derived this evidence"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Structured supporting metrics (e.g. threshold values, cluster size, flow stats)"
    )
    timestamp: datetime = Field(
        ...,
        description="Timestamp when evidence was observed or generated in UTC"
    )

    @field_validator("evidence_id")
    @classmethod
    def validate_evidence_id(cls, value: str) -> str:
        if not ID_PATTERN.match(value):
            raise ValueError(f"Invalid evidence_id format '{value}'.")
        return value

    @field_validator("event_id")
    @classmethod
    def validate_event_id(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and not ID_PATTERN.match(value):
            raise ValueError(f"Invalid event_id format '{value}'.")
        return value

    @field_validator("supporting_event_ids")
    @classmethod
    def validate_supporting_ids(cls, values: List[str]) -> List[str]:
        for item in values:
            if not ID_PATTERN.match(item):
                raise ValueError(f"Invalid supporting event ID format '{item}'.")
        return values

    @field_validator("timestamp")
    @classmethod
    def validate_utc(cls, value: datetime) -> datetime:
        return ensure_utc_datetime(value)

    @model_validator(mode="after")
    def validate_provenance(self) -> "EvidenceReference":
        # Observed events must directly link to an event_id or supporting event IDs
        if not self.is_inferred and not self.event_id and not self.supporting_event_ids:
            raise ValueError(
                "Observed evidence (is_inferred=False) must reference at least one event_id or supporting_event_id."
            )
        return self
