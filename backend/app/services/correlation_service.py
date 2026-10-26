"""SentinelX AI - Event Correlation Service

Applies deterministic multi-factor correlation rules to group related flow events
into an incident evidence chain without double-counting.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, Field

from app.schemas.events import NormalizedEvent


class CorrelationMatch(BaseModel):
    """Result of correlating a candidate event with an incident's seed event."""
    event_id: str
    rule_name: str
    reason: str
    confidence: float
    matched_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CorrelationService:
    """Service providing deterministic temporal and structural event correlation."""

    def __init__(self, default_time_window_seconds: int = 600):
        self.default_time_window_seconds = default_time_window_seconds

    def evaluate_pair(
        self,
        seed: NormalizedEvent,
        candidate: NormalizedEvent,
        time_window_seconds: Optional[int] = None,
    ) -> Optional[CorrelationMatch]:
        """Evaluate if a candidate event correlates with a seed event based on explicit rules."""
        if seed.event_id == candidate.event_id:
            return None

        window = time_window_seconds or self.default_time_window_seconds
        time_diff = abs((seed.event_time - candidate.event_time).total_seconds())

        # If outside time window, cannot correlate under temporal proximity rules
        if time_diff > window:
            return None

        # Rule 1: Direct Host Pair Affinity (same source and destination)
        if seed.source_asset == candidate.source_asset and seed.target_asset == candidate.target_asset:
            seed_port = seed.features.get("destination_port")
            cand_port = candidate.features.get("destination_port")
            if seed_port and cand_port and seed_port == cand_port:
                return CorrelationMatch(
                    event_id=candidate.event_id,
                    rule_name="HOST_PAIR_SERVICE_BURST",
                    reason=(
                        f"Temporal burst targeting identical host and service: {seed.source_asset} -> "
                        f"{seed.target_asset}:{seed_port} within {int(time_diff)}s."
                    ),
                    confidence=0.95,
                )
            return CorrelationMatch(
                event_id=candidate.event_id,
                rule_name="HOST_PAIR_CONVERGENCE",
                reason=(
                    f"Traffic flow between identical endpoints {seed.source_asset} and "
                    f"{seed.target_asset} within {int(time_diff)}s window."
                ),
                confidence=0.85,
            )

        # Rule 2: Multi-port Reconnaissance Sweep (PortScan pattern)
        if seed.source_asset == candidate.source_asset and seed.target_asset == candidate.target_asset:
            seed_port = seed.features.get("destination_port")
            cand_port = candidate.features.get("destination_port")
            if seed_port and cand_port and seed_port != cand_port:
                return CorrelationMatch(
                    event_id=candidate.event_id,
                    rule_name="PORT_SCAN_SWEEP",
                    reason=(
                        f"Reconnaissance pattern: Source {seed.source_asset} probed multiple ports "
                        f"({seed_port} and {cand_port}) on {seed.target_asset} within {int(time_diff)}s."
                    ),
                    confidence=0.90,
                )

        # Rule 3: Targeted Denial of Service / Multi-Source Flood
        if seed.target_asset == candidate.target_asset:
            seed_port = seed.features.get("destination_port")
            cand_port = candidate.features.get("destination_port")
            if seed_port and cand_port and seed_port == cand_port and seed_port in [80, 443, 8080]:
                return CorrelationMatch(
                    event_id=candidate.event_id,
                    rule_name="TARGET_SERVICE_CONCENTRATION",
                    reason=(
                        f"Co-occurring flow against victim service {seed.target_asset}:{seed_port} "
                        f"from {candidate.source_asset} within {int(time_diff)}s."
                    ),
                    confidence=0.75,
                )

        return None

    def correlate_candidates(
        self,
        seed: NormalizedEvent,
        candidates: List[NormalizedEvent],
        time_window_seconds: Optional[int] = None,
    ) -> List[Tuple[NormalizedEvent, CorrelationMatch]]:
        """Find all correlated candidate events without duplicates or double-counting."""
        correlated: List[Tuple[NormalizedEvent, CorrelationMatch]] = []
        seen_event_ids: Set[str] = {seed.event_id}

        for cand in candidates:
            if cand.event_id in seen_event_ids:
                continue

            match = self.evaluate_pair(seed, cand, time_window_seconds=time_window_seconds)
            if match:
                seen_event_ids.add(cand.event_id)
                correlated.append((cand, match))

        return correlated
