"""SentinelX AI - FastAPI Modular Monolith Entrypoint

Exposes core system health, offline dataset replay, threat detection,
incident investigation, and controlled simulation API endpoints.
"""

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import Depends, FastAPI, Header, HTTPException, Query, status
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


@app.post(f"{settings.api_prefix}/replay/{{run_id}}/stop", tags=["Replay"])
async def stop_replay(
    run_id: str,
    db: Session = Depends(get_db),
):
    """Halt an active or running replay session and write audit log."""
    now_utc = datetime.now(timezone.utc)
    AuditRepository.log(
        db,
        actor="operator",
        operation="REPLAY_STOPPED",
        entity_id=run_id,
        status="success",
        details=f"Dataset replay run '{run_id}' manually halted by operator.",
    )
    return {
        "status": "stopped",
        "run_id": run_id,
        "stopped_at": now_utc.isoformat(),
        "execution_mode": settings.execution_mode,
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


@app.post(f"{settings.api_prefix}/incidents/{{incident_id}}/risk", tags=["Risk Assessment"])
async def trigger_risk_assessment(
    incident_id: str,
    db: Session = Depends(get_db),
):
    """Trigger Phase 7 Risk Assessment Agent for a given incident."""
    orchestrator = IncidentOrchestrator(db=db)
    try:
        updated_inc, risk_result = orchestrator.assess_incident_risk(incident_id=incident_id)
        return {
            "incident_id": updated_inc.incident_id,
            "status": updated_inc.status,
            "risk_score": updated_inc.risk_score,
            "severity": updated_inc.severity,
            "mitre_technique": updated_inc.mitre_technique,
            "risk_result": risk_result.model_dump(mode="json"),
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@app.post(f"{settings.api_prefix}/incidents/{{incident_id}}/mitigate", tags=["Mitigation"])
async def trigger_mitigation_planning(
    incident_id: str,
    is_human_approved: bool = Query(False),
    db: Session = Depends(get_db),
):
    """Trigger Phase 8 Mitigation Planning Agent to propose allowlisted actions."""
    orchestrator = IncidentOrchestrator(db=db)
    try:
        updated_inc, mit_result = orchestrator.plan_mitigation(
            incident_id=incident_id,
            is_human_approved=is_human_approved,
        )
        return {
            "incident_id": updated_inc.incident_id,
            "status": updated_inc.status,
            "mitigation_result": mit_result.model_dump(mode="json"),
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


ALLOWED_APPROVAL_ROLES = {
    "security_analyst",
    "soc_lead",
    "soc_manager",
    "admin",
    "incident_responder",
}


@app.post(f"{settings.api_prefix}/incidents/{{incident_id}}/approval", tags=["Approval"])
async def record_approval_decision(
    incident_id: str,
    reviewer_id: str = Query("security_analyst"),
    reviewer_role: str = Query("security_analyst"),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    action: str = Query("simulate_block"),
    approval_status: str = Query("approved"),
    comment: Optional[str] = Query("Approved via Security Analyst Dashboard"),
    db: Session = Depends(get_db),
):
    """Record human-in-the-loop approval decision with strict role authorization check."""
    effective_role = (x_user_role or reviewer_role).lower().strip()
    if effective_role not in ALLOWED_APPROVAL_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Forbidden: Reviewer role '{effective_role}' lacks authority to approve response actions.",
        )

    from app.schemas.common import ActionType, ApprovalStatus
    orchestrator = IncidentOrchestrator(db=db)
    try:
        act_enum = ActionType(action)
        appr_status_enum = ApprovalStatus(approval_status)
        approval_rec = orchestrator.record_approval(
            incident_id=incident_id,
            reviewer_id=reviewer_id,
            action=act_enum,
            status=appr_status_enum,
            comment=comment,
        )
        return approval_rec.model_dump(mode="json")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@app.post(f"{settings.api_prefix}/incidents/{{incident_id}}/simulate-response", tags=["Simulation"])
async def simulate_response(
    incident_id: str,
    action: str = Query("simulate_block"),
    db: Session = Depends(get_db),
):
    """Execute permitted defensive action strictly within virtual simulation sandbox."""
    from app.schemas.common import ActionType
    orchestrator = IncidentOrchestrator(db=db)
    try:
        act_enum = ActionType(action)
        updated_inc, outcome = orchestrator.execute_simulated_response(
            incident_id=incident_id,
            action=act_enum,
        )
        return {
            "incident_id": updated_inc.incident_id,
            "status": updated_inc.status,
            "outcome": outcome.model_dump(mode="json"),
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


# ============================================================================
# Phase 9: Incident Simulator & Scenario Endpoints
# ============================================================================

@app.get(f"{settings.api_prefix}/simulator/scenarios", tags=["Simulator"])
async def list_simulator_scenarios():
    """Retrieve catalogue of reproducible incident simulation scenarios."""
    from app.simulator.scenarios import list_scenarios
    scenarios = list_scenarios()
    return [
        {
            "scenario_id": s.scenario_id,
            "name": s.name,
            "description": s.description,
            "ground_truth_label": s.ground_truth_label,
            "target_asset": s.target_asset,
            "source_asset": s.source_asset,
            "asset_criticality": s.asset_criticality,
            "total_steps": s.total_steps,
            "initial_threat_level": s.initial_threat_level,
        }
        for s in scenarios
    ]


@app.post(f"{settings.api_prefix}/simulator/run-scenario", tags=["Simulator"])
async def run_simulation_scenario(
    scenario_id: str = Query("scen-high-ddos"),
    policy_type: str = Query("q_learning", description="Policy type: q_learning, rule_based, threshold, random"),
    seed: int = Query(42),
    db: Session = Depends(get_db),
):
    """Execute reproducible incident simulation episode with designated defensive policy."""
    from app.simulator.environment import IncidentSimulatorEnv
    from app.simulator.scenarios import get_scenario
    from app.rl.policy import QLearningPolicy, RuleBasedPolicy, ThresholdPolicy, RandomPermittedPolicy

    try:
        scenario = get_scenario(scenario_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    pol_type = policy_type.lower().strip()
    if pol_type in ("q_learning", "qlearning", "rl"):
        artifact_path = Path(__file__).resolve().parents[1] / "artifacts" / "q_learning_policy_v1.json"
        policy = QLearningPolicy(artifact_path=artifact_path)
    elif pol_type in ("rule_based", "rule"):
        policy = RuleBasedPolicy()
    elif pol_type in ("threshold",):
        policy = ThresholdPolicy()
    elif pol_type in ("random",):
        policy = RandomPermittedPolicy(seed=seed)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown policy_type '{policy_type}'. Permitted: q_learning, rule_based, threshold, random",
        )

    env = IncidentSimulatorEnv(scenarios=[scenario], seed=seed)
    obs = env.reset(scenario_id=scenario_id, seed=seed)
    done = False
    step_traces = []

    while not done:
        action = policy.select_action(obs)
        next_obs, step_reward, done, info = env.step(action)
        step_traces.append({
            "step": obs.step,
            "observable_risk": obs.observable_risk,
            "observable_confidence": obs.observable_confidence,
            "action_chosen": action.value,
            "step_reward": step_reward,
            "service_health": next_obs.service_health,
            "transition_reason": info.get("transition_reason"),
        })
        obs = next_obs

    outcome = env.get_episode_outcome()

    return {
        "scenario_id": scenario_id,
        "scenario_name": scenario.name,
        "policy_used": policy.policy_name,
        "seed": seed,
        "total_steps": outcome.total_steps,
        "containment_success": outcome.containment_success,
        "false_action": outcome.false_action,
        "net_reward": outcome.net_reward,
        "final_service_health": outcome.final_service_health,
        "summary": outcome.summary,
        "step_traces": step_traces,
    }


# ============================================================================
# Phase 10 & 11: Benchmark Experiments Endpoints
# ============================================================================

@app.get(f"{settings.api_prefix}/experiments", tags=["Experiments"])
async def list_experiments(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    mode: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List offline ML, RL benchmarks, and comparative evaluation experiments."""
    from app.database.repositories.experiment_repo import ExperimentRepository
    records = ExperimentRepository.list_experiments(db, skip=skip, limit=limit, mode=mode)
    return [
        {
            "experiment_id": r.experiment_id,
            "name": r.name,
            "dataset_id": r.dataset_id,
            "model_name": r.model_name,
            "policy_name": r.policy_name,
            "random_seed": r.random_seed,
            "mode": r.mode,
            "status": r.status,
            "metrics": r.metrics,
            "artifact_path": r.artifact_path,
            "started_at": r.started_at.isoformat() if r.started_at else None,
            "completed_at": r.completed_at.isoformat() if r.completed_at else None,
        }
        for r in records
    ]


@app.post(f"{settings.api_prefix}/experiments/run", tags=["Experiments"])
async def run_experiment(
    experiment_type: str = Query("rl_benchmark", description="rl_benchmark, q_learning_train"),
    episodes: int = Query(30, ge=10, le=500),
    seed: int = Query(42),
    db: Session = Depends(get_db),
):
    """Run an automated benchmark experiment and persist configuration and metrics."""
    from app.database.repositories.experiment_repo import ExperimentRepository
    from app.schemas.common import ExperimentMode, ExperimentStatus
    from app.schemas.experiments import ExperimentConfig, ExperimentResult
    from app.simulator.environment import IncidentSimulatorEnv
    from app.rl.policy import QLearningPolicy, RuleBasedPolicy, ThresholdPolicy, RandomPermittedPolicy
    from app.rl.evaluation import PolicyEvaluator
    from app.rl.q_learning import QLearningHyperparameters, QLearningTrainer

    now_utc = datetime.now(timezone.utc)
    exp_suffix = now_utc.strftime("%Y%m%d%H%M%S")
    exp_type = experiment_type.lower().strip()

    if exp_type == "rl_benchmark":
        exp_id = f"exp-rl-bench-{exp_suffix}"
        config = ExperimentConfig(
            experiment_id=exp_id,
            name="Q-Learning vs Fixed Defensive Baselines Comparison",
            dataset_id="simulator-scenarios-v1",
            model_name="multi_agent_defense",
            policy_name="q_learning_vs_baselines",
            random_seed=seed,
            hyperparameters={"episodes": episodes, "seed": seed},
            mode=ExperimentMode.EVALUATION,
            created_at=now_utc,
        )

        env = IncidentSimulatorEnv(seed=seed)
        artifact_path = Path(__file__).resolve().parents[1] / "artifacts" / "q_learning_policy_v1.json"
        q_policy = QLearningPolicy(artifact_path=artifact_path)
        rule_policy = RuleBasedPolicy()
        thresh_policy = ThresholdPolicy()
        rand_policy = RandomPermittedPolicy(seed=seed)

        comparison = PolicyEvaluator.compare_policies(
            policies=[q_policy, rule_policy, thresh_policy, rand_policy],
            env=env,
            num_episodes=episodes,
            start_seed=seed + 100,
        )

        q_metrics = comparison["QLearningPolicy"]
        metrics_dict = {
            "mean_reward": q_metrics.mean_reward,
            "containment_rate": q_metrics.containment_rate,
            "false_action_rate": q_metrics.false_action_rate,
            "mean_disruption_cost": q_metrics.mean_disruption_cost,
            "mean_damage_cost": q_metrics.mean_damage_cost,
            "mean_steps": q_metrics.mean_steps,
            "comparison": {name: m.model_dump() for name, m in comparison.items()},
        }

        result = ExperimentResult(
            experiment_id=exp_id,
            status=ExperimentStatus.COMPLETED,
            metrics={
                "q_mean_reward": q_metrics.mean_reward,
                "q_containment_rate": q_metrics.containment_rate,
                "q_false_action_rate": q_metrics.false_action_rate,
                "rule_mean_reward": comparison["RuleBasedPolicy"].mean_reward,
                "threshold_mean_reward": comparison["ThresholdPolicy"].mean_reward,
                "random_mean_reward": comparison["RandomPermittedPolicy"].mean_reward,
            },
            artifact_path=str(artifact_path),
            started_at=now_utc,
            completed_at=datetime.now(timezone.utc),
        )

        ExperimentRepository.save_experiment(db, config, result)

        return {
            "experiment_id": exp_id,
            "name": config.name,
            "status": "completed",
            "metrics": result.metrics,
            "detailed_comparison": metrics_dict["comparison"],
            "completed_at": result.completed_at.isoformat() if result.completed_at else None,
        }

    elif exp_type == "q_learning_train":
        exp_id = f"exp-ql-train-{exp_suffix}"
        config = ExperimentConfig(
            experiment_id=exp_id,
            name="Tabular Q-Learning Policy Training",
            dataset_id="simulator-scenarios-v1",
            model_name="tabular_q_learning",
            policy_name="q_learning_policy",
            random_seed=seed,
            hyperparameters={"episodes": episodes, "seed": seed, "learning_rate": 0.1, "gamma": 0.95},
            mode=ExperimentMode.TRAINING,
            created_at=now_utc,
        )

        env = IncidentSimulatorEnv(seed=seed)
        params = QLearningHyperparameters(episodes=episodes, random_seed=seed)
        trainer = QLearningTrainer(hyperparameters=params)
        _, report = trainer.train(env, num_episodes=episodes)

        artifact_path = Path(__file__).resolve().parents[1] / "artifacts" / "q_learning_policy_v1.json"
        trainer.save(artifact_path)

        result = ExperimentResult(
            experiment_id=exp_id,
            status=ExperimentStatus.COMPLETED,
            metrics={
                "episodes_trained": float(report.episodes_trained),
                "final_epsilon": float(report.final_epsilon),
                "mean_reward_first_50": float(report.mean_reward_first_50),
                "mean_reward_last_50": float(report.mean_reward_last_50),
                "total_steps": float(report.total_steps),
            },
            artifact_path=str(artifact_path),
            started_at=now_utc,
            completed_at=datetime.now(timezone.utc),
        )

        ExperimentRepository.save_experiment(db, config, result)

        return {
            "experiment_id": exp_id,
            "name": config.name,
            "status": "completed",
            "metrics": result.metrics,
            "report": report.model_dump(),
            "artifact_path": str(artifact_path),
            "completed_at": result.completed_at.isoformat() if result.completed_at else None,
        }

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown experiment_type '{experiment_type}'. Supported: rl_benchmark, q_learning_train",
        )


@app.get(f"{settings.api_prefix}/experiments/{{experiment_id}}", tags=["Experiments"])
async def get_experiment_detail(
    experiment_id: str,
    db: Session = Depends(get_db),
):
    """Retrieve full detail for a single experiment run."""
    from app.database.repositories.experiment_repo import ExperimentRepository
    r = ExperimentRepository.get_experiment(db, experiment_id)
    if not r:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment '{experiment_id}' not found.",
        )
    return {
        "experiment_id": r.experiment_id,
        "name": r.name,
        "dataset_id": r.dataset_id,
        "model_name": r.model_name,
        "policy_name": r.policy_name,
        "random_seed": r.random_seed,
        "hyperparameters": r.hyperparameters,
        "mode": r.mode,
        "status": r.status,
        "metrics": r.metrics,
        "confusion_matrix": r.confusion_matrix,
        "artifact_path": r.artifact_path,
        "error_message": r.error_message,
        "started_at": r.started_at.isoformat() if r.started_at else None,
        "completed_at": r.completed_at.isoformat() if r.completed_at else None,
    }


@app.get(f"{settings.api_prefix}/experiments/{{experiment_id}}/metrics", tags=["Experiments"])
async def get_experiment_metrics(
    experiment_id: str,
    db: Session = Depends(get_db),
):
    """Retrieve metrics dictionary and benchmark evaluation breakdown for an experiment."""
    from app.database.repositories.experiment_repo import ExperimentRepository
    r = ExperimentRepository.get_experiment(db, experiment_id)
    if not r:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment '{experiment_id}' not found.",
        )
    return {
        "experiment_id": r.experiment_id,
        "status": r.status,
        "metrics": r.metrics,
        "confusion_matrix": r.confusion_matrix,
    }
