"""SentinelX AI - Fixed Defensive Action Catalogue

Defines the closed, strictly bounded catalogue of allowed defensive actions.
CRITICAL SAFETY BOUNDARY: No model, agent, or policy can invent or execute actions
outside this catalogue.
"""

from typing import Dict, List, Optional, Union
from pydantic import BaseModel, Field
from app.schemas.common import ActionType


class ActionSpec(BaseModel):
    """Specification and safety parameters for a permitted defensive action."""
    action_type: ActionType
    title: str
    description: str
    operational_disruption_cost: float = Field(ge=0.0)
    is_reversible: bool = True
    requires_human_approval: bool = False
    min_risk_prerequisite: float = Field(default=0.0, ge=0.0, le=1.0)


# Fixed Catalogue of Permitted Defensive Actions
ACTION_CATALOGUE: Dict[ActionType, ActionSpec] = {
    ActionType.RAISE_ALERT: ActionSpec(
        action_type=ActionType.RAISE_ALERT,
        title="Raise Security Alert",
        description="Notify security analysts and log an alert in the audit record.",
        operational_disruption_cost=0.0,
        is_reversible=True,
        requires_human_approval=False,
        min_risk_prerequisite=0.0,
    ),
    ActionType.INCREASE_MONITORING: ActionSpec(
        action_type=ActionType.INCREASE_MONITORING,
        title="Increase Packet Monitoring",
        description="Temporarily elevate capture granularity and sampling rate on target asset.",
        operational_disruption_cost=1.5,
        is_reversible=True,
        requires_human_approval=False,
        min_risk_prerequisite=0.30,
    ),
    ActionType.ESCALATE_FOR_APPROVAL: ActionSpec(
        action_type=ActionType.ESCALATE_FOR_APPROVAL,
        title="Escalate For Human Approval",
        description="Flag incident for explicit analyst review and response sign-off.",
        operational_disruption_cost=0.0,
        is_reversible=True,
        requires_human_approval=False,
        min_risk_prerequisite=0.50,
    ),
    ActionType.SIMULATE_BLOCK: ActionSpec(
        action_type=ActionType.SIMULATE_BLOCK,
        title="Simulated Host/Port Block",
        description="Apply a containment block strictly inside the simulated environment boundary.",
        operational_disruption_cost=12.0,
        is_reversible=True,
        requires_human_approval=True,  # Mandatory human sign-off
        min_risk_prerequisite=0.60,
    ),
}


def get_action_spec(action: Union[ActionType, str]) -> Optional[ActionSpec]:
    """Retrieve the action specification if in catalogue, else None."""
    try:
        act_enum = ActionType(action) if isinstance(action, str) else action
        return ACTION_CATALOGUE.get(act_enum)
    except ValueError:
        return None


def is_allowed_action(action: str) -> bool:
    """Return True if action string is a member of the fixed catalogue."""
    return get_action_spec(action) is not None
