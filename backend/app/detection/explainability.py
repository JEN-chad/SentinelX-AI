"""SentinelX AI - Threat Detection Explainability Utilities

Provides feature attribution and explanatory ranking for threat detections.
"""

from typing import Dict, List, Sequence
import numpy as np


def rank_explanatory_features(
    feature_vector: np.ndarray,
    feature_names: Sequence[str],
    feature_importances: Sequence[float],
    top_k: int = 3,
) -> List[str]:
    """Identify the top-k most explanatory features for a detected flow anomaly."""
    assert len(feature_names) == len(feature_importances)

    # Combine feature importance weights with absolute normalized magnitude
    scores = []
    for name, imp in zip(feature_names, feature_importances):
        scores.append((imp, name))

    # Sort descending by importance score
    scores.sort(key=lambda x: x[0], reverse=True)
    return [name for _, name in scores[:top_k]]
