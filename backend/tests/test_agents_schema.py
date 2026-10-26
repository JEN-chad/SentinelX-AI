"""Tests for Agent Contracts, Role Boundaries, and Action Allowlists."""

from datetime import datetime, timezone
import pytest
from pydantic import ValidationError
from app.schemas.agents import AgentRunResult, AgentTask
from app.schemas.common import ActionType, AgentName, AgentRunStatus
from app.schemas.evidence import EvidenceReference, EvidenceType


def test_valid_mitigation_agent_run():
    result = AgentRunResult(
        agent_run_id="run-mit-0001",
        agent_name=AgentName.MITIGATION_AGENT,
        incident_id="inc-demo-0001",
        status=AgentRunStatus.COMPLETED,
        findings=[],
        proposed_actions=[ActionType.SIMULATE_BLOCK, ActionType.RAISE_ALERT],
        conflict_flags=[],
        summary="Proposed simulating temporary block on attacker IP with approval gate.",
        structured_output={"estimated_disruption_score": 0.15},
        duration_ms=45.2,
        created_at=datetime.now(timezone.utc)
    )
    assert result.agent_name == AgentName.MITIGATION_AGENT
    assert len(result.proposed_actions) == 2
    assert ActionType.SIMULATE_BLOCK in result.proposed_actions


def test_reject_unregistered_action():
    """Agent output CANNOT include an unregistered action (Action allowlist requirement)."""
    with pytest.raises(ValidationError):
        AgentRunResult(
            agent_run_id="run-mit-0002",
            agent_name=AgentName.MITIGATION_AGENT,
            incident_id="inc-demo-0001",
            status=AgentRunStatus.COMPLETED,
            proposed_actions=["execute_arbitrary_shell_command"],  # Not in ActionType!
            summary="Invalid action proposal",
            duration_ms=10.0,
            created_at=datetime.now(timezone.utc)
        )


def test_analytical_agents_cannot_propose_actions():
    """Detection and Investigation agents cannot propose executable mitigation actions."""
    with pytest.raises(ValidationError, match="analytical only and cannot propose executable actions"):
        AgentRunResult(
            agent_run_id="run-inv-0002",
            agent_name=AgentName.INVESTIGATION_AGENT,
            incident_id="inc-demo-0001",
            status=AgentRunStatus.COMPLETED,
            proposed_actions=[ActionType.SIMULATE_BLOCK],
            summary="Investigation agent illegally proposing block action",
            duration_ms=12.0,
            created_at=datetime.now(timezone.utc)
        )

    with pytest.raises(ValidationError, match="analytical only and cannot propose executable actions"):
        AgentRunResult(
            agent_run_id="run-det-0002",
            agent_name=AgentName.DETECTION_AGENT,
            incident_id="inc-demo-0001",
            status=AgentRunStatus.COMPLETED,
            proposed_actions=[ActionType.RAISE_ALERT],
            summary="Detection agent illegally proposing action",
            duration_ms=5.0,
            created_at=datetime.now(timezone.utc)
        )


def test_agent_task_dispatch():
    task = AgentTask(
        task_id="tsk-001",
        incident_id="inc-demo-0001",
        agent_name=AgentName.INVESTIGATION_AGENT,
        parameters={"correlation_window_sec": 300},
        created_at=datetime.now(timezone.utc)
    )
    assert task.task_id == "tsk-001"
    assert task.agent_name == AgentName.INVESTIGATION_AGENT
