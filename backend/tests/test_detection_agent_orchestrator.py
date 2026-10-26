"""Tests for Phase 5: Detection Agent and Incident Orchestrator."""

from datetime import datetime, timezone
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.agents.detection_agent import DetectionAgent
from app.database.session import init_db
from app.orchestration.coordinator import IncidentOrchestrator
from app.orchestration.state_machine import IncidentStateMachine
from app.schemas.common import ActionType, AgentRunStatus, IncidentStatus
from app.schemas.events import NormalizedEvent


@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    init_db(target_engine=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def benign_event():
    return NormalizedEvent(
        event_id="evt-orch-0001",
        event_time=datetime.now(timezone.utc),
        ingested_at=datetime.now(timezone.utc),
        source="cic_ids2017_replay",
        source_asset="192.168.10.14",
        target_asset="10.0.0.1",
        event_type="internal_tls_flow",
        features={
            "flow_duration": 54000.0,
            "total_fwd_packets": 12,
            "total_bwd_packets": 10,
            "flow_bytes_per_sec": 60000.0,
            "fwd_packet_length_mean": 512.0,
            "syn_flag_count": 1,
            "rst_flag_count": 0,
            "bwd_packets_per_sec": 28.5,
            "destination_port": 443,
        },
        raw_label="BENIGN",
        schema_version="v1",
    )


@pytest.fixture
def malicious_event():
    return NormalizedEvent(
        event_id="evt-orch-0002",
        event_time=datetime.now(timezone.utc),
        ingested_at=datetime.now(timezone.utc),
        source="cic_ids2017_replay",
        source_asset="192.168.10.50",
        target_asset="192.168.10.5",
        event_type="syn_flood_probe",
        features={
            "flow_duration": 124800.0,
            "total_fwd_packets": 68,
            "total_bwd_packets": 1,
            "flow_bytes_per_sec": 14820.5,
            "fwd_packet_length_mean": 42.0,
            "syn_flag_count": 1,
            "rst_flag_count": 0,
            "bwd_packets_per_sec": 8.0,
            "destination_port": 80,
        },
        raw_label="DoS-Slowloris",
        schema_version="v1",
    )


def test_benign_event_does_not_create_incident(test_db, benign_event):
    """Verify that a benign flow is scored and recorded but creates no incident."""
    orchestrator = IncidentOrchestrator(db=test_db, candidate_threshold=0.5)
    incident, agent_result = orchestrator.process_event(benign_event)

    assert incident is None
    assert agent_result.status == AgentRunStatus.COMPLETED
    assert agent_result.structured_output["is_anomaly"] is False
    assert len(agent_result.proposed_actions) == 0


def test_malicious_event_creates_incident(test_db, malicious_event):
    """Verify that a suspicious flow creates an incident in SCORED state with evidence."""
    orchestrator = IncidentOrchestrator(db=test_db, candidate_threshold=0.5)
    incident, agent_result = orchestrator.process_event(malicious_event)

    assert incident is not None
    assert incident.status == IncidentStatus.SCORED.value
    assert incident.incident_id == "inc-orch-0002"
    assert incident.risk_score >= 0.5
    assert len(incident.evidence) >= 1
    assert len(incident.agent_results) >= 1

    # CRITICAL SAFETY INVARIANT: Detection agent must NEVER directly propose or trigger mitigations
    assert len(agent_result.proposed_actions) == 0


def test_state_machine_transitions():
    """Verify permitted and prohibited lifecycle transitions."""
    # Permitted: SCORED -> INVESTIGATING
    IncidentStateMachine.validate_transition(IncidentStatus.SCORED, IncidentStatus.INVESTIGATING)

    # Permitted: INVESTIGATING -> RISK_ASSESSED
    IncidentStateMachine.validate_transition(IncidentStatus.INVESTIGATING, IncidentStatus.RISK_ASSESSED)

    # Prohibited: SCORED -> OUTCOME_RECORDED
    with pytest.raises(ValueError, match="State transition rejected"):
        IncidentStateMachine.validate_transition(IncidentStatus.SCORED, IncidentStatus.OUTCOME_RECORDED)


def test_detection_agent_failure_boundary(test_db):
    """Verify fail-safe behavior when agent encounters error."""
    agent = DetectionAgent()
    orchestrator = IncidentOrchestrator(db=test_db, detection_agent=agent)

    # Event with missing features will cause inference failure
    broken_event = NormalizedEvent(
        event_id="evt-broken-0001",
        event_time=datetime.now(timezone.utc),
        ingested_at=datetime.now(timezone.utc),
        source="corrupt",
        source_asset="1.1.1.1",
        target_asset="2.2.2.2",
        event_type="test",
        features={"invalid": 123},
        schema_version="v1",
    )

    incident, result = orchestrator.process_event(broken_event)
    assert incident is None
    assert result.status == AgentRunStatus.FAILED
    assert len(result.proposed_actions) == 0
