# SentinelX AI --- Project Verification & Demo Guide (Phases 0 - 11)

> **Document:** `check.md`  
> **Status:** All 12 Phases (0 - 11) Complete & Tested (89/89 Tests Passing)  
> **Target Scope:** Multi-Agent Cyber Defense, RL Adaptive Response & Evaluation  

---

## 1. Executive Summary of Completed Phases

| Phase | Module Name | Implementation Summary | Primary Output / Artifact |
|---|---|---|---|
| **Phase 0** | Scope & Environment | FastAPI backend, Next.js dashboard, strict simulation safety guardrails | `/health` endpoint, `.env` |
| **Phase 1** | Domain Schemas | Pydantic contracts with strict action allowlists and UTC datetime validators | `backend/app/schemas/` |
| **Phase 2** | Data Ingestion & Adapter | CIC-IDS2017 flow normalizer, chunked CSV streaming, label segregation & quarantine gates | `backend/app/ingestion/`, sample CSV |
| **Phase 3** | Feature Engineering & Baseline ML | Leakage-free preprocessing, Random Forest classifier, feature attribution | `backend/artifacts/threat_detector_rf_v1.joblib` |
| **Phase 4** | Event & Incident Persistence | SQLAlchemy models for events, incidents, evidence, agent runs, SQLite/Postgres DB session | `backend/app/database/`, `sentinelx_fallback.db` |
| **Phase 5** | Detection Agent & Orchestrator | Base agent contract, Detection Agent wrapper, fail-safe incident state machine | `backend/app/agents/detection_agent.py`, `coordinator.py` |
| **Phase 6** | Investigation & Correlation Agent | Deterministic correlation rules (host-pair burst, port sweep), timeline clustering, evidence gap detection | `backend/app/agents/investigation_agent.py` |
| **Phase 7** | Risk Assessment Agent | Multi-factor risk formula, asset criticality weighting, MITRE ATT&CK mapping (`T1498.001`, `T1046`) | `backend/app/agents/risk_agent.py`, `services/risk_scoring.py` |
| **Phase 8** | Mitigation Planning & Safety Gate | Fixed 4-action catalogue, deterministic safety gate, analyst approval workflow, simulated action executor | `backend/app/safety/`, `simulator/action_executor.py` |
| **Phase 9** | Incident Simulator & Outcome Evaluator | 5 reproducible scenarios (DoS, Brute Force, Port Sweep, Exfiltration, Benign Burst), transition model, uncertainty | `backend/app/simulator/scenarios.py`, `environment.py` |
| **Phase 10** | Reinforcement Learning Policy | 54-state discretizer, Bellman tabular Q-learning, frozen evaluation runner, Rule/Threshold/Random baselines | `backend/app/rl/`, `backend/artifacts/q_learning_policy_v1.json` |
| **Phase 11** | REST API Integration | Role-authorized approval boundary, replay stop, simulator endpoints, experiment benchmark registry | `backend/app/main.py`, `database/repositories/experiment_repo.py` |

---

## 2. Quick Verification: Running All Unit & Integration Tests

From the project root (`SentinelX AI`):

```powershell
backend\.venv\Scripts\pytest backend\tests -v
```

Or from the `backend` directory:

```powershell
.venv\Scripts\pytest tests -v
```

**Expected Result:**
```text
======================== 89 passed, 1 warning in 5.38s ========================
```

---

## 3. Starting the Applications for Demo

### Terminal 1: Start Backend API Server

**If you are already in the `backend` directory:**
```powershell
.venv\Scripts\uvicorn app.main:app --reload --port 8000
```

**Or if you are in the project root (`SentinelX AI`):**
```powershell
backend\.venv\Scripts\uvicorn app.main:app --app-dir backend --reload --port 8000
```

- API Docs URL: **http://127.0.0.1:8000/docs**
- Health Endpoint: **http://127.0.0.1:8000/api/v1/health**

### Terminal 2: Start Frontend Analyst Dashboard

From the project root:
```powershell
cd frontend
npm run dev
```
- Dashboard URL: **http://localhost:3000**

---

## 4. End-to-End Live Workflow Test with Real Payloads

You can execute these commands in PowerShell or Bash while the backend is running.

### Step 1: Verify System Safety & Health (Phase 0)
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/health" -Method GET | ConvertTo-Json
```
**Expected Output:**
```json
{
  "status": "healthy",
  "app": "SentinelX AI",
  "environment": "development",
  "execution_mode": "simulation",
  "simulation_only": true,
  "database": {
    "status": "healthy",
    "dialect": "postgresql",
    "connected": true
  }
}
```

---

### Step 2: Trigger Offline Dataset Replay (Phase 2 & 3)
Replays 12 flows from `data/samples/cic_ids2017_sample.csv` through the ML detection model and orchestrator:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/replay/start?max_rows=12" -Method POST | ConvertTo-Json
```
**Expected Output:**
```json
{
  "status": "completed",
  "processed_events": 12,
  "incidents_created": [
    "inc-cic-0003",
    "inc-cic-0006"
  ],
  "execution_mode": "simulation"
}
```

