"""SentinelX AI - Threat Detection Model Evaluation

Generates precision, recall, macro-F1, false-positive rate, and confusion matrix reports.
"""

from typing import Any, Dict, List, Sequence
import numpy as np
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support


def evaluate_classifier(
    y_true: Sequence[str],
    y_pred: Sequence[str],
    classes: Sequence[str],
) -> Dict[str, Any]:
    """Calculate evaluation metrics for multi-class threat classification."""
    classes_list = list(classes)
    prec, rec, f1, sup = precision_recall_fscore_support(
        y_true,
        y_pred,
        labels=classes_list,
        zero_division=0,
    )

    per_class = {}
    for i, cls_name in enumerate(classes_list):
        per_class[cls_name] = {
            "precision": float(round(prec[i], 4)),
            "recall": float(round(rec[i], 4)),
            "f1_score": float(round(f1[i], 4)),
            "support": int(sup[i]),
        }

    macro_f1 = float(round(np.mean(f1), 4))
    macro_prec = float(round(np.mean(prec), 4))
    macro_rec = float(round(np.mean(rec), 4))

    # Confusion Matrix
    cm = confusion_matrix(y_true, y_pred, labels=classes_list)

    # False Positive Rate on BENIGN (if present)
    fpr_benign = 0.0
    if "BENIGN" in classes_list:
        benign_idx = classes_list.index("BENIGN")
        # FP on benign is when true label is BENIGN but predicted as non-BENIGN
        fp = sum(cm[benign_idx, j] for j in range(len(classes_list)) if j != benign_idx)
        tn = cm[benign_idx, benign_idx]
        total_benign = fp + tn
        fpr_benign = float(round(fp / total_benign, 4)) if total_benign > 0 else 0.0

    return {
        "macro_f1": macro_f1,
        "macro_precision": macro_prec,
        "macro_recall": macro_rec,
        "benign_false_positive_rate": fpr_benign,
        "per_class": per_class,
        "confusion_matrix": {
            "classes": classes_list,
            "matrix": cm.tolist(),
        },
    }
