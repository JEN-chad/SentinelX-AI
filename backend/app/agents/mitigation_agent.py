"""SentinelX AI - Mitigation Planning Agent

Specialized agent proposing ranked defensive actions from the fixed catalogue.
CRITICAL SAFETY BOUNDARY: All proposed actions are strictly validated against
the Deterministic Safety Gate allowlist.
"""

from datetime import datetime, timezone
import time
from typing import Any, Dict, List, Optional

from app.safety.action_catalogue import get_action_spec
from app.safety.policy_gate import DeterministicSafetyGate, SafetyDecision
from app.schemas.agents import AgentRunResult, AgentTask
from app.schemas.common import ActionType, AgentName, AgentRunStatus, SafetyResult
from app.schemas.evidence import EvidenceReference, EvidenceType
from .base import BaseAgent


class MitigationPlanningAgent(BaseAgent):
    """Agent proposing and ranking safe defensive mitigations from the fixed action catalogue."""

    def __init__(self, safety_gate: Optional[DeterministicSafetyGate] = None, version: str = "1.0.0"):
        super().__init__(agent_name=AgentName.MITIGATION_AGENT, version=version)
        self.safety_gate = safety_gate or DeterministicSafetyGate()

    def run(self, task: AgentTask, context: Dict[str, Any]) -> AgentRunResult:
        start_time = time.perf_counter()
        now = datetime.now(timezone.utc)
        run_id = f"run-mit-{now.strftime('%Y%m%d%H%M%S%f')[-8:]}"

        risk_score: float = float(context.get("risk_score", 0.5))
        target_asset: str = str(context.get("target_asset", "192.168.10.5"))
        is_human_approved: bool = bool(context.get("is_human_approved", False))

        # 1. Select candidate actions from fixed catalogue based on risk tier
        if risk_score >= 0.60:
            candidates = [
                ActionType.SIMULATE_BLOCK,
                ActionType.ESCALATE_FOR_APPROVAL,
                ActionType.INCREASE_MONITORING,
            ]
        elif risk_score >= 0.35:
            candidates = [
                ActionType.INCREASE_MONITORING,
                ActionType.RAISE_ALERT,
            ]
        else:
            candidates = [ActionType.RAISE_ALERT]

        # 2. Evaluate each proposed action through the deterministic safety gate
        evaluated_decisions: List[SafetyDecision] = []
        valid_proposals: List[ActionType] = []

        for action in candidates:
            dec = self.safety_gate.evaluate(
                action=action,
                incident_risk_score=risk_score,
                is_human_approved=is_human_approved,
            )
            evaluated_decisions.append(dec)
            if dec.safety_result in [SafetyResult.PERMITTED, SafetyResult.REQUIRES_APPROVAL]:
                valid_proposals.append(action)

        # 3. Create evidence finding
        primary_action = valid_proposals[0] if valid_proposals else ActionType.RAISE_ALERT
        primary_spec = get_action_spec(primary_action)
        disruption_cost = primary_spec.operational_disruption_cost if primary_spec else 0.0

        evidence = EvidenceReference(
            evidence_id=f"evd-{run_id}-mit",
            supporting_event_ids=context.get("supporting_event_ids", []),
            evidence_type=EvidenceType.DERIVED_FEATURE,
            is_inferred=True,
            description=(
                f"Proposed defensive response '{primary_action.value}' (disruption cost {disruption_cost}). "
                f"Safety gate evaluation: {evaluated_decisions[0].safety_result.value.upper()}."
            ),
            confidence=0.92,
            source_component="mitigation_agent",
            metadata={
                "recommended_action": primary_action.value,
                "disruption_cost": disruption_cost,
                "requires_approval": primary_spec.requires_human_approval if primary_spec else False,
            },
            timestamp=now,
        )

        duration_ms = float(round((time.perf_counter() - start_time) * 1000.0, 3))

        summary = (
            f"Recommended primary action: '{primary_action.value}'. "
            f"Safety evaluation: {evaluated_decisions[0].safety_result.value.upper()}. "
            f"Evaluated {len(valid_proposals)} permitted catalogue actions."
        )

        return AgentRunResult(
            agent_run_id=run_id,
            agent_name=self.agent_name,
            incident_id=task.incident_id,
            status=AgentRunStatus.COMPLETED,
            findings=[evidence],
            proposed_actions=valid_proposals,
            conflict_flags=[],
            summary=summary,
            structured_output={
                "recommended_action": primary_action.value,
                "disruption_cost": disruption_cost,
                "safety_decisions": [d.model_dump(mode="json") for d in evaluated_decisions],
            },
            duration_ms=duration_ms,
            created_at=now,
        )
