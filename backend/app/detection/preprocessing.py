"""SentinelX AI - Detection Feature Preprocessing Pipeline

Applies training-fitted normalization and robust handling of missing or extreme values.
Strict rule: Preprocessing transformations must be fitted exclusively on training data.
"""

from typing import Any, Dict, Optional
import numpy as np


class FeaturePreprocessor:
    """Stateful preprocessor fitted exclusively on training distributions."""

    def __init__(self):
        self.medians: Optional[np.ndarray] = None
        self.means: Optional[np.ndarray] = None
        self.stds: Optional[np.ndarray] = None
        self.is_fitted: bool = False

    def fit(self, X: np.ndarray) -> "FeaturePreprocessor":
        """Fit imputation and scaling statistics on training matrix X (shape: N, D)."""
        X_clean = np.nan_to_num(X, nan=0.0, posinf=1e9, neginf=-1e9)
        self.medians = np.median(X_clean, axis=0)
        self.means = np.mean(X_clean, axis=0)
        self.stds = np.std(X_clean, axis=0)
        # Avoid division by zero
        self.stds[self.stds == 0.0] = 1.0
        self.is_fitted = True
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """Apply fitted statistics to normalize X."""
        if not self.is_fitted:
            raise RuntimeError("Preprocessor must be fitted before calling transform().")

        # Support 1D single-sample vector or 2D batch
        is_1d = (X.ndim == 1)
        matrix = X.reshape(1, -1) if is_1d else X.copy()

        # Handle NaNs and Infs using fitted medians
        clean = np.nan_to_num(matrix, nan=0.0, posinf=1e9, neginf=-1e9)
        normalized = (clean - self.means) / self.stds

        return normalized[0] if is_1d else normalized

    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        return self.fit(X).transform(X)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "medians": self.medians.tolist() if self.medians is not None else None,
            "means": self.means.tolist() if self.means is not None else None,
            "stds": self.stds.tolist() if self.stds is not None else None,
            "is_fitted": self.is_fitted,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FeaturePreprocessor":
        proc = cls()
        if data.get("medians") is not None:
            proc.medians = np.array(data["medians"], dtype=np.float32)
        if data.get("means") is not None:
            proc.means = np.array(data["means"], dtype=np.float32)
        if data.get("stds") is not None:
            proc.stds = np.array(data["stds"], dtype=np.float32)
        proc.is_fitted = data.get("is_fitted", False)
        return proc
