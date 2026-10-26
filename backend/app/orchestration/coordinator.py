"""SentinelX AI - Incident Coordinator and Orchestrator

Manages agent execution, task dispatch, state transitions, and fail-safe error boundaries.
"""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.agents.detection_agent import DetectionAgent
from app.agents.investigation_agent import InvestigationAgent
from app.agents.mitigation_agent import MitigationPlanningAgent
from app.agents.risk_agent import RiskAssessmentAgent
from app.database.models import IncidentRecord
from app.database.repositories.audit_repo import AuditRepository
from app.database.repositories.event_repo import EventRepository
from app.database.repositories.incident_repo import IncidentRepository
from app.orchestration.state_machine import IncidentStateMachine
from app.safety.approval import ApprovalRecord, ApprovalWorkflow
from app.safety.policy_gate import DeterministicSafetyGate, SafetyResult
from app.schemas.agents import AgentRunResult, AgentTask
from app.schemas.common import ActionType, AgentName, AgentRunStatus, ApprovalStatus, IncidentStatus, SeverityLevel
from app.schemas.events import NormalizedEvent
from app.schemas.incidents import IncidentState
from app.services.incident_service import IncidentService
from app.simulator.action_executor import SimulatedActionExecutor, SimulationOutcome

logger = logging.getLogger("sentinelx.orchestrator")