---

### Step 3: Query Ingested Events (Phase 2 & 4)
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/events?limit=3" -Method GET | ConvertTo-Json
```
**Expected Output:**
- Returns normalized events containing canonical features: `flow_duration`, `total_fwd_packets`, `destination_port`, etc.
- Confirms `raw_label` is stored as metadata and segregated from features.

---

### Step 4: Inspect Created Security Incidents (Phase 5)
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/incidents" -Method GET | ConvertTo-Json
```
**Expected Output:**
```json
[
  {
    "incident_id": "inc-cic-0003",
    "title": "DoS-Slowloris Alert on 192.168.10.5",
    "status": "scored",
    "severity": "critical",
    "risk_score": 0.95,
    "target_asset": "192.168.10.5",
    "source_asset": "192.168.10.50"
  }
]
```

---

### Step 5: Trigger Investigation Agent & Correlation (Phase 6)
Correlates related attack bursts targeting the same host within a 10-minute time window:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/incidents/inc-cic-0003/investigate?time_window_seconds=600" -Method POST | ConvertTo-Json
```
**Expected Output:**
```json
{
  "incident_id": "inc-cic-0003",
  "status": "risk_assessed",
  "investigation_result": {
    "status": "completed",
    "summary": "Correlated 3 additional events with seed evt-cic-0003. Total linked evidence: 4 flows.",
    "structured_output": {
      "recurrence_count": 4,
      "correlation_matches": [
        {
          "event_id": "evt-cic-0004",
          "rule": "HOST_PAIR_SERVICE_BURST",
          "reason": "Temporal burst targeting identical host and service: 192.168.10.50 -> 192.168.10.5:80"
        }
      ]
    }
  }
}
```

---

### Step 6: Trigger Risk Assessment Agent (Phase 7)
Computes multi-factor risk, maps to MITRE ATT&CK technique:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/incidents/inc-cic-0003/risk" -Method POST | ConvertTo-Json
```
**Expected Output:**
```json
{
  "incident_id": "inc-cic-0003",
  "status": "response_proposed",
  "risk_score": 0.91,
  "severity": "critical",
  "mitre_technique": "T1498.001",
  "risk_result": {
    "summary": "Assessed risk score 0.91 (CRITICAL). Threat behavior attributed to MITRE ATT&CK T1498.001 (DoS-Slowloris)."
  }
}
```

---

### Step 7: Trigger Mitigation Planning Agent & Safety Gate (Phase 8)
Proposes safe, allowlisted defensive actions:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/incidents/inc-cic-0003/mitigate" -Method POST | ConvertTo-Json
```
**Expected Output:**
```json
{
  "incident_id": "inc-cic-0003",
  "status": "approval_required",
  "mitigation_result": {
    "proposed_actions": [
      "simulate_block",
      "escalate_for_approval",
      "increase_monitoring"
    ],
    "structured_output": {
      "recommended_action": "simulate_block",
      "disruption_cost": 12.0
    }
  }
}
```
*Note: Because `simulate_block` carries operational disruption, the incident safely halts in `approval_required`.*

---

### Step 8: Record Human Analyst Approval (Phase 8)
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/incidents/inc-cic-0003/approval?reviewer_id=analyst_lead&action=simulate_block&approval_status=approved&comment=Confirmed+Slowloris+flood" -Method POST | ConvertTo-Json
```
**Expected Output:**
```json
{
  "approval_id": "appr-...",
  "incident_id": "inc-cic-0003",
  "action": "simulate_block",
  "reviewer_id": "analyst_lead",
  "status": "approved",
  "comment": "Confirmed Slowloris flood"
}
```
*Incident status transitions to `simulating`.*

---

### Step 9: Execute Permitted Simulated Response (Phase 8)
Executes containment strictly within virtual simulation sandbox:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/incidents/inc-cic-0003/simulate-response?action=simulate_block" -Method POST | ConvertTo-Json
```
**Expected Output:**
```json
{
  "incident_id": "inc-cic-0003",
  "status": "outcome_recorded",
  "outcome": {
    "action": "simulate_block",
    "target_asset": "192.168.10.5",
    "containment_success": true,
    "operational_disruption_cost": 12.0,
    "reward": 86.8
  }
}
```

---

### Step 10: Inspect Append-Only Audit Trail (Phase 4 & 8)
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/audit?limit=5" -Method GET | ConvertTo-Json
```
**Expected Output:**
- Complete tamper-evident audit history showing:
  1. `INCIDENT_CREATED`
  2. `STATE_TRANSITION` (to INVESTIGATING)
  3. `STATE_TRANSITION` (to RESPONSE_PROPOSED)
  4. `STATE_TRANSITION` (to SIMULATING upon approval)
  5. `STATE_TRANSITION` (to OUTCOME_RECORDED)
