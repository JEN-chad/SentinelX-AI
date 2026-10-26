"""SentinelX AI - Incident, Evidence, and Agent Run Repository"""

from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database.models import (
    AgentRunRecord,
    EvidenceRecord,
    IncidentEventLink,
    IncidentRecord,
)
from app.schemas.agents import AgentRunResult
from app.schemas.evidence import EvidenceReference
from app.schemas.incidents import IncidentState


class IncidentRepository:
    """Repository handling persistence and queries for Incidents, Evidence, and Agent Traces."""

    @staticmethod
    def save_incident(db: Session, incident: IncidentState) -> IncidentRecord:
        """Persist or update an incident record idempotently."""
        existing = db.execute(
            select(IncidentRecord)
            .options(
                selectinload(IncidentRecord.event_links),
                selectinload(IncidentRecord.evidence),
                selectinload(IncidentRecord.agent_results),
            )
            .where(IncidentRecord.incident_id == incident.incident_id)
        ).scalar_one_or_none()

        if existing:
            existing.title = incident.title
            existing.status = incident.status.value if hasattr(incident.status, "value") else str(incident.status)
            existing.severity = incident.severity.value if hasattr(incident.severity, "value") else str(incident.severity)
            existing.risk_score = incident.risk_score
            existing.updated_at = incident.updated_at
            db.commit()
            db.refresh(existing)
            return existing

        record = IncidentRecord(
            incident_id=incident.incident_id,
            title=incident.title,
            status=incident.status.value if hasattr(incident.status, "value") else str(incident.status),
            severity=incident.severity.value if hasattr(incident.severity, "value") else str(incident.severity),
            risk_score=incident.risk_score,
            allowed_actions=[a.value if hasattr(a, "value") else str(a) for a in incident.allowed_actions],
            created_at=incident.created_at,
            updated_at=incident.updated_at,
            schema_version=incident.schema_version,
        )
        db.add(record)
        db.commit()

        # Link initial event IDs
        for eid in incident.event_ids:
            IncidentRepository.link_event(db, incident.incident_id, eid, reason="primary_detection")

        # Save any attached evidence
        for ev in incident.evidence:
            IncidentRepository.add_evidence(db, incident.incident_id, ev)

        db.refresh(record)
        return record

    @staticmethod
    def get_incident(db: Session, incident_id: str) -> Optional[IncidentRecord]:
        return db.execute(
            select(IncidentRecord)
            .options(
                selectinload(IncidentRecord.event_links),
                selectinload(IncidentRecord.evidence),
                selectinload(IncidentRecord.agent_results),
                selectinload(IncidentRecord.decisions),
            )
            .where(IncidentRecord.incident_id == incident_id)
        ).scalar_one_or_none()

    @staticmethod
    def list_incidents(
        db: Session,
        skip: int = 0,
        limit: int = 50,
        status: Optional[str] = None,
        severity: Optional[str] = None,
    ) -> List[IncidentRecord]:
        stmt = select(IncidentRecord).options(
            selectinload(IncidentRecord.event_links),
            selectinload(IncidentRecord.evidence),
            selectinload(IncidentRecord.agent_results),
        )
        if status:
            stmt = stmt.where(IncidentRecord.status == status)
        if severity:
            stmt = stmt.where(IncidentRecord.severity == severity)
        stmt = stmt.order_by(IncidentRecord.created_at.desc()).offset(skip).limit(limit)
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def link_event(db: Session, incident_id: str, event_id: str, reason: str = "correlated_evidence") -> IncidentEventLink:
        """Link an event to an incident idempotently."""
        existing = db.execute(
            select(IncidentEventLink).where(
                IncidentEventLink.incident_id == incident_id,
                IncidentEventLink.event_id == event_id,
            )
        ).scalar_one_or_none()

        if existing:
            return existing

        link = IncidentEventLink(
            incident_id=incident_id,
            event_id=event_id,
            association_reason=reason,
            linked_at=datetime.now(timezone.utc),
        )
        db.add(link)
        db.commit()
        db.refresh(link)
        return link

    @staticmethod
    def add_evidence(db: Session, incident_id: str, evidence: EvidenceReference) -> EvidenceRecord:
        """Persist an evidence item linked to an incident."""
        existing = db.execute(
            select(EvidenceRecord).where(EvidenceRecord.evidence_id == evidence.evidence_id)
        ).scalar_one_or_none()

        if existing:
            return existing

        record = EvidenceRecord(
            evidence_id=evidence.evidence_id,
            incident_id=incident_id,
            event_id=evidence.event_id,
            supporting_event_ids=evidence.supporting_event_ids,
            evidence_type=evidence.evidence_type.value if hasattr(evidence.evidence_type, "value") else str(evidence.evidence_type),
            is_inferred=evidence.is_inferred,
            description=evidence.description,
            confidence=evidence.confidence,
            source_component=evidence.source_component,
            metadata_payload=evidence.metadata,
            timestamp=evidence.timestamp,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def add_agent_result(db: Session, result: AgentRunResult) -> AgentRunRecord:
        """Persist an agent execution run trace."""
        existing = db.execute(
            select(AgentRunRecord).where(AgentRunRecord.agent_run_id == result.agent_run_id)
        ).scalar_one_or_none()

        if existing:
            return existing

        record = AgentRunRecord(
            agent_run_id=result.agent_run_id,
            agent_name=result.agent_name.value if hasattr(result.agent_name, "value") else str(result.agent_name),
            incident_id=result.incident_id,
            status=result.status.value if hasattr(result.status, "value") else str(result.status),
            proposed_actions=[a.value if hasattr(a, "value") else str(a) for a in result.proposed_actions],
            conflict_flags=result.conflict_flags,
            summary=result.summary,
            structured_output=result.structured_output,
            duration_ms=result.duration_ms,
            created_at=result.created_at,
        )
        db.add(record)
        db.commit()

        # Also persist any findings emitted by this agent
        for finding in result.findings:
            IncidentRepository.add_evidence(db, result.incident_id, finding)

        db.refresh(record)
        return record

    @staticmethod
    def update_incident_state(
        db: Session,
        incident_id: str,
        new_status: str,
        risk_score: Optional[float] = None,
        severity: Optional[str] = None,
    ) -> Optional[IncidentRecord]:
        """Update incident lifecycle state and risk/severity metrics."""
        inc = IncidentRepository.get_incident(db, incident_id)
        if not inc:
            return None

        inc.status = new_status
        inc.updated_at = datetime.now(timezone.utc)
        if risk_score is not None:
            inc.risk_score = risk_score
        if severity is not None:
            inc.severity = severity

        db.commit()
        db.refresh(inc)
        return inc
