"""Tests for Phase 8: Mitigation Planning, Safety Gate, and Simulated Execution."""

from datetime import datetime, timezone
import pytest

from app.agents.mitigation_agent import MitigationPlanningAgent
from app.safety.action_catalogue import ACTION_CATALOGUE, get_action_spec, is_allowed_action
from app.safety.approval import ApprovalWorkflow
from app.safety.policy_gate import DeterministicSafetyGate
from app.schemas.agents import AgentRunResult, AgentTask
from app.schemas.common import ActionType, AgentName, AgentRunStatus, ApprovalStatus, SafetyResult
from app.simulator.action_executor import SimulatedActionExecutor, SimulationOutcome


def test_action_catalogue_allowlist():
    """Verify that only the 4 canonical actions exist in the catalogue."""
    assert len(ACTION_CATALOGUE) == 4
    assert is_allowed_action("raise_alert")
    assert is_allowed_action("increase_monitoring")
    assert is_allowed_action("escalate_for_approval")
    assert is_allowed_action("simulate_block")

    # Reject arbitrary or dangerous shell/firewall commands
    assert not is_allowed_action("iptables_drop")
    assert not is_allowed_action("reboot_system")
    assert not is_allowed_action("rm_rf")


def test_safety_gate_unknown_action_rejection():
    """Verify that the safety gate unconditionally rejects unknown actions."""
    gate = DeterministicSafetyGate()
    decision = gate.evaluate(action="delete_firewall_rule", incident_risk_score=0.9)

    assert decision.safety_result == SafetyResult.REJECTED
    assert any("UNKNOWN_ACTION_REJECTED" in r for r in decision.reason_codes)


def test_safety_gate_prerequisite_enforcement():
    """Verify that actions with unmet risk prerequisites are rejected."""
    gate = DeterministicSafetyGate()

    # simulate_block requires min risk 0.60; test with risk 0.20
    decision = gate.evaluate(action=ActionType.SIMULATE_BLOCK, incident_risk_score=0.20, is_human_approved=True)
    assert decision.safety_result == SafetyResult.REJECTED
    assert any("PREREQUISITE_FAILED" in r for r in decision.reason_codes)


def test_safety_gate_approval_workflow():
    """Verify approval requirement for simulated blocking."""
    gate = DeterministicSafetyGate()

    # 1. Unapproved simulate_block returns REQUIRES_APPROVAL
    decision_unapproved = gate.evaluate(
        action=ActionType.SIMULATE_BLOCK,
        incident_risk_score=0.85,
        is_human_approved=False,
    )
    assert decision_unapproved.safety_result == SafetyResult.REQUIRES_APPROVAL

    # 2. Record approval
    approval = ApprovalWorkflow.create_approval(
        incident_id="inc-test-01",
        action=ActionType.SIMULATE_BLOCK,
        reviewer_id="analyst_alice",
        comment="Containment confirmed for active Slowloris flood",
    )
    assert approval.status == ApprovalStatus.APPROVED

    # 3. Approved simulate_block returns PERMITTED
    decision_approved = gate.evaluate(
        action=ActionType.SIMULATE_BLOCK,
        incident_risk_score=0.85,
        is_human_approved=True,
    )
    assert decision_approved.safety_result == SafetyResult.PERMITTED


def test_safety_gate_rejects_non_simulation_mode():
    """Verify that execution mode other than simulation is blocked."""
    gate = DeterministicSafetyGate()
    decision = gate.evaluate(
        action=ActionType.RAISE_ALERT,
        incident_risk_score=0.5,
        execution_mode="production",
    )
    assert decision.safety_result == SafetyResult.REJECTED
    assert any("NON_SIMULATION_MODE" in r for r in decision.reason_codes)


def test_simulated_action_executor_and_rollback():
    """Verify virtual sandbox containment execution and rollback without OS side-effects."""
    executor = SimulatedActionExecutor(random_seed=42)

    # 1. Execute simulated block
    outcome = executor.execute(
        incident_id="inc-test-01",
        action=ActionType.SIMULATE_BLOCK,
        target_asset="192.168.10.5",
        is_attack=True,
    )

    assert isinstance(outcome, SimulationOutcome)
    assert outcome.containment_success is True
    assert outcome.operational_disruption_cost == 12.0
    assert outcome.reward > 0
    assert "192.168.10.5" in executor.simulated_blocked_hosts

    # 2. Revert virtual containment
    rolled_back = executor.rollback("inc-test-01", "192.168.10.5")
    assert rolled_back is True
    assert "192.168.10.5" not in executor.simulated_blocked_hosts


def test_mitigation_planning_agent_proposals():
    """Verify MitigationPlanningAgent proposes valid allowlisted actions and includes safety gate evaluations."""
    agent = MitigationPlanningAgent()
    task = AgentTask(
        task_id="tsk-mit-01",
        incident_id="inc-test-01",
        agent_name=AgentName.MITIGATION_AGENT,
        parameters={},
        created_at=datetime.now(timezone.utc),
    )

    context = {
        "risk_score": 0.88,
        "target_asset": "192.168.10.5",
        "is_human_approved": False,
        "supporting_event_ids": ["evt-001"],
    }

    result = agent.run(task, context=context)

    assert isinstance(result, AgentRunResult)
    assert result.status == AgentRunStatus.COMPLETED
    assert result.agent_name == AgentName.MITIGATION_AGENT

    # Check that all proposed actions belong to the catalogue allowlist
    assert len(result.proposed_actions) > 0
    for act in result.proposed_actions:
        act_val = act.value if hasattr(act, "value") else str(act)
        assert act_val in [a.value for a in ActionType]
        assert is_allowed_action(act_val)

    assert result.structured_output["recommended_action"] == ActionType.SIMULATE_BLOCK.value
    assert len(result.findings) >= 1
