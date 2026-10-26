"""Tests for Response Decisions, Approvals, and Safety Invariants."""

from datetime import datetime, timezone
import pytest
from pydantic import ValidationError
from app.schemas.common import ActionType, ApprovalStatus, ExecutionMode, SafetyResult
from app.schemas.decisions import ApprovalRecord, ResponseDecision, SimulationOutcome


def test_valid_decision_parses(valid_decision_dict):
    decision = ResponseDecision.model_validate(valid_decision_dict)
    assert decision.decision_id == "dec-demo-0001"
    assert decision.proposed_action == ActionType.SIMULATE_BLOCK
    assert decision.safety_result == SafetyResult.REQUIRES_APPROVAL
    assert decision.execution_mode == ExecutionMode.SIMULATION
    assert decision.created_at.tzinfo == timezone.utc


def test_safety_invariant_reject_production_mode(valid_decision_dict):
    """Enforce that response decision strictly rejects production mode."""
    invalid_dict = valid_decision_dict.copy()
    invalid_dict["execution_mode"] = "production"
    with pytest.raises(ValidationError):
        ResponseDecision.model_validate(invalid_dict)


def test_reject_empty_reason_or_evidence(valid_decision_dict):
    invalid_reasons = valid_decision_dict.copy()
    invalid_reasons["reason_codes"] = []
    with pytest.raises(ValidationError):
        ResponseDecision.model_validate(invalid_reasons)

    invalid_evidence = valid_decision_dict.copy()
    invalid_evidence["evidence_event_ids"] = []
    with pytest.raises(ValidationError):
        ResponseDecision.model_validate(invalid_evidence)


def test_approval_record():
    approval = ApprovalRecord(
        approval_id="appr-0001",
        decision_id="dec-demo-0001",
        incident_id="inc-demo-0001",
        reviewer_id="sec-analyst-42",
        status=ApprovalStatus.APPROVED,
        comment="Confirmed attack signature matches slowloris pattern. Approved simulated block.",
        timestamp=datetime.now(timezone.utc)
    )
    assert approval.status == ApprovalStatus.APPROVED
    assert approval.reviewer_id == "sec-analyst-42"


def test_simulation_outcome():
    outcome = SimulationOutcome(
        outcome_id="out-0001",
        decision_id="dec-demo-0001",
        incident_id="inc-demo-0001",
        action=ActionType.SIMULATE_BLOCK,
        containment_success=True,
        operational_disruption_cost=10.5,
        response_delay_ms=250.0,
        reward=89.5,
        episode_id="ep-001",
        recorded_at=datetime.now(timezone.utc)
    )
    assert outcome.containment_success is True
    assert outcome.reward == 89.5
    assert outcome.operational_disruption_cost == 10.5
