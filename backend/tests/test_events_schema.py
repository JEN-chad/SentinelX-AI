"""Tests for Normalized Event Schemas and Ingestion Contracts."""

from datetime import datetime, timezone
import pytest
from pydantic import ValidationError
from app.schemas.events import EventBatchIngest, EventFilterParams, NormalizedEvent


def test_valid_event_parses_correctly(valid_event_dict):
    event = NormalizedEvent.model_validate(valid_event_dict)
    assert event.event_id == "evt-demo-0001"
    assert event.source == "dataset_replay"
    assert event.event_time.tzinfo == timezone.utc
    assert event.ingested_at.tzinfo == timezone.utc
    assert event.features["flow_duration"] == 120500
    assert event.raw_label == "DoS-Slowloris"
    assert event.schema_version == "v1"


def test_invalid_event_rejected(invalid_event_dict):
    with pytest.raises(ValidationError) as exc_info:
        NormalizedEvent.model_validate(invalid_event_dict)
    errors = str(exc_info.value)
    assert "event_id" in errors or "event_time" in errors or "ingested_at" in errors


def test_reject_naive_datetime():
    """Verify that datetimes without timezone awareness are rejected."""
    naive_dt = datetime(2026, 10, 14, 8, 0, 0)
    with pytest.raises(ValidationError, match="timezone-aware"):
        NormalizedEvent(
            event_id="evt-001",
            event_time=naive_dt,
            ingested_at=datetime.now(timezone.utc),
            source="test",
            source_asset="host-1",
            target_asset="host-2",
            event_type="test_event",
            features={}
        )


def test_reject_oversized_features():
    """Reject payloads that exceed max allowed features."""
    huge_features = {f"feat_{i}": float(i) for i in range(251)}
    with pytest.raises(ValidationError, match="exceeds maximum allowed limit"):
        NormalizedEvent(
            event_id="evt-002",
            event_time=datetime.now(timezone.utc),
            ingested_at=datetime.now(timezone.utc),
            source="test",
            source_asset="host-1",
            target_asset="host-2",
            event_type="test_event",
            features=huge_features
        )


def test_event_batch_ingest(valid_event_dict):
    event = NormalizedEvent.model_validate(valid_event_dict)
    batch = EventBatchIngest(
        batch_id="batch-001",
        events=[event]
    )
    assert batch.batch_id == "batch-001"
    assert len(batch.events) == 1

    # Empty batch must be rejected
    with pytest.raises(ValidationError):
        EventBatchIngest(batch_id="batch-002", events=[])


def test_event_filter_params():
    params = EventFilterParams(
        source_asset="192.168.1.100",
        limit=100,
        offset=10
    )
    assert params.limit == 100
    assert params.offset == 10

    # Test limit boundary
    with pytest.raises(ValidationError):
        EventFilterParams(limit=0)
    with pytest.raises(ValidationError):
        EventFilterParams(limit=501)
