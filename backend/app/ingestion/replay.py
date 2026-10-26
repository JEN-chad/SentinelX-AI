"""SentinelX AI - Offline Dataset Replay Service

Orchestrates deterministic batch and stream replay of offline flow datasets.
"""

from pathlib import Path
from typing import Generator, List, Optional, Union

from app.schemas.events import NormalizedEvent
from .base import BaseDatasetAdapter, IngestionBatch, QuarantineRecord
from .cic_ids2017 import CICIDS2017Adapter
from .csv_reader import read_csv_in_chunks


class ReplayService:
    """Service for deterministic offline dataset replay."""

    def __init__(self, adapter: Optional[BaseDatasetAdapter] = None):
        self.adapter = adapter or CICIDS2017Adapter()

    def process_file(
        self,
        file_path: Union[str, Path],
        max_rows: Optional[int] = None,
        chunk_size: int = 100,
    ) -> IngestionBatch:
        """Process an entire CSV dataset and return valid events and quarantined rows."""
        valid_events: List[NormalizedEvent] = []
        quarantined: List[QuarantineRecord] = []
        row_counter = 0

        for chunk in read_csv_in_chunks(file_path, chunk_size=chunk_size):
            for raw_row in chunk:
                row_counter += 1
                if max_rows and row_counter > max_rows:
                    break

                event, quarantine = self.adapter.process_row(raw_row, row_index=row_counter)
                if event:
                    valid_events.append(event)
                elif quarantine:
                    quarantined.append(quarantine)

            if max_rows and row_counter >= max_rows:
                break

        return IngestionBatch(
            dataset_id=self.adapter.dataset_id,
            run_id=self.adapter.run_id,
            total_rows=row_counter,
            valid_events=valid_events,
            quarantined_rows=quarantined,
        )

    def replay_stream(
        self,
        file_path: Union[str, Path],
        max_rows: Optional[int] = None,
        chunk_size: int = 10,
    ) -> Generator[NormalizedEvent, None, None]:
        """Stream valid normalized events one-by-one in deterministic sequence."""
        row_counter = 0
        for chunk in read_csv_in_chunks(file_path, chunk_size=chunk_size):
            for raw_row in chunk:
                row_counter += 1
                if max_rows and row_counter > max_rows:
                    return

                event, _ = self.adapter.process_row(raw_row, row_index=row_counter)
                if event:
                    yield event