- Each audit entry contains a cryptographic `verification_hash` (e.g. `sha256:7a92df44...`).

---

### Step 11: Stop Active Replay Session (Phase 11)
Halt a running dataset replay stream and record audit event:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/replay/run-demo-001/stop" -Method POST | ConvertTo-Json
```
**Expected Output:**
```json
{
  "status": "stopped",
  "run_id": "run-demo-001",
  "stopped_at": "2026-10-26T...",
  "execution_mode": "simulation"
}
```

---

### Step 12: List Reproducible Simulation Scenarios (Phase 9 & 11)
Inspect the catalog of threat and benign operational scenarios:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/simulator/scenarios" -Method GET | ConvertTo-Json
```
**Expected Output:**
- Returns all 5 reproducible scenarios:
  1. `scen-benign-burst` (High-Volume Backup Sync, ground truth: BENIGN, criticality 4)
  2. `scen-brute-force` (SSH Credential Stuffing, ground truth: BRUTE_FORCE, criticality 3)
  3. `scen-port-sweep` (Reconnaissance Port Sweep, ground truth: PORT_SCAN, criticality 2)
  4. `scen-high-ddos` (DoS Slowloris Volumetric Flood, ground truth: DOS, criticality 4)
  5. `scen-data-exfiltration` (Customer Data Store Exfiltration, ground truth: EXFILTRATION, criticality 5)

---

### Step 13: Execute Incident Simulation with RL Policy (Phase 9, 10 & 11)
Runs a full episode of a simulated threat with chosen response policy:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/simulator/run-scenario?scenario_id=scen-high-ddos&policy_type=q_learning&seed=42" -Method POST | ConvertTo-Json
```
**Expected Output:**
```json
{
  "scenario_id": "scen-high-ddos",
  "scenario_name": "High-Volume Distributed DoS / Slowloris Flood",
  "policy_used": "QLearningPolicy",
  "seed": 42,
  "total_steps": 2,
  "containment_success": true,
  "false_action": false,
  "net_reward": 53.67,
  "final_service_health": 95.8,
  "summary": "SUCCESS: Threat 'DOS' successfully contained in step 2/2. Final health: 95.8%."
}
```

---

### Step 14: Run Comparative Policy Benchmark Experiment (Phase 10 & 11)
Compares Tabular Q-Learning against Rule-Based, Threshold, and Random baselines on held-out seeds:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/experiments/run?experiment_type=rl_benchmark&episodes=20&seed=42" -Method POST | ConvertTo-Json
```
**Expected Output:**
```json
{
  "experiment_id": "exp-rl-bench-...",
  "name": "Q-Learning vs Fixed Defensive Baselines Comparison",
  "status": "completed",
  "metrics": {
    "q_mean_reward": 45.2,
    "q_containment_rate": 1.0,
    "q_false_action_rate": 0.0,
    "rule_mean_reward": 38.4,
    "threshold_mean_reward": 18.2,
    "random_mean_reward": -12.6
  }
}
```

---

### Step 15: Retrieve Experiment Detail and Metrics (Phase 10 & 11)
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/experiments" -Method GET | ConvertTo-Json
```
- Returns persisted benchmark runs with full metric dictionaries and policy comparisons.

---

## 5. Project Demo Checklist for Evaluators

- [x] **Reproducible Ingestion:** Offline replay of standard CIC-IDS2017 dataset without network dependency.
- [x] **Supervised ML Classification:** Random Forest classifier with trained feature attributions.
- [x] **Agent Orchestration:** 4 distinct specialized agents (Detection, Investigation, Risk, Mitigation) coordinated via typed schemas.
- [x] **Evidence Provenance:** Detections are linked to source event IDs and feature signals.
- [x] **Correlation & Timeline:** Deterministic grouping of repeated flows with explicit reasons and gap detection.
- [x] **Deterministic Safety Gate:** Unknown actions rejected; disruptive blocks require human analyst approval.
- [x] **Role Authorization Boundary:** Non-analysts rejected with HTTP 403 Forbidden on approval endpoints.
- [x] **Incident Simulator:** 5 canonical scenarios with transition model, uncertainty, and ground-truth isolation.
- [x] **Tabular Q-Learning Policy:** 54 discrete states, Bellman TD update, frozen evaluation, and reward weighting.
- [x] **Baseline Comparison:** Direct benchmark against Rule-Based, Threshold, and Random defensive policies.
- [x] **Experiment Persistence:** DB and JSON serialization of experiment configurations, seeds, and metrics.
- [x] **Simulation Confinement:** Defensive actions execute exclusively against simulated targets, protecting real systems.
- [x] **Auditability:** Complete append-only audit trail with SHA-256 hashes.
