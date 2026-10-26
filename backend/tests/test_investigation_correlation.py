"""Tests for Phase 6: Investigation and Correlation Agent."""

from datetime import datetime, timedelta, timezone
import pytest

from app.agents.investigation_agent import InvestigationAgent
from app.schemas.agents import AgentRunResult, AgentTask
from app.schemas.common import AgentName, AgentRunStatus
from app.schemas.events import NormalizedEvent
from app.schemas.evidence import EvidenceType
from app.services.correlation_service import CorrelationService
from app.services.timeline_service import TimelineService


@pytest.fixture
def base_time():
    return datetime(2026, 10, 14, 4, 12, 0, tzinfo=timezone.utc)


@pytest.fixture
def seed_slowloris_event(base_time):
    return NormalizedEvent(
        event_id="evt-inv-0001",
        event_time=base_time,
        ingested_at=base_time,
        source="cic_ids2017_replay",
        source_asset="192.168.10.50",
        target_asset="192.168.10.5",
        event_type="http_persistent_flow",
        features={
            "flow_duration": 124800.0,
            "total_fwd_packets": 68,
            "total_bwd_packets": 0,
            "flow_bytes_per_sec": 14820.5,
            "fwd_packet_length_mean": 42.0,
            "syn_flag_count": 1,
            "rst_flag_count": 0,
            "bwd_packets_per_sec": 0.0,
            "destination_port": 80,
        },
        raw_label="DoS-Slowloris",
        schema_version="v1",
    )


@pytest.fixture
def correlated_candidate_event(base_time):
    # 2 seconds after seed, same host pair and service
    return NormalizedEvent(
        event_id="evt-inv-0002",
        event_time=base_time + timedelta(seconds=2),
        ingested_at=base_time + timedelta(seconds=2),
        source="cic_ids2017_replay",
        source_asset="192.168.10.50",
        target_asset="192.168.10.5",
        event_type="http_persistent_flow",
        features={
            "flow_duration": 119500.0,
            "total_fwd_packets": 74,
            "total_bwd_packets": 0,
            "flow_bytes_per_sec": 16210.0,
            "fwd_packet_length_mean": 44.0,
            "syn_flag_count": 1,
            "rst_flag_count": 0,
            "bwd_packets_per_sec": 0.0,
            "destination_port": 80,
        },
        raw_label="DoS-Slowloris",
        schema_version="v1",
    )


@pytest.fixture
def distant_unrelated_event(base_time):
    # 25 minutes later, completely outside 10-minute window
    return NormalizedEvent(
        event_id="evt-inv-0099",
        event_time=base_time + timedelta(minutes=25),
        ingested_at=base_time + timedelta(minutes=25),
        source="cic_ids2017_replay",
        source_asset="192.168.10.50",
        target_asset="192.168.10.5",
        event_type="http_persistent_flow",
        features={
            "flow_duration": 5000.0,
            "total_fwd_packets": 5,
            "total_bwd_packets": 5,
            "flow_bytes_per_sec": 10000.0,
            "fwd_packet_length_mean": 50.0,
            "syn_flag_count": 0,
            "rst_flag_count": 0,
            "bwd_packets_per_sec": 1.0,
            "destination_port": 80,
        },
        raw_label="BENIGN",
        schema_version="v1",
    )


def test_correlation_service_within_window(seed_slowloris_event, correlated_candidate_event):
    """Verify events inside time window with matching host pair correlate with reason."""
    service = CorrelationService(default_time_window_seconds=600)
    match = service.evaluate_pair(seed_slowloris_event, correlated_candidate_event)

    assert match is not None
    assert match.event_id == correlated_candidate_event.event_id
    assert match.rule_name in ["HOST_PAIR_SERVICE_BURST", "HOST_PAIR_CONVERGENCE"]
    assert match.confidence >= 0.85
    assert "192.168.10.50" in match.reason


def test_correlation_service_outside_window(seed_slowloris_event, distant_unrelated_event):
    """Verify events outside the configured time window are NOT correlated."""
    service = CorrelationService(default_time_window_seconds=600)
    match = service.evaluate_pair(seed_slowloris_event, distant_unrelated_event)
    assert match is None


def test_timeline_service_ordering_and_gaps(seed_slowloris_event, correlated_candidate_event):
    """Verify chronological timeline sorting and evidence gap identification."""
    # Pass events in reverse order
    entries = TimelineService.build_timeline([correlated_candidate_event, seed_slowloris_event])

    assert len(entries) == 2
    # Must be ordered chronologically
    assert entries[0].event_id == seed_slowloris_event.event_id
    assert entries[1].event_id == correlated_candidate_event.event_id
    assert entries[0].is_inferred is False

    gaps, conflicts = TimelineService.detect_evidence_gaps_and_conflicts([seed_slowloris_event, correlated_candidate_event])
    # Both events have total_bwd_packets == 0
    assert any("ZERO_REVERSE_TRAFFIC" in g for g in gaps)


def test_investigation_agent_run(seed_slowloris_event, correlated_candidate_event, distant_unrelated_event):
    """Verify end-to-end Investigation Agent execution and structured outputs."""
    agent = InvestigationAgent()
    task = AgentTask(
        task_id="tsk-inv-001",
        incident_id="inc-test-0001",
        agent_name=AgentName.INVESTIGATION_AGENT,
        parameters={"time_window_seconds": 600},
        created_at=datetime.now(timezone.utc),
    )

    context = {
        "seed_event": seed_slowloris_event,
        "candidate_events": [correlated_candidate_event, distant_unrelated_event],
    }

    result = agent.run(task, context=context)

    assert isinstance(result, AgentRunResult)
    assert result.status == AgentRunStatus.COMPLETED
    assert result.agent_name == AgentName.INVESTIGATION_AGENT
    assert result.incident_id == "inc-test-0001"

    # Correlated candidate should be linked, distant candidate should not
    correlated_ids = result.structured_output["correlated_event_ids"]
    assert seed_slowloris_event.event_id in correlated_ids
    assert correlated_candidate_event.event_id in correlated_ids
    assert distant_unrelated_event.event_id not in correlated_ids

    # Check evidence findings
    assert len(result.findings) >= 2
    timeline_evidence = next(f for f in result.findings if f.evidence_type == EvidenceType.TIMELINE_CLUSTER)
    assert timeline_evidence.is_inferred is True
    assert len(timeline_evidence.supporting_event_ids) == 2

    # Verify structured timeline
    assert len(result.structured_output["timeline"]) == 2
    assert result.structured_output["recurrence_count"] == 2


def test_orchestrator_investigate_incident(seed_slowloris_event, correlated_candidate_event):
    """Verify that IncidentOrchestrator can investigate an existing incident and advance its state."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.database.session import init_db
    from app.orchestration.coordinator import IncidentOrchestrator
    from app.schemas.common import IncidentStatus

    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    init_db(target_engine=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        orchestrator = IncidentOrchestrator(db=db)

        # 1. First event creates incident in SCORED state
        inc, det_result = orchestrator.process_event(seed_slowloris_event)
        assert inc is not None
        assert inc.status == IncidentStatus.SCORED.value

        # 2. Investigate the incident with correlated candidates
        updated_inc, inv_result = orchestrator.investigate_incident(
            incident_id=inc.incident_id,
            candidate_events=[correlated_candidate_event],
        )

        assert updated_inc.status == IncidentStatus.RISK_ASSESSED.value
        assert inv_result.status == AgentRunStatus.COMPLETED
        assert len(updated_inc.event_links) >= 2
    finally:
        db.close()
