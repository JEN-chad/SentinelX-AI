"""SentinelX AI - Common Enums, Types, and Shared Schema Validators

Defines canonical system enums, identifier standards, and UTC datetime validators.
"""

from datetime import datetime, timezone
from enum import Enum
import re
from typing import Any
from pydantic import BaseModel, ConfigDict, field_validator


class IncidentStatus(str, Enum):
    RECEIVED = "received"
    VALIDATED = "validated"
    SCORED = "scored"
    INVESTIGATING = "investigating"
    RISK_ASSESSED = "risk_assessed"
    RESPONSE_PROPOSED = "response_proposed"
    APPROVAL_REQUIRED = "approval_required"
    SIMULATING = "simulating"
    OUTCOME_RECORDED = "outcome_recorded"
    CLOSED = "closed"
    REJECTED = "rejected"
    ERROR = "error"


class SeverityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AgentName(str, Enum):
    DETECTION_AGENT = "detection_agent"
    INVESTIGATION_AGENT = "investigation_agent"
    RISK_AGENT = "risk_agent"
    MITIGATION_AGENT = "mitigation_agent"
    RL_POLICY_COMPONENT = "rl_policy_component"


class ActionType(str, Enum):
    RAISE_ALERT = "raise_alert"
    INCREASE_MONITORING = "increase_monitoring"
    ESCALATE_FOR_APPROVAL = "escalate_for_approval"
    SIMULATE_BLOCK = "simulate_block"


class ExecutionMode(str, Enum):
    SIMULATION = "simulation"


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class SafetyResult(str, Enum):
    PERMITTED = "permitted"
    REQUIRES_APPROVAL = "requires_approval"
    REJECTED = "rejected"


class EvidenceType(str, Enum):
    OBSERVED_EVENT = "observed_event"
    DERIVED_FEATURE = "derived_feature"
    ANOMALY_SIGNAL = "anomaly_signal"
    TIMELINE_CLUSTER = "timeline_cluster"
    MODEL_SCORE = "model_score"


class ExperimentMode(str, Enum):
    TRAINING = "training"
    EVALUATION = "evaluation"


class ExperimentStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentRunStatus(str, Enum):
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


def ensure_utc_datetime(dt: Any) -> datetime:
    """Validate that datetime is timezone-aware and set to UTC."""
    if not isinstance(dt, datetime):
        raise TypeError(f"Expected datetime object, received {type(dt).__name__}")
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        raise ValueError("Datetime must be timezone-aware (UTC). Naive datetime is prohibited.")
    # Convert to standard UTC
    return dt.astimezone(timezone.utc)


class SentinelBaseModel(BaseModel):
    """Base Pydantic model with strict validation and deterministic serialization."""
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        str_strip_whitespace=True,
        use_enum_values=True
    )
