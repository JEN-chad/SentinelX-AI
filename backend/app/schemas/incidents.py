"""SentinelX AI - Incident Lifecycle and State Schemas

Defines core incident contracts and validated state transition boundaries.
"""

from datetime import datetime
from typing import Dict, List, Optional, Set
from pydantic import Field, field_validator, model_validator
from .common import (
    ActionType,
    IncidentStatus,
    SentinelBaseModel,
    SeverityLevel,
    ensure_utc_datetime,
)
from .evidence import EvidenceReference
from .agents import AgentRunResult
from .events import ID_PATTERN


# Allowed incident state transitions enforcing lifecycle integrity (Section 5 of architecture.md)
VALID_TRANSITIONS: Dict[IncidentStatus, Set[IncidentStatus]] = {
    IncidentStatus.RECEIVED: {IncidentStatus.VALIDATED, IncidentStatus.REJECTED, IncidentStatus.ERROR},
    IncidentStatus.VALIDATED: {IncidentStatus.SCORED, IncidentStatus.REJECTED, IncidentStatus.ERROR},
    IncidentStatus.SCORED: {IncidentStatus.INVESTIGATING, IncidentStatus.REJECTED, IncidentStatus.ERROR},
    IncidentStatus.INVESTIGATING: {IncidentStatus.RISK_ASSESSED, IncidentStatus.ERROR},
    IncidentStatus.RISK_ASSESSED: {IncidentStatus.RESPONSE_PROPOSED, IncidentStatus.ERROR},
    IncidentStatus.RESPONSE_PROPOSED: {
        IncidentStatus.APPROVAL_REQUIRED,
        IncidentStatus.SIMULATING,
        IncidentStatus.CLOSED,
        IncidentStatus.ERROR,
    },
    IncidentStatus.APPROVAL_REQUIRED: {
        IncidentStatus.SIMULATING,
        IncidentStatus.CLOSED,
        IncidentStatus.ERROR,
    },
    IncidentStatus.SIMULATING: {IncidentStatus.OUTCOME_RECORDED, IncidentStatus.ERROR},
    IncidentStatus.OUTCOME_RECORDED: {IncidentStatus.CLOSED, IncidentStatus.ERROR},
    IncidentStatus.REJECTED: {IncidentStatus.CLOSED, IncidentStatus.ERROR},
    IncidentStatus.ERROR: {IncidentStatus.CLOSED},
    IncidentStatus.CLOSED: set(),
}


def can_transition(current: IncidentStatus, target: IncidentStatus) -> bool:
    """Evaluate whether an incident state transition is permissible."""
    return target in VALID_TRANSITIONS.get(current, set())


class IncidentState(SentinelBaseModel):
    """Canonical representation of an incident record across its lifecycle."""
    incident_id: str = Field(
        ...,
        description="Unique identifier for the incident (e.g. inc-demo-0001)"
    )
    title: str = Field(
        ...,
        min_length=3,
        max_length=150,
        description="Descriptive title of the incident"
    )
    status: IncidentStatus = Field(
        default=IncidentStatus.RECEIVED,
        description="Current state within incident lifecycle"
    )
    severity: SeverityLevel = Field(
        default=SeverityLevel.LOW,
        description="Assessed severity classification"
    )
    risk_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Normalized risk metric in [0.0, 1.0]"
    )
    event_ids: List[str] = Field(
        ...,
        min_length=1,
        description="List of primary and correlated event IDs backing this incident"
    )
    evidence: List[EvidenceReference] = Field(
        default_factory=list,
        description="Aggregated chain of evidence"
    )
    agent_results: List[AgentRunResult] = Field(
        default_factory=list,
        description="Execution trace and outputs from specialized agents"
    )
    allowed_actions: List[ActionType] = Field(
        default_factory=lambda: [
            ActionType.RAISE_ALERT,
            ActionType.INCREASE_MONITORING,
            ActionType.ESCALATE_FOR_APPROVAL,
            ActionType.SIMULATE_BLOCK,
        ],
        description="Catalogue of currently permitted defensive responses"
    )
    created_at: datetime = Field(
        ...,
        description="Creation timestamp in UTC"
    )
    updated_at: datetime = Field(
        ...,
        description="Last update timestamp in UTC"
    )
    schema_version: str = Field(
        default="v1",
        description="Contract version identifier"
    )

    @field_validator("incident_id")
    @classmethod
    def validate_incident_id(cls, value: str) -> str:
        if not ID_PATTERN.match(value):
            raise ValueError(f"Invalid incident_id format '{value}'.")
        return value

    @field_validator("event_ids")
    @classmethod
    def validate_event_ids(cls, values: List[str]) -> List[str]:
        for eid in values:
            if not ID_PATTERN.match(eid):
                raise ValueError(f"Invalid event_id in incident '{eid}'.")
        return values

    @field_validator("created_at", "updated_at")
    @classmethod
    def validate_utc(cls, value: datetime) -> datetime:
        return ensure_utc_datetime(value)

    @model_validator(mode="after")
    def validate_timestamp_sequence(self) -> "IncidentState":
        if self.updated_at < self.created_at:
            raise ValueError("updated_at cannot be prior to created_at.")
        return self


class IncidentCreate(SentinelBaseModel):
    """Payload for creating a candidate incident from detection alert."""
    incident_id: str
    title: str = Field(..., min_length=3, max_length=150)
    initial_event_id: str
    severity: SeverityLevel = SeverityLevel.LOW
    risk_score: float = Field(default=0.0, ge=0.0, le=1.0)
    created_at: datetime

    @field_validator("incident_id", "initial_event_id")
    @classmethod
    def validate_ids(cls, value: str) -> str:
        if not ID_PATTERN.match(value):
            raise ValueError(f"Invalid identifier format '{value}'.")
        return value

    @field_validator("created_at")
    @classmethod
    def validate_utc(cls, value: datetime) -> datetime:
        return ensure_utc_datetime(value)


class IncidentUpdate(SentinelBaseModel):
    """Safe state transition and enrichment payload."""
    target_status: Optional[IncidentStatus] = None
    severity: Optional[SeverityLevel] = None
    risk_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    add_event_ids: Optional[List[str]] = None
    add_evidence: Optional[List[EvidenceReference]] = None
    add_agent_result: Optional[AgentRunResult] = None
    updated_at: datetime

    @field_validator("updated_at")
    @classmethod
    def validate_utc(cls, value: datetime) -> datetime:
        return ensure_utc_datetime(value)
