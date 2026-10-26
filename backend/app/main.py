"""SentinelX AI - FastAPI Modular Monolith Entrypoint

Exposes core system health, offline dataset replay, threat detection,
incident investigation, and controlled simulation API endpoints.
"""

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .config import settings
from .database.repositories.audit_repo import AuditRepository
from .database.repositories.event_repo import EventRepository
from .database.repositories.incident_repo import IncidentRepository
from .database.session import check_db_health, get_db, init_db
from .ingestion.cic_ids2017 import CICIDS2017Adapter
from .ingestion.replay import ReplayService
from .orchestration.coordinator import IncidentOrchestrator
from .schemas.events import NormalizedEvent


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle event handler initializing database schemas on startup."""
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    description=(
        "SentinelX: A Multi-Agentic AI Framework with Autonomous Reasoning "
        "and Reinforcement-Guided Adaptive Response for Cyber Threat Detection and Mitigation"
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS configuration for frontend dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["System"])
@app.get(f"{settings.api_prefix}/health", tags=["System"])
async def health_check():
    """System health and safety boundary verification endpoint."""
    db_health = check_db_health()
    return {
        "status": "healthy" if db_health.get("connected") else "degraded",
        "app": settings.app_name,
        "environment": settings.environment,
        "execution_mode": settings.execution_mode,
        "simulation_only": settings.simulation_only,
        "database": db_health,
        "version": "0.1.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/", tags=["System"])
async def root():
    """Root info endpoint."""
    return {
        "message": f"Welcome to {settings.app_name} API",
        "health_check": f"{settings.api_prefix}/health",
        "documentation": "/docs",
    }


# ============================================================================
# Phase 2 & 11: Ingestion & Replay Endpoints
# ============================================================================

@app.get(f"{settings.api_prefix}/events", tags=["Events"])
async def list_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    source_asset: Optional[str] = None,
    target_asset: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Retrieve normalized network flow events with pagination."""
    records = EventRepository.list_events(
        db, skip=skip, limit=limit, source_asset=source_asset, target_asset=target_asset
    )
    return [
        {
            "event_id": r.event_id,
            "event_time": r.event_time.isoformat() if r.event_time else None,
            "ingested_at": r.ingested_at.isoformat() if r.ingested_at else None,
            "source": r.source,
            "source_asset": r.source_asset,
            "target_asset": r.target_asset,
            "event_type": r.event_type,
            "features": r.features,
            "dataset_id": r.dataset_id,
            "run_id": r.run_id,
            "raw_label": r.raw_label,
            "schema_version": r.schema_version,
        }
        for r in records
    ]


