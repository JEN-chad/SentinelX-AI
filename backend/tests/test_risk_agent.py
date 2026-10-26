"""Tests for Phase 7: Risk Assessment Agent."""

from datetime import datetime, timezone
import pytest

from app.agents.risk_agent import RiskAssessmentAgent
from app.services.risk_policy import map_risk_to_severity
from app.schemas.agents import AgentRunResult, AgentTask
from app.schemas.common import AgentName, AgentRunStatus, SeverityLevel
from app.services.risk_scoring import RiskScoringService


def test_risk_score_bounds_and_determinism():
    """Verify that risk scores remain strictly bounded in [0.0, 1.0] and are deterministic."""
    service = RiskScoringService()

    score1, sev1, b1, m1 = service.assess_risk(
        detection_score=0.95,
        predicted_class="DoS-Slowloris",
        target_asset="192.168.10.5",
        recurrence_count=4,
    )
    score2, sev2, b2, m2 = service.assess_risk(
        detection_score=0.95,
        predicted_class="DoS-Slowloris",
        target_asset="192.168.10.5",
        recurrence_count=4,
    )

    assert 0.0 <= score1 <= 1.0
    assert score1 == score2
    assert sev1 == sev2
    assert sev1 in [SeverityLevel.CRITICAL, SeverityLevel.HIGH]
    assert m1 is not None
    assert m1["technique_id"] == "T1498.001"


def test_risk_score_monotonicity():
    """Verify that increasing recurrence or asset criticality increases risk score."""
    service = RiskScoringService()

    # Base low recurrence
    score_low_rec, _, _, _ = service.assess_risk(
        detection_score=0.70,
        predicted_class="DoS-Slowloris",
        target_asset="192.168.10.12",
        recurrence_count=1,
    )

    # Higher recurrence on same asset
    score_high_rec, _, _, _ = service.assess_risk(
        detection_score=0.70,
        predicted_class="DoS-Slowloris",
        target_asset="192.168.10.12",
        recurrence_count=5,
    )
    assert score_high_rec > score_low_rec

    # Higher asset criticality
    score_critical_asset, _, _, _ = service.assess_risk(
        detection_score=0.70,
        predicted_class="DoS-Slowloris",
        target_asset="192.168.10.5",  # Critical production web server (0.95)
        recurrence_count=5,
    )
    assert score_critical_asset >= score_high_rec


def test_severity_threshold_boundaries():
    """Test boundary mappings for severity levels."""
    assert map_risk_to_severity(0.95) == SeverityLevel.CRITICAL
    assert map_risk_to_severity(0.80) == SeverityLevel.CRITICAL
    assert map_risk_to_severity(0.79) == SeverityLevel.HIGH
    assert map_risk_to_severity(0.60) == SeverityLevel.HIGH
    assert map_risk_to_severity(0.59) == SeverityLevel.MEDIUM
    assert map_risk_to_severity(0.35) == SeverityLevel.MEDIUM
    assert map_risk_to_severity(0.34) == SeverityLevel.LOW
    assert map_risk_to_severity(0.0) == SeverityLevel.LOW


def test_risk_assessment_agent_execution():
    """Verify RiskAssessmentAgent produces compliant AgentRunResult and adheres to safety rules."""
    agent = RiskAssessmentAgent()
    task = AgentTask(
        task_id="tsk-rsk-001",
        incident_id="inc-test-0001",
        agent_name=AgentName.RISK_AGENT,
        parameters={},
        created_at=datetime.now(timezone.utc),
    )

    context = {
        "detection_score": 0.94,
        "predicted_class": "DoS-Slowloris",
        "target_asset": "192.168.10.5",
        "recurrence_count": 3,
        "supporting_event_ids": ["evt-001", "evt-002"],
        "telemetry_gaps": ["ZERO_REVERSE_TRAFFIC"],
    }

    result = agent.run(task, context=context)

    assert isinstance(result, AgentRunResult)
    assert result.status == AgentRunStatus.COMPLETED
    assert result.agent_name == AgentName.RISK_AGENT
    assert result.incident_id == "inc-test-0001"
    assert result.structured_output["risk_score"] >= 0.70
    assert result.structured_output["mitre_technique"] == "T1498.001"
    assert "ZERO_REVERSE_TRAFFIC" in result.conflict_flags

    # SAFETY INVARIANT: Risk Agent NEVER proposes actions directly
    assert len(result.proposed_actions) == 0
