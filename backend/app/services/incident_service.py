"""SentinelX AI - Incident Lifecycle and Persistence Service

Coordinates database persistence, event linking, idempotency handling,
and audit logging across incident state transitions.
"""

from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session

from app.database.models import IncidentRecord
from app.database.repositories.audit_repo import AuditRepository
from app.database.repositories.event_repo import EventRepository
from app.database.repositories.incident_repo import IncidentRepository
from app.schemas.common import ActionType, IncidentStatus, SeverityLevel
from app.schemas.detections import DetectionResult
from app.schemas.events import NormalizedEvent
from app.schemas.evidence import EvidenceReference, EvidenceType
from app.schemas.incidents import IncidentState, can_transition


class IncidentService:
    """Service managing the persistence lifecycle of security incidents."""

    def __init__(self, db: Session):
        self.db = db

    def record_ingested_event(self, event: NormalizedEvent) -> None:
        """Persist an ingested normalized event idempotently."""
        EventRepository.save_event(self.db, event)

    def create_or_update_from_detection(
        self,
        event: NormalizedEvent,
        detection: DetectionResult,
        candidate_threshold: float = 0.5,
    ) -> Tuple[Optional[IncidentRecord], bool]:
        """Evaluate a detection result. If it meets candidate criteria, create or link to an incident.
        
        Returns:
            (incident_record, is_new_incident)
        """
        # Save event and detection in DB
        EventRepository.save_event(self.db, event)
        EventRepository.save_detection(self.db, detection)

        is_threat = (
            detection.anomaly_score is not None and detection.anomaly_score >= candidate_threshold
        ) or (detection.predicted_class != "BENIGN")

        if not is_threat:
            return None, False

        # Determine severity from anomaly score
        score = detection.anomaly_score or 0.5
        if score >= 0.85:
            severity = SeverityLevel.CRITICAL
        elif score >= 0.65:
            severity = SeverityLevel.HIGH
        elif score >= 0.40:
            severity = SeverityLevel.MEDIUM
        else:
            severity = SeverityLevel.LOW

        # Generate incident ID
        incident_id = f"inc-{event.event_id.replace('evt-', '')}"
        existing = IncidentRepository.get_incident(self.db, incident_id)

        if existing:
            # Already created - link event if not linked
            IncidentRepository.link_event(self.db, incident_id, event.event_id, reason="repeated_detection")
            return existing, False

        # Build initial evidence item
        initial_evidence = EvidenceReference(
            evidence_id=f"evd-{event.event_id.replace('evt-', '')}-det",
            event_id=event.event_id,
            supporting_event_ids=[event.event_id],
            evidence_type=EvidenceType.ANOMALY_SIGNAL,
            is_inferred=False,
            description=(
                f"Threat detector '{detection.model_version}' classified event as '{detection.predicted_class}' "
                f"with anomaly score {score:.2f}. Explanatory features: {', '.join(detection.evidence_feature_names)}."
            ),
            confidence=score,
            source_component="threat_detection_service",
            metadata={"detection_id": detection.detection_id, "predicted_class": detection.predicted_class},
            timestamp=datetime.now(timezone.utc),
        )

        incident_schema = IncidentState(
            incident_id=incident_id,
            title=f"{detection.predicted_class} Attack Candidate on {event.target_asset}",
            status=IncidentStatus.SCORED,
            severity=severity,
            risk_score=score,
            event_ids=[event.event_id],
            evidence=[initial_evidence],
            allowed_actions=[
                ActionType.RAISE_ALERT,
                ActionType.INCREASE_MONITORING,
                ActionType.ESCALATE_FOR_APPROVAL,
                ActionType.SIMULATE_BLOCK,
            ],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            schema_version="v1",
        )

        created_incident = IncidentRepository.save_incident(self.db, incident_schema)

        # Audit log creation
        AuditRepository.log(
            db=self.db,
            actor="incident_service",
            operation="INCIDENT_CREATED",
            entity_id=incident_id,
            status="SUCCESS",
            details=f"Created incident {incident_id} ({detection.predicted_class}) with severity {severity.value}.",
        )

        return created_incident, True

    def transition_state(
        self,
        incident_id: str,
        target_status: IncidentStatus,
        risk_score: Optional[float] = None,
        severity: Optional[SeverityLevel] = None,
        actor: str = "orchestrator",
        reason: str = "",
    ) -> IncidentRecord:
        """Transition an incident's lifecycle status with safety validation."""
        inc = IncidentRepository.get_incident(self.db, incident_id)
        if not inc:
            raise ValueError(f"Incident '{incident_id}' not found.")

        current = IncidentStatus(inc.status)
        if not can_transition(current, target_status):
            raise ValueError(
                f"Invalid incident state transition from '{current.value}' to '{target_status.value}'."
            )

        updated = IncidentRepository.update_incident_state(
            db=self.db,
            incident_id=incident_id,
            new_status=target_status.value,
            risk_score=risk_score,
            severity=severity.value if severity else None,
        )

        AuditRepository.log(
            db=self.db,
            actor=actor,
            operation="STATE_TRANSITION",
            entity_id=incident_id,
            status="SUCCESS",
            details=f"Transitioned status from {current.value} to {target_status.value}. Reason: {reason}",
        )

        return updated
