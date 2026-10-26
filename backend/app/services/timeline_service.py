"""SentinelX AI - Incident Timeline Construction Service

Assembles chronological, provenance-backed incident timelines from linked flow records.
Explicitly separates raw observed telemetry facts from inferred analytical conclusions.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel

from app.schemas.detections import DetectionResult
from app.schemas.events import NormalizedEvent


class TimelineEntry(BaseModel):
    """Single chronological step in an incident progression."""
    event_id: str
    timestamp: datetime
    source_asset: str
    target_asset: str
    event_type: str
    description: str
    is_inferred: bool
    anomaly_score: Optional[float] = None
    predicted_class: Optional[str] = None


class TimelineService:
    """Service building ordered incident timelines and identifying telemetry gaps."""

    @staticmethod
    def build_timeline(
        events: List[NormalizedEvent],
        detections: Optional[Dict[str, DetectionResult]] = None,
    ) -> List[TimelineEntry]:
        """Construct a chronologically sorted sequence of incident events."""
        det_map = detections or {}
        entries: List[TimelineEntry] = []

        # Sort events by timestamp in ascending order
        sorted_events = sorted(events, key=lambda e: e.event_time)

        for evt in sorted_events:
            det = det_map.get(evt.event_id)
            score = det.anomaly_score if det else None
            cls_name = det.predicted_class if det else evt.raw_label

            port = evt.features.get("destination_port", "?")
            fwd_pkts = evt.features.get("total_fwd_packets", 0)
            bwd_pkts = evt.features.get("total_bwd_packets", 0)

            desc = (
                f"Flow {evt.event_id}: {evt.source_asset} -> {evt.target_asset}:{port} "
                f"({fwd_pkts} fwd, {bwd_pkts} bwd packets)."
            )
            if cls_name and cls_name != "BENIGN":
                score_str = f" (score: {score:.2f})" if score is not None else ""
                desc += f" [Model tagged: {cls_name}{score_str}]"

            entries.append(
                TimelineEntry(
                    event_id=evt.event_id,
                    timestamp=evt.event_time,
                    source_asset=evt.source_asset,
                    target_asset=evt.target_asset,
                    event_type=evt.event_type,
                    description=desc,
                    is_inferred=False,
                    anomaly_score=score,
                    predicted_class=cls_name,
                )
            )

        return entries

    @staticmethod
    def detect_evidence_gaps_and_conflicts(events: List[NormalizedEvent]) -> Tuple[List[str], List[str]]:
        """Identify missing telemetry or contradictory flow flags across linked events."""
        gaps: List[str] = []
        conflicts: List[str] = []

        total_bwd_zero = 0
        has_rst = False
        has_syn = False

        for evt in events:
            bwd = evt.features.get("total_bwd_packets", 0)
            if bwd == 0:
                total_bwd_zero += 1

            if evt.features.get("rst_flag_count", 0) == 1:
                has_rst = True
            if evt.features.get("syn_flag_count", 0) == 1:
                has_syn = True

        # Gap: Unidirectional traffic (no reverse response packets)
        if len(events) > 0 and total_bwd_zero == len(events):
            gaps.append("ZERO_REVERSE_TRAFFIC: Target asset emitted 0 response packets across all linked flows.")

        # Conflict: Simultaneous active SYN probe and RST reset in short sequence
        if has_syn and has_rst:
            conflicts.append("CONTRADICTORY_FLAGS: Both SYN initiation and RST teardown observed across linked burst.")

        return gaps, conflicts
