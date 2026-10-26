"""SentinelX AI - Domain Schemas and Data Contracts (Phase 1)

Canonical exports for all typed Pydantic data contracts across SentinelX subsystems.
"""

from .common import (
    ActionType,
    AgentName,
    AgentRunStatus,
    ApprovalStatus,
    EvidenceType,
    ExecutionMode,
    ExperimentMode,
    ExperimentStatus,
    IncidentStatus,
    SafetyResult,
    SentinelBaseModel,
    SeverityLevel,
    ensure_utc_datetime,
)
from .events import (
    EventBatchIngest,
    EventFilterParams,
    NormalizedEvent,
)
from .detections import (
    DetectionResult,
)
from .evidence import (
    EvidenceReference,
)
from .agents import (
    AgentRunResult,
    AgentTask,
)
from .incidents import (
    IncidentCreate,
    IncidentState,
    IncidentUpdate,
    VALID_TRANSITIONS,
    can_transition,
)
from .decisions import (
    ApprovalRecord,
    ResponseDecision,
    SimulationOutcome,
)
from .experiments import (
    ExperimentConfig,
    ExperimentResult,
)

__all__ = [
    # Enums & Common
    "ActionType",
    "AgentName",
    "AgentRunStatus",
    "ApprovalStatus",
    "EvidenceType",
    "ExecutionMode",
    "ExperimentMode",
    "ExperimentStatus",
    "IncidentStatus",
    "SafetyResult",
    "SentinelBaseModel",
    "SeverityLevel",
    "ensure_utc_datetime",
    # Events
    "EventBatchIngest",
    "EventFilterParams",
    "NormalizedEvent",
    # Detections
    "DetectionResult",
    # Evidence
    "EvidenceReference",
    # Agents
    "AgentRunResult",
    "AgentTask",
    # Incidents
    "IncidentCreate",
    "IncidentState",
    "IncidentUpdate",
    "VALID_TRANSITIONS",
    "can_transition",
    # Decisions & Approval & Simulation
    "ApprovalRecord",
    "ResponseDecision",
    "SimulationOutcome",
    # Experiments
    "ExperimentConfig",
    "ExperimentResult",
]
