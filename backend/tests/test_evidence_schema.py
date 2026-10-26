"""Tests for Evidence Reference Schemas and Provenance Tracking."""

from datetime import datetime, timezone
import pytest
from pydantic import ValidationError
from app.schemas.evidence import EvidenceReference, EvidenceType


def test_valid_evidence_parses(valid_evidence_dict):
    evidence = EvidenceReference.model_validate(valid_evidence_dict)
    assert evidence.evidence_id == "evd-demo-0001"
    assert evidence.is_inferred is False
    assert evidence.confidence == 0.92
    assert evidence.evidence_type == EvidenceType.ANOMALY_SIGNAL
    assert evidence.timestamp.tzinfo == timezone.utc


def test_observed_evidence_requires_event_link():
    """Observed evidence (is_inferred=False) must link to at least one event ID."""
    with pytest.raises(ValidationError, match="must reference at least one event_id"):
        EvidenceReference(
            evidence_id="evd-002",
            event_id=None,
            supporting_event_ids=[],
            evidence_type=EvidenceType.OBSERVED_EVENT,
            is_inferred=False,
            description="Raw observation without event link is prohibited",
            confidence=0.9,
            source_component="network_sensor",
            timestamp=datetime.now(timezone.utc)
        )


def test_inferred_evidence_allowed_with_explicit_flag():
    """Inferred evidence (is_inferred=True) is allowed derived claims."""
    inferred = EvidenceReference(
        evidence_id="evd-003",
        event_id=None,
        supporting_event_ids=["evt-001", "evt-002"],
        evidence_type=EvidenceType.TIMELINE_CLUSTER,
        is_inferred=True,
        description="Correlated multi-event temporal anomaly sequence",
        confidence=0.85,
        source_component="investigation_agent",
        timestamp=datetime.now(timezone.utc)
    )
    assert inferred.is_inferred is True
    assert len(inferred.supporting_event_ids) == 2


def test_confidence_bounds_enforced():
    with pytest.raises(ValidationError):
        EvidenceReference(
            evidence_id="evd-004",
            event_id="evt-001",
            evidence_type=EvidenceType.OBSERVED_EVENT,
            is_inferred=False,
            description="Valid description",
            confidence=1.2,  # > 1.0 prohibited
            source_component="sensor",
            timestamp=datetime.now(timezone.utc)
        )
