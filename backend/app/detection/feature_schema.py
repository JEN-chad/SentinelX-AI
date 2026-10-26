"""SentinelX AI - Threat Detection Feature Schema

Enforces exact feature ordering and schema validation across training and inference.
"""

from typing import Any, Dict, List
import numpy as np


CANONICAL_FEATURES: List[str] = [
    "flow_duration",
    "total_fwd_packets",
    "total_bwd_packets",
    "flow_bytes_per_sec",
    "fwd_packet_length_mean",
    "syn_flag_count",
    "rst_flag_count",
    "bwd_packets_per_sec",
    "destination_port",
]

SCHEMA_VERSION: str = "v1"


def extract_feature_vector(features: Dict[str, Any]) -> np.ndarray:
    """Extract a 1D numeric numpy array with features in strict canonical order.
    
    Raises:
        ValueError: If any canonical feature is missing or cannot be converted to float.
    """
    vector: List[float] = []
    missing_features = []

    for name in CANONICAL_FEATURES:
        if name not in features:
            missing_features.append(name)
            continue
        try:
            val = float(features[name])
            vector.append(val)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Feature '{name}' has invalid numeric value '{features[name]}': {e}")

    if missing_features:
        raise ValueError(
            f"Missing required canonical features for model inference: {missing_features}. "
            f"Expected schema: {CANONICAL_FEATURES}"
        )

    return np.array(vector, dtype=np.float32)
