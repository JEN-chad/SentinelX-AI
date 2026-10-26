"""SentinelX AI - Experiment Persistence Repository

Manages database persistence for offline ML, RL benchmarks, and comparative evaluation runs.
"""

from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session

from app.database.models import ExperimentRecord
from app.schemas.experiments import ExperimentConfig, ExperimentResult


class ExperimentRepository:
    """Data access repository for experiment benchmark records."""

    @staticmethod
    def get_experiment(db: Session, experiment_id: str) -> Optional[ExperimentRecord]:
        return db.query(ExperimentRecord).filter(ExperimentRecord.experiment_id == experiment_id).first()

    @staticmethod
    def list_experiments(
        db: Session,
        skip: int = 0,
        limit: int = 50,
        mode: Optional[str] = None,
    ) -> List[ExperimentRecord]:
        q = db.query(ExperimentRecord)
        if mode:
            q = q.filter(ExperimentRecord.mode == mode)
        return q.order_by(ExperimentRecord.started_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def save_experiment(
        db: Session,
        config: ExperimentConfig,
        result: ExperimentResult,
    ) -> ExperimentRecord:
        """Persist or update an experiment record with both configuration and measured metrics."""
        record = db.query(ExperimentRecord).filter(ExperimentRecord.experiment_id == config.experiment_id).first()
        if not record:
            record = ExperimentRecord(
                experiment_id=config.experiment_id,
                name=config.name,
                dataset_id=config.dataset_id,
                model_name=config.model_name,
                policy_name=config.policy_name,
                random_seed=config.random_seed,
                hyperparameters=config.hyperparameters,
                mode=config.mode.value if hasattr(config.mode, "value") else str(config.mode),
                status=result.status.value if hasattr(result.status, "value") else str(result.status),
                metrics=result.metrics,
                confusion_matrix=result.confusion_matrix,
                artifact_path=result.artifact_path,
                error_message=result.error_message,
                started_at=result.started_at,
                completed_at=result.completed_at,
            )
            db.add(record)
        else:
            record.name = config.name
            record.status = result.status.value if hasattr(result.status, "value") else str(result.status)
            record.metrics = result.metrics
            record.confusion_matrix = result.confusion_matrix
            record.artifact_path = result.artifact_path
            record.error_message = result.error_message
            record.completed_at = result.completed_at

        db.commit()
        db.refresh(record)
        return record
