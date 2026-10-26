"""Tests for Incident State, Lifecycle Transitions, and Constraints."""

from datetime import datetime, timedelta, timezone
import pytest
from pydantic import ValidationError
from app.schemas.incidents import (
    IncidentCreate,
    IncidentState,
    IncidentStatus,
    IncidentUpdate,
    can_transition,
)
from app.schemas.common import SeverityLevel


def test_valid_incident_parses(valid_incident_dict):
    incident = IncidentState.model_validate(valid_incident_dict)
    assert incident.incident_id == "inc-demo-0001"
    assert incident.status == IncidentStatus.INVESTIGATING
    assert incident.severity == SeverityLevel.HIGH
    assert incident.risk_score == 0.84
    assert len(incident.event_ids) == 1
    assert len(incident.evidence) == 1


def test_incident_state_transitions():
    """Verify allowable and illegal state transitions as defined in architecture.md."""
    # Legal transitions
    assert can_transition(IncidentStatus.RECEIVED, IncidentStatus.VALIDATED) is True
    assert can_transition(IncidentStatus.VALIDATED, IncidentStatus.SCORED) is True
    assert can_transition(IncidentStatus.SCORED, IncidentStatus.INVESTIGATING) is True
    assert can_transition(IncidentStatus.INVESTIGATING, IncidentStatus.RISK_ASSESSED) is True
    assert can_transition(IncidentStatus.RISK_ASSESSED, IncidentStatus.RESPONSE_PROPOSED) is True
    assert can_transition(IncidentStatus.RESPONSE_PROPOSED, IncidentStatus.APPROVAL_REQUIRED) is True
    assert can_transition(IncidentStatus.RESPONSE_PROPOSED, IncidentStatus.SIMULATING) is True
    assert can_transition(IncidentStatus.SIMULATING, IncidentStatus.OUTCOME_RECORDED) is True
    assert can_transition(IncidentStatus.OUTCOME_RECORDED, IncidentStatus.CLOSED) is True

    # Illegal transitions (skipping states or moving backwards)
    assert can_transition(IncidentStatus.RECEIVED, IncidentStatus.SIMULATING) is False
    assert can_transition(IncidentStatus.RECEIVED, IncidentStatus.CLOSED) is False
    assert can_transition(IncidentStatus.CLOSED, IncidentStatus.INVESTIGATING) is False
    assert can_transition(IncidentStatus.SCORED, IncidentStatus.RECEIVED) is False


def test_reject_empty_event_ids(valid_incident_dict):
    invalid_dict = valid_incident_dict.copy()
    invalid_dict["event_ids"] = []
    with pytest.raises(ValidationError):
        IncidentState.model_validate(invalid_dict)


def test_reject_chronologically_invalid_timestamps(valid_incident_dict):
    """updated_at cannot be prior to created_at."""
    invalid_dict = valid_incident_dict.copy()
    invalid_dict["created_at"] = "2026-10-14T08:00:10Z"
    invalid_dict["updated_at"] = "2026-10-14T08:00:00Z"
    with pytest.raises(ValidationError, match="updated_at cannot be prior to created_at"):
        IncidentState.model_validate(invalid_dict)


def test_incident_create_and_update():
    now = datetime.now(timezone.utc)
    create_payload = IncidentCreate(
        incident_id="inc-new-001",
        title="Candidate Brute Force Activity",
        initial_event_id="evt-demo-0001",
        severity=SeverityLevel.MEDIUM,
        risk_score=0.55,
        created_at=now
    )
    assert create_payload.incident_id == "inc-new-001"

    update_payload = IncidentUpdate(
        target_status=IncidentStatus.SCORED,
        risk_score=0.65,
        updated_at=now + timedelta(seconds=2)
    )
    assert update_payload.target_status == IncidentStatus.SCORED
    assert update_payload.risk_score == 0.65