@app.post(f"{settings.api_prefix}/replay/start", tags=["Replay"])
async def start_replay(
    max_rows: int = Query(25, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Trigger offline dataset replay from sample CSV through Detection Agent and Orchestrator."""
    sample_path = Path(__file__).resolve().parents[2] / "data" / "samples" / "cic_ids2017_sample.csv"
    if not sample_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sample dataset not found at {sample_path}",
        )

    adapter = CICIDS2017Adapter(dataset_id="CIC-IDS2017-Friday")
    replay = ReplayService(adapter=adapter)
    orchestrator = IncidentOrchestrator(db=db)

    processed_count = 0
    incidents_created = []

    for event in replay.replay_stream(sample_path, max_rows=max_rows):
        processed_count += 1
        inc, _ = orchestrator.process_event(event)
        if inc:
            incidents_created.append(inc.incident_id)

    return {
        "status": "completed",
        "processed_events": processed_count,
        "incidents_created": list(set(incidents_created)),
        "execution_mode": settings.execution_mode,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ============================================================================
# Phase 4, 5, 6: Incidents & Investigation Endpoints
# ============================================================================

@app.get(f"{settings.api_prefix}/incidents", tags=["Incidents"])
async def list_incidents(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    severity: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List security incidents with filtering."""
    records = IncidentRepository.list_incidents(
        db, skip=skip, limit=limit, status=status_filter, severity=severity
    )
    return [
        {
            "incident_id": r.incident_id,
            "title": r.title,
            "status": r.status,
            "severity": r.severity,
            "risk_score": r.risk_score,
            "target_asset": r.target_asset,
            "source_asset": r.source_asset,
            "mitre_technique": r.mitre_technique,
            "event_ids": [l.event_id for l in r.event_links],
            "allowed_actions": r.allowed_actions,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "updated_at": r.updated_at.isoformat() if r.updated_at else None,
        }
        for r in records
    ]


@app.get(f"{settings.api_prefix}/incidents/{{incident_id}}", tags=["Incidents"])
async def get_incident_detail(
    incident_id: str,
    db: Session = Depends(get_db),
):
    """Retrieve full incident details including linked events, evidence chain, and agent execution traces."""
    r = IncidentRepository.get_incident(db, incident_id)
    if not r:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident '{incident_id}' not found.",
        )

    return {
        "incident_id": r.incident_id,
        "title": r.title,
        "status": r.status,
        "severity": r.severity,
        "risk_score": r.risk_score,
        "target_asset": r.target_asset,
        "source_asset": r.source_asset,
        "mitre_technique": r.mitre_technique,
        "event_ids": [l.event_id for l in r.event_links],
        "evidence": [
            {
                "evidence_id": ev.evidence_id,
                "event_id": ev.event_id,
                "supporting_event_ids": ev.supporting_event_ids,
                "evidence_type": ev.evidence_type,
                "is_inferred": ev.is_inferred,
                "description": ev.description,
                "confidence": ev.confidence,
                "source_component": ev.source_component,
                "metadata": ev.metadata_payload,
                "timestamp": ev.timestamp.isoformat() if ev.timestamp else None,
            }
            for ev in r.evidence
        ],
        "agent_results": [
            {
                "agent_run_id": ar.agent_run_id,
                "agent_name": ar.agent_name,
                "status": ar.status,
                "proposed_actions": ar.proposed_actions,
                "conflict_flags": ar.conflict_flags,
                "summary": ar.summary,
                "structured_output": ar.structured_output,
                "duration_ms": ar.duration_ms,
                "created_at": ar.created_at.isoformat() if ar.created_at else None,
            }
            for ar in r.agent_results
        ],
        "allowed_actions": r.allowed_actions,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "updated_at": r.updated_at.isoformat() if r.updated_at else None,
    }


@app.post(f"{settings.api_prefix}/incidents/{{incident_id}}/investigate", tags=["Investigation"])
async def trigger_investigation(
    incident_id: str,
    time_window_seconds: int = Query(600, ge=60, le=3600),
    db: Session = Depends(get_db),
):
    """Trigger Phase 6 Investigation and Correlation Agent for a given incident."""
    orchestrator = IncidentOrchestrator(db=db)
    try:
        updated_inc, inv_result = orchestrator.investigate_incident(
            incident_id=incident_id,
            time_window_seconds=time_window_seconds,
        )
        return {
            "incident_id": updated_inc.incident_id,
            "status": updated_inc.status,
            "investigation_result": inv_result.model_dump(mode="json"),
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================================
# Audit Log Endpoints
# ============================================================================

@app.get(f"{settings.api_prefix}/audit", tags=["Audit"])
async def list_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    entity_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Retrieve append-only audit trail with sha256 verification hashes."""
    records = AuditRepository.list_logs(db, skip=skip, limit=limit, entity_id=entity_id)
    return [
        {
            "audit_id": r.audit_id,
            "timestamp": r.timestamp.isoformat() if r.timestamp else None,
            "actor": r.actor,
            "operation": r.operation,
            "entity_id": r.entity_id,
            "status": r.status,
            "details": r.details,
            "verification_hash": r.verification_hash,
        }
        for r in records
    ]
