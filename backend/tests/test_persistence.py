"""Tests for Phase 4: Event and Incident Persistence."""

from datetime import datetime, timezone
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.base import Base
from app.database.models import EventRecord, IncidentRecord
from app.database.repositories.audit_repo import AuditRepository
from app.database.repositories.event_repo import EventRepository
from app.database.repositories.incident_repo import IncidentRepository
from app.database.session import check_db_health, init_db
from app.schemas.common import ActionType, IncidentStatus, SeverityLevel
from app.schemas.detections import DetectionResult
from app.schemas.events import NormalizedEvent
from app.schemas.evidence import EvidenceReference, EvidenceType
from app.schemas.incidents import IncidentState
from app.services.incident_service import IncidentService


@pytest.fixture
def test_db():
    """In-memory SQLite database session for tests."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    init_db(target_engine=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def sample_event():
    return NormalizedEvent(
        event_id="evt-persist-0001",
        event_time=datetime.now(timezone.utc),
        ingested_at=datetime.now(timezone.utc),
        source="dataset_replay",
        source_asset="192.168.10.50",
        target_asset="192.168.10.5",
        event_type="syn_flood_probe",
        features={"flow_duration": 120000.0, "total_fwd_packets": 60, "destination_port": 80},
        raw_label="DoS-Slowloris",
        schema_version="v1",
    )


def test_db_health_check(test_db):
    """Verify database health verification returns healthy."""
    health = check_db_health(test_db.get_bind())
    assert health["status"] == "healthy"
    assert health["connected"] is True


def test_event_persistence_and_idempotency(test_db, sample_event):
    """Ensure events are persisted and duplicate ingestion is idempotent."""
    # First save
    rec1 = EventRepository.save_event(test_db, sample_event)
    assert rec1.event_id == sample_event.event_id
    assert rec1.raw_label == "DoS-Slowloris"

    # Second save with same event_id
    rec2 = EventRepository.save_event(test_db, sample_event)
    assert rec2.event_id == rec1.event_id

    # Retrieve from DB
    queried = EventRepository.get_event(test_db, sample_event.event_id)
    assert queried is not None
    assert queried.source_asset == "192.168.10.50"


def test_incident_persistence_lifecycle(test_db, sample_event):
    """Test incident creation, event linking, evidence attachment, and state transitions."""
    service = IncidentService(test_db)

    # 1. Benign detection does not create incident
    benign_detection = DetectionResult(
        detection_id="det-benign-01",
        event_id=sample_event.event_id,
        predicted_class="BENIGN",
        class_scores={"BENIGN": 0.99, "DoS-Slowloris": 0.01},
        anomaly_score=0.01,
        model_version="rf-v1",
        evidence_feature_names=["destination_port"],
        calibrated=True,
        created_at=datetime.now(timezone.utc),
    )
    inc_record, is_new = service.create_or_update_from_detection(sample_event, benign_detection)
    assert inc_record is None
    assert is_new is False

    # 2. Malicious detection creates incident in SCORED state
    attack_detection = DetectionResult(
        detection_id="det-attack-01",
        event_id=sample_event.event_id,
        predicted_class="DoS-Slowloris",
        class_scores={"BENIGN": 0.05, "DoS-Slowloris": 0.95},
        anomaly_score=0.95,
        model_version="rf-v1",
        evidence_feature_names=["flow_duration", "total_fwd_packets"],
        calibrated=True,
        created_at=datetime.now(timezone.utc),
    )
    inc_record, is_new = service.create_or_update_from_detection(sample_event, attack_detection)
    assert inc_record is not None
    assert is_new is True
    assert inc_record.status == IncidentStatus.SCORED.value
    assert inc_record.severity == SeverityLevel.CRITICAL.value

    # 3. Transition to INVESTIGATING
    updated = service.transition_state(
        incident_id=inc_record.incident_id,
        target_status=IncidentStatus.INVESTIGATING,
        reason="Triggered multi-agent investigation",
    )
    assert updated.status == IncidentStatus.INVESTIGATING.value

    # 4. Invalid transition directly to CLOSED raises ValueError
    with pytest.raises(ValueError, match="Invalid incident state transition"):
        service.transition_state(
            incident_id=inc_record.incident_id,
            target_status=IncidentStatus.CLOSED,
        )


def test_audit_log_append_only(test_db):
    """Verify audit log records are appended with sha256 verification hash."""
    rec = AuditRepository.log(
        db=test_db,
        actor="system_test",
        operation="CONFIG_CHECK",
        entity_id="sys-01",
        status="SUCCESS",
        details="Verified simulation safety guardrails",
    )
    assert rec.audit_id.startswith("aud-")
    assert rec.verification_hash.startswith("sha256:")

    logs = AuditRepository.list_logs(test_db)
    assert len(logs) >= 1
    assert logs[0].actor == "system_test"
