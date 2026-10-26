"""SentinelX AI - Normalized Event Schemas

Contracts for ingested network-flow and simulation event records.
Labels are tracked as audit/ground-truth metadata and strictly segregated from model features.
"""

from datetime import datetime
import re
from typing import Any, Dict, List, Optional, Union
from pydantic import Field, field_validator
from .common import SentinelBaseModel, ensure_utc_datetime


ID_PATTERN = re.compile(r"^[a-zA-Z0-9_\-\.]{3,64}$")


class NormalizedEvent(SentinelBaseModel):
    """Canonical normalized event representation used across SentinelX AI."""
    event_id: str = Field(
        ...,
        description="Unique identifier for the event (e.g. evt-cic-0001 or UUID)"
    )
    event_time: datetime = Field(
        ...,
        description="Original occurrence timestamp of the event in UTC"
    )
    ingested_at: datetime = Field(
        ...,
        description="Timestamp when event was ingested by SentinelX in UTC"
    )
    source: str = Field(
        ...,
        min_length=2,
        max_length=64,
        description="Source of the event (e.g. 'dataset_replay', 'simulator')"
    )
    source_asset: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="Origin host, IP, or simulated asset identifier"
    )
    target_asset: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="Destination host, IP, or simulated asset identifier"
    )
    event_type: str = Field(
        ...,
        min_length=2,
        max_length=64,
        description="Category/type of event (e.g. 'flow_record', 'repeated_login_failures')"
    )
    features: Dict[str, Union[float, int, str, bool]] = Field(
        default_factory=dict,
        description="Extracted feature dictionary for threat detection models"
    )
    dataset_id: Optional[str] = Field(
        default=None,
        max_length=64,
        description="Identifier of originating dataset (e.g. 'CIC-IDS2017-Friday')"
    )
    run_id: Optional[str] = Field(
        default=None,
        max_length=64,
        description="Replay or experiment execution identifier"
    )
    raw_label: Optional[str] = Field(
        default=None,
        max_length=64,
        description="Ground truth or dataset-provided label. Auditing only; strictly excluded from model inference input."
    )
    schema_version: str = Field(
        default="v1",
        description="Schema contract version"
    )

    @field_validator("event_id")
    @classmethod
    def validate_event_id(cls, value: str) -> str:
        if not ID_PATTERN.match(value):
            raise ValueError(
                f"Invalid event_id '{value}'. Must be alphanumeric with hyphens/underscores (3-64 chars)."
            )
        return value

    @field_validator("event_time", "ingested_at")
    @classmethod
    def validate_utc(cls, value: datetime) -> datetime:
        return ensure_utc_datetime(value)

    @field_validator("features")
    @classmethod
    def validate_features_size(cls, value: Dict[str, Any]) -> Dict[str, Any]:
        if len(value) > 250:
            raise ValueError(f"Feature count ({len(value)}) exceeds maximum allowed limit (250).")
        return value


class EventBatchIngest(SentinelBaseModel):
    """Batch ingestion request schema for replay and simulator streams."""
    batch_id: str = Field(..., description="Unique batch identifier")
    events: List[NormalizedEvent] = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="List of normalized events (1 to 1000 per batch)"
    )
    dataset_id: Optional[str] = None
    run_id: Optional[str] = None

    @field_validator("batch_id")
    @classmethod
    def validate_batch_id(cls, value: str) -> str:
        if not ID_PATTERN.match(value):
            raise ValueError(f"Invalid batch_id '{value}'.")
        return value


class EventFilterParams(SentinelBaseModel):
    """Query parameter validation for event exploration and filtering."""
    source_asset: Optional[str] = None
    target_asset: Optional[str] = None
    event_type: Optional[str] = None
    dataset_id: Optional[str] = None
    run_id: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    limit: int = Field(default=50, ge=1, le=500)
    offset: int = Field(default=0, ge=0)

    @field_validator("start_time", "end_time")
    @classmethod
    def validate_query_timestamps(cls, value: Optional[datetime]) -> Optional[datetime]:
        if value is not None:
            return ensure_utc_datetime(value)
        return None
