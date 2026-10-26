"""SentinelX AI - Event and Detection Repository"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.database.models import DetectionRecord, EventRecord
from app.schemas.detections import DetectionResult
from app.schemas.events import NormalizedEvent


class EventRepository:
    """Repository handling persistence and queries for Normalized Events and Detections."""

    @staticmethod
    def save_event(db: Session, event: NormalizedEvent) -> EventRecord:
        """Persist a NormalizedEvent idempotently. If event_id already exists, return existing record."""
        existing = db.execute(
            select(EventRecord).where(EventRecord.event_id == event.event_id)
        ).scalar_one_or_none()

        if existing:
            return existing

        record = EventRecord(
            event_id=event.event_id,
            event_time=event.event_time,
            ingested_at=event.ingested_at,
            source=event.source,
            source_asset=event.source_asset,
            target_asset=event.target_asset,
            event_type=event.event_type,
            features=event.features,
            dataset_id=event.dataset_id,
            run_id=event.run_id,
            raw_label=event.raw_label,
            schema_version=event.schema_version,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def get_event(db: Session, event_id: str) -> Optional[EventRecord]:
        return db.execute(
            select(EventRecord).where(EventRecord.event_id == event_id)
        ).scalar_one_or_none()

    @staticmethod
    def list_events(
        db: Session,
        skip: int = 0,
        limit: int = 50,
        source_asset: Optional[str] = None,
        target_asset: Optional[str] = None,
    ) -> List[EventRecord]:
        stmt = select(EventRecord)
        if source_asset:
            stmt = stmt.where(EventRecord.source_asset == source_asset)
        if target_asset:
            stmt = stmt.where(EventRecord.target_asset == target_asset)
        stmt = stmt.order_by(EventRecord.event_time.desc()).offset(skip).limit(limit)
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def save_detection(db: Session, detection: DetectionResult) -> DetectionRecord:
        """Persist a Threat Detection result."""
        existing = db.execute(
            select(DetectionRecord).where(DetectionRecord.detection_id == detection.detection_id)
        ).scalar_one_or_none()

        if existing:
            return existing

        record = DetectionRecord(
            detection_id=detection.detection_id,
            event_id=detection.event_id,
            predicted_class=detection.predicted_class,
            class_scores=detection.class_scores,
            anomaly_score=detection.anomaly_score or 0.0,
            model_version=detection.model_version,
            evidence_feature_names=detection.evidence_feature_names,
            inference_duration_ms=detection.inference_duration_ms,
            calibrated=detection.calibrated,
            created_at=detection.created_at,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def get_detection(db: Session, detection_id: str) -> Optional[DetectionRecord]:
        return db.execute(
            select(DetectionRecord).where(DetectionRecord.detection_id == detection_id)
        ).scalar_one_or_none()
