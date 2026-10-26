"""SentinelX AI - Deterministic Safety Gate

Independent server-side safety validator operating outside the control of LLMs,
agents, and RL policies. Guarantees fail-safe confinement.
"""

from typing import List, Optional, Union
from pydantic import BaseModel, Field

from app.config import settings
from app.schemas.common import ActionType, ExecutionMode, SafetyResult
from .action_catalogue import ACTION_CATALOGUE, get_action_spec


class SafetyDecision(BaseModel):
    """Result of deterministic policy gate validation."""
    action: Optional[ActionType] = None
    safety_result: SafetyResult
    reason_codes: List[str] = Field(default_factory=list)
    execution_mode: ExecutionMode = ExecutionMode.SIMULATION
    is_approved: bool = False


class DeterministicSafetyGate:
    """Deterministic validator enforcing action allowlists and prerequisite rules."""

    @staticmethod
    def evaluate(
        action: Union[ActionType, str],
        incident_risk_score: float,
        is_human_approved: bool = False,
        execution_mode: Optional[str] = None,
    ) -> SafetyDecision:
        """Validate a proposed action against deterministic safety rules."""
        mode = execution_mode or settings.execution_mode
        reason_codes: List[str] = []

        # Rule 1: CRITICAL SAFETY BOUNDARY - Reject non-simulation execution
        if mode != ExecutionMode.SIMULATION.value:
            return SafetyDecision(
                action=None,
                safety_result=SafetyResult.REJECTED,
                reason_codes=["SAFETY_VIOLATION_NON_SIMULATION_MODE"],
                execution_mode=ExecutionMode.SIMULATION,
                is_approved=False,
            )

        # Rule 2: ACTION ALLOWLIST - Reject unknown actions
        spec = get_action_spec(action)
        if not spec:
            return SafetyDecision(
                action=None,
                safety_result=SafetyResult.REJECTED,
                reason_codes=[f"UNKNOWN_ACTION_REJECTED: '{action}' not in action catalogue."],
                execution_mode=ExecutionMode.SIMULATION,
                is_approved=False,
            )

        # Rule 3: PREREQUISITE CHECK - Validate risk threshold
        if incident_risk_score < spec.min_risk_prerequisite:
            reason_codes.append(
                f"PREREQUISITE_FAILED: Action '{spec.action_type.value}' requires minimum risk "
                f"{spec.min_risk_prerequisite:.2f}, but incident risk is {incident_risk_score:.2f}."
            )
            return SafetyDecision(
                action=spec.action_type,
                safety_result=SafetyResult.REJECTED,
                reason_codes=reason_codes,
                execution_mode=ExecutionMode.SIMULATION,
                is_approved=False,
            )

        # Rule 4: HUMAN APPROVAL GATE - Disruptive containment requires approval
        if spec.requires_human_approval and not is_human_approved:
            reason_codes.append(
                f"APPROVAL_REQUIRED: Action '{spec.action_type.value}' carries operational disruption "
                f"cost ({spec.operational_disruption_cost}) and requires explicit human analyst approval."
            )
            return SafetyDecision(
                action=spec.action_type,
                safety_result=SafetyResult.REQUIRES_APPROVAL,
                reason_codes=reason_codes,
                execution_mode=ExecutionMode.SIMULATION,
                is_approved=False,
            )

        # Action is completely permitted for simulation
        reason_codes.append(f"ACTION_PERMITTED: Permitted for execution under simulation mode.")
        return SafetyDecision(
            action=spec.action_type,
            safety_result=SafetyResult.PERMITTED,
            reason_codes=reason_codes,
            execution_mode=ExecutionMode.SIMULATION,
            is_approved=is_human_approved or not spec.requires_human_approval,
        )
