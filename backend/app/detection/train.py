"""SentinelX AI - Threat Detection Model Training Pipeline

Trains a reproducible Random Forest baseline classifier on flow datasets.
Enforces that preprocessing is fitted strictly on the training set with no test leakage.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union
import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

from app.ingestion.cic_ids2017 import CICIDS2017Adapter
from app.ingestion.replay import ReplayService
from .evaluation import evaluate_classifier
from .feature_schema import CANONICAL_FEATURES, extract_feature_vector
from .preprocessing import FeaturePreprocessor


ARTIFACT_DIR = Path(__file__).resolve().parents[2] / "artifacts"
DEFAULT_ARTIFACT_PATH = ARTIFACT_DIR / "threat_detector_rf_v1.joblib"
SAMPLE_CSV_PATH = Path(__file__).resolve().parents[3] / "data" / "samples" / "cic_ids2017_sample.csv"


def prepare_dataset_from_csv(csv_path: Union[str, Path]) -> Tuple[np.ndarray, np.ndarray]:
    """Ingest dataset through adapter and extract feature matrix X and target labels y."""
    adapter = CICIDS2017Adapter()
    replay = ReplayService(adapter=adapter)
    batch = replay.process_file(csv_path)

    X_list = []
    y_list = []

    for event in batch.valid_events:
        vec = extract_feature_vector(event.features)
        X_list.append(vec)
        y_list.append(event.raw_label or "BENIGN")

    return np.array(X_list, dtype=np.float32), np.array(y_list)


def train_baseline_model(
    csv_path: Optional[Union[str, Path]] = None,
    output_path: Optional[Union[str, Path]] = None,
    random_state: int = 42,
) -> Dict[str, Any]:
    """Train Random Forest baseline classifier, fit preprocessor on train only, evaluate, and save artifact."""
    source_csv = Path(csv_path or SAMPLE_CSV_PATH)
    if not source_csv.exists():
        raise FileNotFoundError(f"Source dataset not found at {source_csv}")

    dest_artifact = Path(output_path or DEFAULT_ARTIFACT_PATH)
    dest_artifact.parent.mkdir(parents=True, exist_ok=True)

    X, y = prepare_dataset_from_csv(source_csv)

    # Train / Test split (stratified by attack label if possible)
    stratify = y if len(np.unique(y)) > 1 and all(count > 1 for count in np.bincount(np.unique(y, return_inverse=True)[1])) else None
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=random_state, stratify=stratify
    )

    # STRICT RULE: Fit preprocessor ONLY on training data!
    preprocessor = FeaturePreprocessor()
    X_train_norm = preprocessor.fit_transform(X_train)
    X_test_norm = preprocessor.transform(X_test)

    # Train Random Forest baseline
    rf = RandomForestClassifier(
        n_estimators=30,
        max_depth=6,
        random_state=random_state,
        class_weight="balanced",
    )
    rf.fit(X_train_norm, y_train)

    # Evaluate on held-out test data
    y_pred = rf.predict(X_test_norm)
    metrics = evaluate_classifier(y_test, y_pred, classes=rf.classes_)

    bundle = {
        "model": rf,
        "preprocessor": preprocessor,
        "feature_names": CANONICAL_FEATURES,
        "classes": list(rf.classes_),
        "model_version": "rf-baseline-v1.0.0",
        "feature_importances": [float(val) for val in rf.feature_importances_],
        "metrics": metrics,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "training_samples": len(X_train),
        "test_samples": len(X_test),
    }

    joblib.dump(bundle, dest_artifact)
    return bundle


if __name__ == "__main__":
    train_baseline_model()
