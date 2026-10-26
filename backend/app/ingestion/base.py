"""SentinelX AI - Dataset Adapter Base Contracts

Abstract base classes and quarantine reporting models for multi-dataset ingestion.
Strict rule: labels are captured as metadata, never included in feature dicts.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field
from app.schemas.events import NormalizedEvent


class QuarantineRecord(BaseModel):
    """Encapsulates a rejected or malformed row that failed data quality gates."""
    row_index: int
    raw_data: Dict[str, Any]
    error_reason: str
    dataset_id: str
    quarantined_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class IngestionBatch(BaseModel):
    """Result of batch ingestion processing."""
    dataset_id: str
    run_id: str
    total_rows: int
    valid_events: List[NormalizedEvent]
    quarantined_rows: List[QuarantineRecord]


class BaseDatasetAdapter(ABC):
    """Abstract base for dataset-specific ingestion adapters."""

    def __init__(self, dataset_id: str, run_id: Optional[str] = None):
        self.dataset_id = dataset_id
        self.run_id = run_id or f"run-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"

    @abstractmethod
    def process_row(self, raw_row: Dict[str, Any], row_index: int) -> Tuple[Optional[NormalizedEvent], Optional[QuarantineRecord]]:
        """Normalize a single source record into a Canonical NormalizedEvent.
        
        Returns:
            (NormalizedEvent, None) if valid
            (None, QuarantineRecord) if malformed or quarantined
        """
        pass
