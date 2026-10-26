"""Tests for Phase 2: Data Ingestion and Dataset Adapter."""

from pathlib import Path
import pytest
from app.ingestion.base import BaseDatasetAdapter, IngestionBatch, QuarantineRecord
from app.ingestion.cic_ids2017 import CICIDS2017Adapter
from app.ingestion.replay import ReplayService
from app.schemas.events import NormalizedEvent


SAMPLE_CSV_PATH = Path(__file__).resolve().parents[2] / "data" / "samples" / "cic_ids2017_sample.csv"


def test_cic_ids2017_adapter_valid_row():
    """Verify that a valid raw CIC-IDS2017 row normalizes accurately."""
    adapter = CICIDS2017Adapter(dataset_id="CIC-IDS2017-Test", run_id="run-test-01")
    raw_row = {
        "Flow Duration": "124800",
        "Total Fwd Packets": "68",
        "Total Backward Packets": "1",
        "Flow Bytes/s": "14820.5",
        "Fwd Packet Length Mean": "42.0",
        "SYN Flag Count": "1",
        "RST Flag Count": "0",
        "Bwd Packets/s": "8.0",
        "Destination Port": "80",
        "Source IP": "192.168.10.50",
        "Destination IP": "192.168.10.5",
        "Timestamp": "2026-10-14 04:12:01",
        "Label": "DoS-Slowloris",
    }

    event, quarantine = adapter.process_row(raw_row, row_index=1)
    assert quarantine is None
    assert isinstance(event, NormalizedEvent)
    assert event.event_id == "evt-cic-0001"
    assert event.source_asset == "192.168.10.50"
    assert event.target_asset == "192.168.10.5"
    assert event.raw_label == "DoS-Slowloris"
    assert event.dataset_id == "CIC-IDS2017-Test"
    assert event.run_id == "run-test-01"

    # Verify features and label exclusion
    assert "label" not in event.features
    assert "Label" not in event.features
    assert event.features["flow_duration"] == 124800.0
    assert event.features["total_fwd_packets"] == 68
    assert event.features["destination_port"] == 80


def test_cic_ids2017_adapter_quarantine_negative_duration():
    """Verify that negative flow duration is rejected and quarantined."""
    adapter = CICIDS2017Adapter()
    raw_row = {
        "Flow Duration": "-500",
        "Total Fwd Packets": "10",
        "Total Backward Packets": "0",
        "Flow Bytes/s": "1000.0",
        "Fwd Packet Length Mean": "30.0",
        "SYN Flag Count": "1",
        "RST Flag Count": "0",
        "Bwd Packets/s": "0.0",
        "Destination Port": "80",
        "Label": "MALFORMED",
    }

    event, quarantine = adapter.process_row(raw_row, row_index=42)
    assert event is None
    assert isinstance(quarantine, QuarantineRecord)
    assert quarantine.row_index == 42
    assert "Invalid 'Flow Duration'" in quarantine.error_reason


def test_cic_ids2017_adapter_quarantine_nan_inf():
    """Verify that NaN and Inf are rejected and quarantined."""
    adapter = CICIDS2017Adapter()
    raw_row = {
        "Flow Duration": "1000",
        "Total Fwd Packets": "NaN",
        "Total Backward Packets": "0",
        "Flow Bytes/s": "Infinity",
        "Fwd Packet Length Mean": "30.0",
        "SYN Flag Count": "1",
        "RST Flag Count": "0",
        "Bwd Packets/s": "0.0",
        "Destination Port": "80",
        "Label": "MALFORMED",
    }

    event, quarantine = adapter.process_row(raw_row, row_index=43)
    assert event is None
    assert isinstance(quarantine, QuarantineRecord)
    assert quarantine.row_index == 43


def test_replay_service_process_sample_file():
    """Test full replay of synthetic fixture CSV file."""
    assert SAMPLE_CSV_PATH.exists(), f"Sample CSV missing at {SAMPLE_CSV_PATH}"
    replay = ReplayService(adapter=CICIDS2017Adapter(dataset_id="CIC-IDS2017-Friday"))
    batch = replay.process_file(SAMPLE_CSV_PATH)

    assert isinstance(batch, IngestionBatch)
    assert batch.total_rows == 24
    # 22 valid rows, 2 malformed rows at the end of the file
    assert len(batch.valid_events) == 22
    assert len(batch.quarantined_rows) == 2

    # Check event order determinism
    first_event = batch.valid_events[0]
    assert first_event.event_id == "evt-cic-0001"
    assert first_event.raw_label == "BENIGN"

    second_event = batch.valid_events[1]
    assert second_event.event_id == "evt-cic-0002"


def test_replay_service_stream():
    """Test generator-based streaming replay."""
    replay = ReplayService(adapter=CICIDS2017Adapter())
    events = list(replay.replay_stream(SAMPLE_CSV_PATH, max_rows=5))

    assert len(events) == 5
    assert [e.event_id for e in events] == [
        "evt-cic-0001",
        "evt-cic-0002",
        "evt-cic-0003",
        "evt-cic-0004",
        "evt-cic-0005",
    ]
