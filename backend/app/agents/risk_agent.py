"""SentinelX AI - Risk Assessment Agent

Specialized agent transforming model scores, asset criticality, and correlated
evidence into documented risk estimates and MITRE ATT&CK technique mappings.
CRITICAL SAFETY RULE: The Risk Assessment Agent NEVER executes mitigations directly.
"""

from datetime import datetime, timezone
import time
from typing import Any, Dict, List, Optional

from app.schemas.agents import AgentRunResult, AgentTask
from app.schemas.common import AgentName, AgentRunStatus
from app.schemas.evidence import EvidenceReference, EvidenceType
from app.services.risk_scoring import RiskScoringService
from .base import BaseAgent


class RiskAssessmentAgent(BaseAgent):
    """Agent calculating reproducible risk scores, severity classifications, and MITRE attributions."""

    def __init__(self, risk_service: Optional[RiskScoringService] = None, version: str = "1.0.0"):
        super().__init__(agent_name=AgentName.RISK_AGENT, version=version)
        self.risk_service = risk_service or RiskScoringService()

    def run(self, task: AgentTask, context: Dict[str, Any]) -> AgentRunResult:
        start_time = time.perf_counter()
        now = datetime.now(timezone.utc)
        run_id = f"run-rsk-{now.strftime('%Y%m%d%H%M%S%f')[-8:]}"

        detection_score: float = float(context.get("detection_score", 0.5))
        predicted_class: str = str(context.get("predicted_class", "Threat"))
        target_asset: str = str(context.get("target_asset", "192.168.10.5"))
        recurrence_count: int = int(context.get("recurrence_count", 1))
        telemetry_gaps: List[str] = context.get("telemetry_gaps", [])

        # 1. Compute transparent multi-factor risk score
        risk_score, severity, breakdown, mitre_info = self.risk_service.assess_risk(
            detection_score=detection_score,
            predicted_class=predicted_class,
            target_asset=target_asset,
            recurrence_count=recurrence_count,
            telemetry_gaps=telemetry_gaps,
        )

        # 2. Build evidence reference
        mitre_tech_str = mitre_info["technique_id"] if mitre_info else "T1498"
        evidence = EvidenceReference(
            evidence_id=f"evd-{run_id}-risk",
            supporting_event_ids=context.get("supporting_event_ids", []),
            evidence_type=EvidenceType.MODEL_SCORE,
            is_inferred=True,
            description=(
                f"Assessed incident risk as {risk_score:.2f} ({severity.value.upper()}) "
                f"based on detection confidence {detection_score:.2f}, recurrence {recurrence_count}x, "
                f"and asset criticality of {target_asset} ({breakdown.asset_criticality:.2f}). "
                f"Mapped to MITRE ATT&CK: {mitre_tech_str}."
            ),
            confidence=risk_score,
            source_component="risk_agent",
            metadata={
                "risk_score": risk_score,
                "severity": severity.value,
                "mitre_technique": mitre_tech_str,
                "breakdown": breakdown.model_dump(mode="json"),
            },
            timestamp=now,
        )

        duration_ms = float(round((time.perf_counter() - start_time) * 1000.0, 3))

        summary = (
            f"Assessed risk score {risk_score:.2f} ({severity.value.upper()}). "
            f"Threat behavior attributed to MITRE ATT&CK {mitre_tech_str} ({predicted_class}). "
            f"{breakdown.rationale}"
        )

        return AgentRunResult(
            agent_run_id=run_id,
            agent_name=self.agent_name,
            incident_id=task.incident_id,
            status=AgentRunStatus.COMPLETED,
            findings=[evidence],
            # STRICT SAFETY RULE: Never propose actions from risk assessment alone
            proposed_actions=[],
            conflict_flags=telemetry_gaps,
            summary=summary,
            structured_output={
                "risk_score": risk_score,
                "severity": severity.value,
                "mitre_technique": mitre_tech_str,
                "breakdown": breakdown.model_dump(mode="json"),
            },
            duration_ms=duration_ms,
            created_at=now,
        )
