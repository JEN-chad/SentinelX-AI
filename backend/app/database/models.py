"""SentinelX AI - SQLAlchemy Database Models

Defines persistence schema for events, detections, incidents, evidence, agent runs,
response decisions, and append-only audit records.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    JSON,
)
from sqlalchemy.orm import relationship

from .base import Base


class EventRecord(Base):
    __tablename__ = "events"

    event_id = Column(String(64), primary_key=True, index=True)
    event_time = Column(DateTime(timezone=True), nullable=False, index=True)
    ingested_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    source = Column(String(64), nullable=False, index=True)
    source_asset = Column(String(128), nullable=False, index=True)
    target_asset = Column(String(128), nullable=False, index=True)
    event_type = Column(String(64), nullable=False, index=True)
    features = Column(JSON, nullable=False, default=dict)
    dataset_id = Column(String(64), nullable=True, index=True)
    run_id = Column(String(64), nullable=True, index=True)
    raw_label = Column(String(64), nullable=True)
    schema_version = Column(String(16), nullable=False, default="v1")

    # Relationships
    detections = relationship("DetectionRecord", back_populates="event", cascade="all, delete-orphan")
    incident_links = relationship("IncidentEventLink", back_populates="event", cascade="all, delete-orphan")


class DetectionRecord(Base):
    __tablename__ = "detections"

    detection_id = Column(String(64), primary_key=True, index=True)
    event_id = Column(String(64), ForeignKey("events.event_id", ondelete="CASCADE"), nullable=False, index=True)
    predicted_class = Column(String(64), nullable=False, index=True)
    class_scores = Column(JSON, nullable=False, default=dict)
    anomaly_score = Column(Float, nullable=False, default=0.0)
    model_version = Column(String(64), nullable=False)
    evidence_feature_names = Column(JSON, nullable=False, default=list)
    inference_duration_ms = Column(Float, nullable=True)
    calibrated = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    event = relationship("EventRecord", back_populates="detections")


class IncidentRecord(Base):
    __tablename__ = "incidents"

    incident_id = Column(String(64), primary_key=True, index=True)
    title = Column(String(150), nullable=False)
    status = Column(String(32), nullable=False, default="received", index=True)
    severity = Column(String(16), nullable=False, default="low", index=True)
    risk_score = Column(Float, nullable=False, default=0.0, index=True)
    target_asset = Column(String(128), nullable=True, index=True)
    source_asset = Column(String(128), nullable=True, index=True)
    mitre_technique = Column(String(32), nullable=True)
    allowed_actions = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    schema_version = Column(String(16), nullable=False, default="v1")

    # Relationships
    event_links = relationship("IncidentEventLink", back_populates="incident", cascade="all, delete-orphan")
    evidence = relationship("EvidenceRecord", back_populates="incident", cascade="all, delete-orphan")
    agent_results = relationship("AgentRunRecord", back_populates="incident", cascade="all, delete-orphan")
    decisions = relationship("ResponseDecisionRecord", back_populates="incident", cascade="all, delete-orphan")


class IncidentEventLink(Base):
    __tablename__ = "incident_event_links"

    id = Column(Integer, primary_key=True, autoincrement=True)
    incident_id = Column(String(64), ForeignKey("incidents.incident_id", ondelete="CASCADE"), nullable=False, index=True)
    event_id = Column(String(64), ForeignKey("events.event_id", ondelete="CASCADE"), nullable=False, index=True)
    association_reason = Column(String(255), nullable=False, default="primary_detection")
    linked_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    incident = relationship("IncidentRecord", back_populates="event_links")
    event = relationship("EventRecord", back_populates="incident_links")


class EvidenceRecord(Base):
    __tablename__ = "evidence"

    evidence_id = Column(String(64), primary_key=True, index=True)
    incident_id = Column(String(64), ForeignKey("incidents.incident_id", ondelete="CASCADE"), nullable=False, index=True)
    event_id = Column(String(64), nullable=True, index=True)
    supporting_event_ids = Column(JSON, nullable=False, default=list)
    evidence_type = Column(String(32), nullable=False, index=True)
    is_inferred = Column(Boolean, nullable=False, default=False)
    description = Column(Text, nullable=False)
    confidence = Column(Float, nullable=False, default=1.0)
    source_component = Column(String(64), nullable=False)
    metadata_payload = Column(JSON, nullable=False, default=dict)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    incident = relationship("IncidentRecord", back_populates="evidence")


class AgentRunRecord(Base):
    __tablename__ = "agent_runs"

    agent_run_id = Column(String(64), primary_key=True, index=True)
    agent_name = Column(String(64), nullable=False, index=True)
    incident_id = Column(String(64), ForeignKey("incidents.incident_id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(32), nullable=False, default="completed")
    proposed_actions = Column(JSON, nullable=False, default=list)
    conflict_flags = Column(JSON, nullable=False, default=list)
    summary = Column(Text, nullable=False)
    structured_output = Column(JSON, nullable=False, default=dict)
    duration_ms = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    incident = relationship("IncidentRecord", back_populates="agent_results")


class ResponseDecisionRecord(Base):
    __tablename__ = "response_decisions"

    decision_id = Column(String(64), primary_key=True, index=True)
    incident_id = Column(String(64), ForeignKey("incidents.incident_id", ondelete="CASCADE"), nullable=False, index=True)
    policy_version = Column(String(64), nullable=False)
    proposed_action = Column(String(64), nullable=False)
    safety_result = Column(String(32), nullable=False)
    reason_codes = Column(JSON, nullable=False, default=list)
    evidence_event_ids = Column(JSON, nullable=False, default=list)
    execution_mode = Column(String(32), nullable=False, default="simulation")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    incident = relationship("IncidentRecord", back_populates="decisions")


class AuditLogRecord(Base):
    __tablename__ = "audit_logs"

    audit_id = Column(String(64), primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    actor = Column(String(64), nullable=False, index=True)
    operation = Column(String(64), nullable=False, index=True)
    entity_id = Column(String(64), nullable=False, index=True)
    status = Column(String(32), nullable=False)
    details = Column(Text, nullable=False)
    verification_hash = Column(String(128), nullable=False)


# Compound indices for common query patterns
Index("idx_events_source_target_time", EventRecord.source_asset, EventRecord.target_asset, EventRecord.event_time)
Index("idx_incidents_status_severity", IncidentRecord.status, IncidentRecord.severity)
