"""Tests for Experiment Configuration and Results Reproducibility Schemas."""

from datetime import datetime, timedelta, timezone
import pytest
from pydantic import ValidationError
from app.schemas.common import ExperimentMode, ExperimentStatus
from app.schemas.experiments import ExperimentConfig, ExperimentResult


def test_valid_experiment_config():
    config = ExperimentConfig(
        experiment_id="exp-baseline-001",
        name="Random Forest Baseline on CIC-IDS2017",
        dataset_id="cic-ids2017-subset-v1",
        model_name="random_forest",
        policy_name="threshold_baseline",
        random_seed=42,
        hyperparameters={"n_estimators": 100, "max_depth": 15},
        mode=ExperimentMode.TRAINING,
        created_at=datetime.now(timezone.utc)
    )
    assert config.experiment_id == "exp-baseline-001"
    assert config.random_seed == 42
    assert config.mode == ExperimentMode.TRAINING


def test_completed_experiment_requires_completed_at():
    start = datetime.now(timezone.utc)
    with pytest.raises(ValidationError, match="Completed experiment must provide completed_at timestamp"):
        ExperimentResult(
            experiment_id="exp-001",
            status=ExperimentStatus.COMPLETED,
            metrics={"macro_f1": 0.94},
            started_at=start,
            completed_at=None
        )


def test_failed_experiment_requires_error_message():
    start = datetime.now(timezone.utc)
    with pytest.raises(ValidationError, match="Failed experiment must include an error_message"):
        ExperimentResult(
            experiment_id="exp-002",
            status=ExperimentStatus.FAILED,
            started_at=start,
            completed_at=start + timedelta(seconds=10),
            error_message=None
        )


def test_experiment_result_chronology():
    start = datetime.now(timezone.utc)
    with pytest.raises(ValidationError, match="completed_at cannot be earlier than started_at"):
        ExperimentResult(
            experiment_id="exp-003",
            status=ExperimentStatus.COMPLETED,
            metrics={"precision": 0.92},
            started_at=start,
            completed_at=start - timedelta(seconds=10)
        )
