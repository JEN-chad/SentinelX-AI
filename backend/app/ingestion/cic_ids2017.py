"""SentinelX AI - CIC-IDS2017 Dataset Adapter

Normalizes raw flow records into canonical NormalizedEvent instances.
Guarantees strict segregation of ground-truth labels from inference feature dicts.
"""

from datetime import datetime, timezone
import re
from typing import Any, Dict, Optional, Tuple

from app.schemas.events import NormalizedEvent
from .base import BaseDatasetAdapter, QuarantineRecord
from .validation import is_valid_numeric, validate_required_columns


class CICIDS2017Adapter(BaseDatasetAdapter):
    """Adapter for CIC-IDS2017 network flow records."""

    REQUIRED_COLUMNS = [
        "Flow Duration",
        "Total Fwd Packets",
        "Total Backward Packets",
        "Flow Bytes/s",
        "Fwd Packet Length Mean",
        "SYN Flag Count",
        "RST Flag Count",
        "Bwd Packets/s",
        "Destination Port",
        "Label",
    ]

    def __init__(self, dataset_id: str = "CIC-IDS2017", run_id: Optional[str] = None):
        super().__init__(dataset_id=dataset_id, run_id=run_id)

    def _clean_dict(self, raw_row: Dict[str, Any]) -> Dict[str, Any]:
        """Strip leading/trailing whitespace from dict keys and string values."""
        clean = {}
        for k, v in raw_row.items():
            key = k.strip()
            val = v.strip() if isinstance(v, str) else v
            clean[key] = val
        return clean

    def process_row(self, raw_row: Dict[str, Any], row_index: int) -> Tuple[Optional[NormalizedEvent], Optional[QuarantineRecord]]:
        clean_row = self._clean_dict(raw_row)

        # 1. Validate required columns
        valid, err = validate_required_columns(clean_row, self.REQUIRED_COLUMNS)
        if not valid:
            return None, QuarantineRecord(
                row_index=row_index,
                raw_data=clean_row,
                error_reason=err or "Missing columns",
                dataset_id=self.dataset_id,
            )

        # 2. Extract and validate numeric features
        features: Dict[str, Any] = {}

        # flow_duration: must be non-negative
        ok, flow_dur, err = is_valid_numeric(clean_row.get("Flow Duration"), min_val=0.0)
        if not ok:
            return None, QuarantineRecord(
                row_index=row_index,
                raw_data=clean_row,
                error_reason=f"Invalid 'Flow Duration': {err}",
                dataset_id=self.dataset_id,
            )
        features["flow_duration"] = float(flow_dur)

        # total_fwd_packets: integer >= 0
        ok, fwd_pkts, err = is_valid_numeric(clean_row.get("Total Fwd Packets"), min_val=0.0)
        if not ok:
            return None, QuarantineRecord(
                row_index=row_index,
                raw_data=clean_row,
                error_reason=f"Invalid 'Total Fwd Packets': {err}",
                dataset_id=self.dataset_id,
            )
        features["total_fwd_packets"] = int(fwd_pkts)

        # total_bwd_packets: integer >= 0
        ok, bwd_pkts, err = is_valid_numeric(clean_row.get("Total Backward Packets"), min_val=0.0)
        if not ok:
            return None, QuarantineRecord(
                row_index=row_index,
                raw_data=clean_row,
                error_reason=f"Invalid 'Total Backward Packets': {err}",
                dataset_id=self.dataset_id,
            )
        features["total_bwd_packets"] = int(bwd_pkts)

        # flow_bytes_per_sec: float >= 0
        ok, flow_bps, err = is_valid_numeric(clean_row.get("Flow Bytes/s"), min_val=0.0)
        if not ok:
            return None, QuarantineRecord(
                row_index=row_index,
                raw_data=clean_row,
                error_reason=f"Invalid 'Flow Bytes/s': {err}",
                dataset_id=self.dataset_id,
            )
        features["flow_bytes_per_sec"] = float(flow_bps)

        # fwd_packet_length_mean: float >= 0
        ok, fwd_mean, err = is_valid_numeric(clean_row.get("Fwd Packet Length Mean"), min_val=0.0)
        if not ok:
            return None, QuarantineRecord(
                row_index=row_index,
                raw_data=clean_row,
                error_reason=f"Invalid 'Fwd Packet Length Mean': {err}",
                dataset_id=self.dataset_id,
            )
        features["fwd_packet_length_mean"] = float(fwd_mean)

        # syn_flag_count: 0 or 1
        ok, syn_flag, err = is_valid_numeric(clean_row.get("SYN Flag Count"), min_val=0.0, max_val=1.0)
        if not ok:
            return None, QuarantineRecord(
                row_index=row_index,
                raw_data=clean_row,
                error_reason=f"Invalid 'SYN Flag Count': {err}",
                dataset_id=self.dataset_id,
            )
        features["syn_flag_count"] = int(syn_flag)

        # rst_flag_count: 0 or 1
        ok, rst_flag, err = is_valid_numeric(clean_row.get("RST Flag Count"), min_val=0.0, max_val=1.0)
        if not ok:
            return None, QuarantineRecord(
                row_index=row_index,
                raw_data=clean_row,
                error_reason=f"Invalid 'RST Flag Count': {err}",
                dataset_id=self.dataset_id,
            )
        features["rst_flag_count"] = int(rst_flag)

        # bwd_packets_per_sec: float >= 0
        ok, bwd_pps, err = is_valid_numeric(clean_row.get("Bwd Packets/s"), min_val=0.0)
        if not ok:
            return None, QuarantineRecord(
                row_index=row_index,
                raw_data=clean_row,
                error_reason=f"Invalid 'Bwd Packets/s': {err}",
                dataset_id=self.dataset_id,
            )
        features["bwd_packets_per_sec"] = float(bwd_pps)

        # destination_port: integer 1..65535
        ok, dst_port, err = is_valid_numeric(clean_row.get("Destination Port"), min_val=0.0, max_val=65535.0)
        if not ok:
            return None, QuarantineRecord(
                row_index=row_index,
                raw_data=clean_row,
                error_reason=f"Invalid 'Destination Port': {err}",
                dataset_id=self.dataset_id,
            )
        features["destination_port"] = int(dst_port)

        # 3. Label Isolation: Ground-truth strictly stored as metadata, NEVER in features
        raw_label = str(clean_row.get("Label", "UNKNOWN")).strip()
        assert "label" not in features, "Target leakage prevention violation"
        assert "Label" not in features, "Target leakage prevention violation"

        # 4. Extract asset endpoints and timestamps
        source_ip = str(clean_row.get("Source IP", f"192.168.10.{row_index % 100 + 10}"))
        target_ip = str(clean_row.get("Destination IP", "192.168.10.5"))

        # Parse timestamp or default to UTC now
        ts_raw = clean_row.get("Timestamp")
        if ts_raw:
            try:
                # Handle standard formats: '2026-10-14 04:12:00' or '14/10/2026 04:12:00'
                if "/" in str(ts_raw):
                    event_time = datetime.strptime(str(ts_raw), "%d/%m/%Y %H:%M:%S").replace(tzinfo=timezone.utc)
                else:
                    event_time = datetime.fromisoformat(str(ts_raw).replace(" ", "T")).replace(tzinfo=timezone.utc)
            except Exception:
                event_time = datetime.now(timezone.utc)
        else:
            event_time = datetime.now(timezone.utc)

        ingested_at = datetime.now(timezone.utc)
        event_id = f"evt-cic-{row_index:04d}"

        # Classify event_type from port/features for display
        if features["destination_port"] == 80 and features["flow_duration"] > 100000:
            event_type = "http_persistent_flow"
        elif features["destination_port"] in [22, 139, 445, 8080] and features["total_fwd_packets"] <= 2:
            event_type = "port_scan_sweep"
        else:
            event_type = "network_flow_record"

        event = NormalizedEvent(
            event_id=event_id,
            event_time=event_time,
            ingested_at=ingested_at,
            source="cic_ids2017_replay",
            source_asset=source_ip,
            target_asset=target_ip,
            event_type=event_type,
            features=features,
            dataset_id=self.dataset_id,
            run_id=self.run_id,
            raw_label=raw_label,
            schema_version="v1",
        )

        return event, None
