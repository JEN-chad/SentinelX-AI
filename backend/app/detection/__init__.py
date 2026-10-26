"""SentinelX AI - Threat Detection and Baseline ML Pipeline"""

from .evaluation import evaluate_classifier
from .explainability import rank_explanatory_features
from .feature_schema import CANONICAL_FEATURES, SCHEMA_VERSION, extract_feature_vector
from .inference import ThreatDetectionService
from .preprocessing import FeaturePreprocessor
from .train import train_baseline_model

__all__ = [
    "CANONICAL_FEATURES",
    "SCHEMA_VERSION",
    "extract_feature_vector",
    "FeaturePreprocessor",
    "ThreatDetectionService",
    "train_baseline_model",
    "evaluate_classifier",
    "rank_explanatory_features",
]
