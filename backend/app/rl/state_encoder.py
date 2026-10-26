"""SentinelX AI - RL State Discretizer and Encoder (Phase 10)

Discretizes continuous observation telemetry (risk, criticality, recurrence, confidence)
into a compact, deterministic state index suitable for tabular Q-learning.
"""

from typing import Any, Dict, Union
from pydantic import BaseModel

from app.simulator.environment import Observation

NUM_RISK_BINS = 3
NUM_CRITICALITY_BINS = 3
NUM_RECURRENCE_BINS = 3
NUM_CONFIDENCE_BINS = 2
TOTAL_DISCRETE_STATES = NUM_RISK_BINS * NUM_CRITICALITY_BINS * NUM_RECURRENCE_BINS * NUM_CONFIDENCE_BINS  # 54


class DiscreteState(BaseModel):
    """Human-readable discrete bucket labels for an encoded state."""
    state_index: int
    risk_bucket: str          # "LOW", "MEDIUM", "HIGH"
    criticality_bucket: str   # "LOW", "MEDIUM", "HIGH"
    recurrence_bucket: str    # "SINGLE", "BURST", "PERSISTENT"
    confidence_bucket: str    # "UNCERTAIN", "CONFIDENT"


class ObservationEncoder:
    """Encodes continuous observation dictionary into a deterministic discrete state index [0..53]."""

    @staticmethod
    def encode(observation: Union[Observation, Dict[str, Any]]) -> int:
        """Map continuous observation features into discrete state index."""
        if isinstance(observation, dict):
            risk = float(observation.get("observable_risk", 0.0))
            criticality = int(observation.get("asset_criticality", 3))
            recurrence = int(observation.get("recurrence_count", 1))
            confidence = float(observation.get("observable_confidence", 0.5))
        else:
            risk = observation.observable_risk
            criticality = observation.asset_criticality
            recurrence = observation.recurrence_count
            confidence = observation.observable_confidence

        # 1. Risk bin: [0..0.4) -> 0 (LOW), [0.4..0.7) -> 1 (MEDIUM), [0.7..1.0] -> 2 (HIGH)
        if risk < 0.40:
            r_bin = 0
        elif risk < 0.70:
            r_bin = 1
        else:
            r_bin = 2

        # 2. Asset Criticality bin: 1, 2 -> 0 (LOW), 3 -> 1 (MEDIUM), 4, 5 -> 2 (HIGH)
        if criticality <= 2:
            c_bin = 0
        elif criticality == 3:
            c_bin = 1
        else:
            c_bin = 2

        # 3. Recurrence bin: 1 -> 0 (SINGLE), 2..4 -> 1 (BURST), >= 5 -> 2 (PERSISTENT)
        if recurrence <= 1:
            rec_bin = 0
        elif recurrence <= 4:
            rec_bin = 1
        else:
            rec_bin = 2

        # 4. Confidence bin: [0..0.65) -> 0 (UNCERTAIN), [0.65..1.0] -> 1 (CONFIDENT)
        if confidence < 0.65:
            conf_bin = 0
        else:
            conf_bin = 1

        # Compute row-major flat index
        index = (
            r_bin * (NUM_CRITICALITY_BINS * NUM_RECURRENCE_BINS * NUM_CONFIDENCE_BINS)
            + c_bin * (NUM_RECURRENCE_BINS * NUM_CONFIDENCE_BINS)
            + rec_bin * NUM_CONFIDENCE_BINS
            + conf_bin
        )

        return int(index)

    @staticmethod
    def decode(state_index: int) -> DiscreteState:
        """Decode discrete index [0..53] back into structured discrete bucket representation."""
        if not (0 <= state_index < TOTAL_DISCRETE_STATES):
            raise ValueError(f"State index {state_index} out of range [0..{TOTAL_DISCRETE_STATES - 1}].")

        idx = state_index
        conf_bin = idx % NUM_CONFIDENCE_BINS
        idx //= NUM_CONFIDENCE_BINS

        rec_bin = idx % NUM_RECURRENCE_BINS
        idx //= NUM_RECURRENCE_BINS

        c_bin = idx % NUM_CRITICALITY_BINS
        r_bin = idx // NUM_CRITICALITY_BINS

        risk_labels = ["LOW", "MEDIUM", "HIGH"]
        crit_labels = ["LOW", "MEDIUM", "HIGH"]
        rec_labels = ["SINGLE", "BURST", "PERSISTENT"]
        conf_labels = ["UNCERTAIN", "CONFIDENT"]

        return DiscreteState(
            state_index=state_index,
            risk_bucket=risk_labels[r_bin],
            criticality_bucket=crit_labels[c_bin],
            recurrence_bucket=rec_labels[rec_bin],
            confidence_bucket=conf_labels[conf_bin],
        )