class IncidentOrchestrator:
    """Central coordinator for agent execution and incident lifecycle transitions."""

    def __init__(
        self,
        db: Session,
        detection_agent: Optional[DetectionAgent] = None,
        investigation_agent: Optional[InvestigationAgent] = None,
        risk_agent: Optional[RiskAssessmentAgent] = None,
        mitigation_agent: Optional[MitigationPlanningAgent] = None,
        simulator_executor: Optional[SimulatedActionExecutor] = None,
        candidate_threshold: float = 0.5,
    ):
        self.db = db
        self.detection_agent = detection_agent or DetectionAgent()
        self.investigation_agent = investigation_agent or InvestigationAgent()
        self.risk_agent = risk_agent or RiskAssessmentAgent()
        self.mitigation_agent = mitigation_agent or MitigationPlanningAgent()
        self.simulator_executor = simulator_executor or SimulatedActionExecutor()
        self.candidate_threshold = candidate_threshold
        self.incident_service = IncidentService(db)

    def process_event(self, event: NormalizedEvent) -> Tuple[Optional[IncidentRecord], AgentRunResult]:
        """Process a NormalizedEvent through the detection workflow.
        
        Returns:
            (IncidentRecord or None, AgentRunResult)
        """
        # 1. Persist the event idempotently
        EventRepository.save_event(self.db, event)

        # 2. Dispatch detection task
        now = datetime.now(timezone.utc)
        target_incident_id = f"inc-{event.event_id.replace('evt-', '')}"
        task = AgentTask(
            task_id=f"tsk-det-{now.strftime('%Y%m%d%H%M%S%f')[-8:]}",
            incident_id=target_incident_id,
            agent_name=AgentName.DETECTION_AGENT,
            parameters={"candidate_threshold": self.candidate_threshold},
            created_at=now,
        )

        try:
            agent_result = self.detection_agent.run(task, context={"event": event})
        except Exception as e:
            logger.error(f"Detection Agent crashed: {e}")
            agent_result = AgentRunResult(
                agent_run_id=f"run-err-{now.strftime('%Y%m%d%H%M%S%f')[-8:]}",
                agent_name=AgentName.DETECTION_AGENT,
                incident_id=target_incident_id,
                status=AgentRunStatus.FAILED,
                findings=[],
                proposed_actions=[],
                conflict_flags=[f"CRASH: {str(e)}"],
                summary=f"Agent exception: {str(e)}",
                structured_output={"error": str(e)},
                duration_ms=0.0,
                created_at=now,
            )

        # 3. Handle Detection Agent failure fail-safely
        if agent_result.status != AgentRunStatus.COMPLETED:
            AuditRepository.log(
                db=self.db,
                actor="orchestrator",
                operation="AGENT_FAILED",
                entity_id=target_incident_id,
                status="BLOCKED",
                details=f"Detection agent failed on event {event.event_id}: {agent_result.summary}",
            )
            return None, agent_result

        # 4. Check if event meets threat candidate threshold
        is_threat = agent_result.structured_output.get("is_anomaly", False)
        anomaly_score = float(agent_result.structured_output.get("anomaly_score", 0.0))

        if not is_threat:
            # Benign flow - no incident created
            return None, agent_result

        # 5. Create or retrieve IncidentRecord
        existing_inc = IncidentRepository.get_incident(self.db, target_incident_id)
        if existing_inc:
            IncidentRepository.link_event(self.db, target_incident_id, event.event_id, reason="correlated_detection")
            IncidentRepository.add_agent_result(self.db, agent_result)
            return existing_inc, agent_result

        # Assess preliminary severity from anomaly score
        if anomaly_score >= 0.85:
            severity = SeverityLevel.CRITICAL
        elif anomaly_score >= 0.65:
            severity = SeverityLevel.HIGH
        elif anomaly_score >= 0.40:
            severity = SeverityLevel.MEDIUM
        else:
            severity = SeverityLevel.LOW

        predicted_class = agent_result.structured_output.get("detection", {}).get("predicted_class", "Threat")

        incident_schema = IncidentState(
            incident_id=target_incident_id,
            title=f"{predicted_class} Alert on {event.target_asset}",
            status=IncidentStatus.SCORED,
            severity=severity,
            risk_score=anomaly_score,
            event_ids=[event.event_id],
            evidence=agent_result.findings,
            agent_results=[agent_result],
            allowed_actions=[
                ActionType.RAISE_ALERT,
                ActionType.INCREASE_MONITORING,
                ActionType.ESCALATE_FOR_APPROVAL,
                ActionType.SIMULATE_BLOCK,
            ],
            created_at=now,
            updated_at=now,
            schema_version="v1",
        )

        incident_record = IncidentRepository.save_incident(self.db, incident_schema)
        IncidentRepository.add_agent_result(self.db, agent_result)

        AuditRepository.log(
            db=self.db,
            actor="orchestrator",
            operation="INCIDENT_ORCHESTRATED",
            entity_id=target_incident_id,
            status="SUCCESS",
            details=f"Orchestrated new incident {target_incident_id} ({predicted_class}) in state SCORED.",
        )

        return incident_record, agent_result

    def investigate_incident(
        self,
        incident_id: str,
        candidate_events: Optional[List[NormalizedEvent]] = None,
        time_window_seconds: int = 600,
    ) -> Tuple[IncidentRecord, AgentRunResult]:
        """Dispatch Investigation Agent on an existing incident to correlate related events and assemble timeline."""
        incident = IncidentRepository.get_incident(self.db, incident_id)
        if not incident:
            raise ValueError(f"Incident '{incident_id}' not found.")

        # Transition incident to INVESTIGATING if it was in SCORED
        if incident.status == IncidentStatus.SCORED.value:
            self.incident_service.transition_state(
                incident_id=incident_id,
                target_status=IncidentStatus.INVESTIGATING,
                reason="Investigation Agent dispatched for event correlation and timeline construction.",
            )
        elif incident.status not in (IncidentStatus.INVESTIGATING.value, IncidentStatus.RISK_ASSESSED.value):
            raise ValueError(f"Cannot investigate incident in state '{incident.status}'. Expected 'scored'.")

        # Retrieve seed event
        seed_link = incident.event_links[0] if incident.event_links else None
        if not seed_link:
            raise ValueError(f"Incident '{incident_id}' has no linked seed events.")

        seed_record = EventRepository.get_event(self.db, seed_link.event_id)
        if not seed_record:
            raise ValueError(f"Seed event record '{seed_link.event_id}' not found in database.")

        def _to_utc(dt: datetime) -> datetime:
            return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)

        seed_event = NormalizedEvent(
            event_id=seed_record.event_id,
            event_time=_to_utc(seed_record.event_time),
            ingested_at=_to_utc(seed_record.ingested_at),
            source=seed_record.source,
            source_asset=seed_record.source_asset,
            target_asset=seed_record.target_asset,
            event_type=seed_record.event_type,
            features=seed_record.features,
            dataset_id=seed_record.dataset_id,
            run_id=seed_record.run_id,
            raw_label=seed_record.raw_label,
            schema_version=seed_record.schema_version,
        )

        # Retrieve candidates from database if not supplied
        if candidate_events is None:
            db_events = EventRepository.list_events(self.db, limit=100)
            candidate_events = [
                NormalizedEvent(
                    event_id=e.event_id,
                    event_time=_to_utc(e.event_time),
                    ingested_at=_to_utc(e.ingested_at),
                    source=e.source,
                    source_asset=e.source_asset,
                    target_asset=e.target_asset,
                    event_type=e.event_type,
                    features=e.features,
                    dataset_id=e.dataset_id,
                    run_id=e.run_id,
                    raw_label=e.raw_label,
                    schema_version=e.schema_version,
                )
                for e in db_events
                if e.event_id != seed_event.event_id
            ]

        now = datetime.now(timezone.utc)
        task = AgentTask(
            task_id=f"tsk-inv-{now.strftime('%Y%m%d%H%M%S%f')[-8:]}",
            incident_id=incident_id,
            agent_name=AgentName.INVESTIGATION_AGENT,
            parameters={"time_window_seconds": time_window_seconds},
            created_at=now,
        )

        # Execute investigation
        inv_result = self.investigation_agent.run(
            task=task,
            context={
                "seed_event": seed_event,
                "candidate_events": candidate_events,
            },
        )

        # Persist agent results and correlated links
        IncidentRepository.add_agent_result(self.db, inv_result)

        for match in inv_result.structured_output.get("correlation_matches", []):
            IncidentRepository.link_event(
                self.db,
                incident_id=incident_id,
                event_id=match["event_id"],
                reason=match["reason"],
            )

        # Advance incident state: INVESTIGATING -> RISK_ASSESSED
        current_record = IncidentRepository.get_incident(self.db, incident_id)
        if current_record.status != IncidentStatus.RISK_ASSESSED.value:
            updated_inc = self.incident_service.transition_state(
                incident_id=incident_id,
                target_status=IncidentStatus.RISK_ASSESSED,
                reason=f"Investigation concluded. Linked {inv_result.structured_output.get('recurrence_count', 1)} flows.",
            )
        else:
            updated_inc = current_record

        return updated_inc, inv_result

    def assess_incident_risk(self, incident_id: str) -> Tuple[IncidentRecord, AgentRunResult]:
        """Dispatch Risk Assessment Agent (Phase 7) to compute multi-factor risk and attribute MITRE technique."""
        incident = IncidentRepository.get_incident(self.db, incident_id)
        if not incident:
            raise ValueError(f"Incident '{incident_id}' not found.")

        # Ensure incident is in RISK_ASSESSED state
        if incident.status != IncidentStatus.RISK_ASSESSED.value:
            if incident.status == IncidentStatus.SCORED.value:
                # Run investigation first if not yet performed
                incident, _ = self.investigate_incident(incident_id)
            elif incident.status != IncidentStatus.RISK_ASSESSED.value:
                pass  # allow re-evaluating risk if already beyond

        now = datetime.now(timezone.utc)
        task = AgentTask(
            task_id=f"tsk-rsk-{now.strftime('%Y%m%d%H%M%S%f')[-8:]}",
            incident_id=incident_id,
            agent_name=AgentName.RISK_AGENT,
            parameters={},
            created_at=now,
        )

        # Context derivation from existing incident and linked events
        seed_event_id = incident.event_links[0].event_id if incident.event_links else None
        target_asset = incident.target_asset or "192.168.10.5"
        predicted_class = incident.title.split()[0] if incident.title else "Threat"

        risk_result = self.risk_agent.run(
            task=task,
            context={
                "detection_score": incident.risk_score or 0.75,
                "predicted_class": predicted_class,
                "target_asset": target_asset,
                "recurrence_count": len(incident.event_links),
                "supporting_event_ids": [l.event_id for l in incident.event_links],
            },
        )

        IncidentRepository.add_agent_result(self.db, risk_result)

        new_risk_score = risk_result.structured_output["risk_score"]
        new_severity = SeverityLevel(risk_result.structured_output["severity"])
        mitre_tech = risk_result.structured_output.get("mitre_technique")

        # Update MITRE technique on DB record
        incident_rec = IncidentRepository.get_incident(self.db, incident_id)
        if incident_rec:
            incident_rec.mitre_technique = mitre_tech
            incident_rec.target_asset = target_asset
            self.db.commit()

        # Transition: RISK_ASSESSED -> RESPONSE_PROPOSED
        updated_inc = self.incident_service.transition_state(
            incident_id=incident_id,
            target_status=IncidentStatus.RESPONSE_PROPOSED,
            risk_score=new_risk_score,
            severity=new_severity,
            actor="risk_agent",
            reason=f"Risk assessed as {new_risk_score:.2f} ({new_severity.value.upper()}).",
        )

        return updated_inc, risk_result

    def plan_mitigation(self, incident_id: str, is_human_approved: bool = False) -> Tuple[IncidentRecord, AgentRunResult]:
        """Dispatch Mitigation Planning Agent (Phase 8) to propose allowlisted defensive actions."""
        incident = IncidentRepository.get_incident(self.db, incident_id)
        if not incident:
            raise ValueError(f"Incident '{incident_id}' not found.")

        # Ensure incident has had risk assessed
        if incident.status in [IncidentStatus.SCORED.value, IncidentStatus.INVESTIGATING.value, IncidentStatus.RISK_ASSESSED.value]:
            incident, _ = self.assess_incident_risk(incident_id)

        now = datetime.now(timezone.utc)
        task = AgentTask(
            task_id=f"tsk-mit-{now.strftime('%Y%m%d%H%M%S%f')[-8:]}",
            incident_id=incident_id,
            agent_name=AgentName.MITIGATION_AGENT,
            parameters={},
            created_at=now,
        )

        mit_result = self.mitigation_agent.run(
            task=task,
            context={
                "risk_score": incident.risk_score,
                "target_asset": incident.target_asset or "192.168.10.5",
                "is_human_approved": is_human_approved,
                "supporting_event_ids": [l.event_id for l in incident.event_links],
            },
        )

        IncidentRepository.add_agent_result(self.db, mit_result)

        primary_action = mit_result.structured_output["recommended_action"]

        # If primary action is simulate_block and not approved, advance to APPROVAL_REQUIRED
        if primary_action == ActionType.SIMULATE_BLOCK.value and not is_human_approved:
            target_status = IncidentStatus.APPROVAL_REQUIRED
            reason = "Recommended simulate_block requires human security analyst approval."
        else:
            target_status = IncidentStatus.SIMULATING
            reason = f"Response '{primary_action}' permitted under deterministic safety gate."

        updated_inc = self.incident_service.transition_state(
            incident_id=incident_id,
            target_status=target_status,
            actor="mitigation_agent",
            reason=reason,
        )

        return updated_inc, mit_result

    def record_approval(
        self,
        incident_id: str,
        reviewer_id: str,
        action: ActionType,
        status: ApprovalStatus = ApprovalStatus.APPROVED,
        comment: Optional[str] = None,
    ) -> ApprovalRecord:
        """Record human analyst approval decision and transition incident to SIMULATING or CLOSED."""
        incident = IncidentRepository.get_incident(self.db, incident_id)
        if not incident:
            raise ValueError(f"Incident '{incident_id}' not found.")

        approval = ApprovalWorkflow.create_approval(
            incident_id=incident_id,
            action=action,
            reviewer_id=reviewer_id,
            status=status,
            comment=comment,
        )

        if status == ApprovalStatus.APPROVED:
            self.incident_service.transition_state(
                incident_id=incident_id,
                target_status=IncidentStatus.SIMULATING,
                actor=reviewer_id,
                reason=f"Analyst approved action '{action.value}'. Note: {comment}",
            )
        else:
            self.incident_service.transition_state(
                incident_id=incident_id,
                target_status=IncidentStatus.CLOSED,
                actor=reviewer_id,
                reason=f"Analyst rejected proposed action '{action.value}'.",
            )

        return approval

    def execute_simulated_response(
        self,
        incident_id: str,
        action: ActionType,
    ) -> Tuple[IncidentRecord, SimulationOutcome]:
        """Execute approved response strictly within simulated sandbox boundary."""
        incident = IncidentRepository.get_incident(self.db, incident_id)
        if not incident:
            raise ValueError(f"Incident '{incident_id}' not found.")

        target_asset = incident.target_asset or "192.168.10.5"

        # Execute containment in virtual simulation state
        outcome = self.simulator_executor.execute(
            incident_id=incident_id,
            action=action,
            target_asset=target_asset,
            is_attack=True,
        )

        # Transition incident: SIMULATING -> OUTCOME_RECORDED
        updated_inc = self.incident_service.transition_state(
            incident_id=incident_id,
            target_status=IncidentStatus.OUTCOME_RECORDED,
            actor="simulator_executor",
            reason=(
                f"Simulated action '{action.value}' completed. "
                f"Containment: {outcome.containment_success}, Disruption: {outcome.operational_disruption_cost}, "
                f"Reward: {outcome.reward}."
            ),
        )

        return updated_inc, outcome
