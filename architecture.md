# SentinelX AI --- Project Architecture

> **Project title:** SentinelX: A Multi-Agentic AI Framework with
> Autonomous Reasoning and Reinforcement-Guided Adaptive Response for
> Cyber Threat Detection and Mitigation\
> **Project type:** Final-year B.Tech AI & Data Science project\
> **Architecture status:** Proposed implementation architecture\
> **Primary operating mode:** Offline dataset replay and controlled
> simulation

------------------------------------------------------------------------

## 1. Project Overview

SentinelX AI is a research-oriented cyber defense prototype that
combines machine-learning-based threat detection, multi-agent incident
investigation, risk assessment, and reinforcement-learning-guided
defensive response selection.

The system ingests labeled network-flow data or simulated security
events, normalizes them, detects suspicious activity, correlates related
evidence, assesses risk, and selects a permitted response. A web
dashboard presents incidents, evidence, decisions, and experimental
metrics.

The initial version must operate in **offline replay and simulation
mode**. It must not connect experimental policies to production
firewalls, real endpoints, or third-party systems.

### Primary objectives

1.  Detect malicious or anomalous network activity using reproducible ML
    models.
2.  Coordinate specialized agents through typed messages and a shared
    incident record.
3.  Explain detections and response recommendations using traceable
    evidence.
4.  Train and evaluate a reinforcement-learning policy for response
    selection in a simulator.
5.  Compare the proposed system with single-model, rule-based, and
    non-adaptive baselines.
6.  Provide a full-stack dashboard, persistent incident history, and an
    audit trail.

### Research hypothesis

A coordinated agent workflow with a reinforcement-guided response policy
may improve the trade-off between simulated threat containment and
operational disruption compared with fixed response rules. This is a
hypothesis to test, not a result to assume.

------------------------------------------------------------------------

## 2. Scope and Non-Goals

### In scope

-   Offline network-flow dataset ingestion and replay.
-   Data validation, preprocessing, feature engineering, and ML
    inference.
-   Anomaly scoring and supervised threat classification.
-   Multi-agent investigation, correlation, risk assessment, and
    mitigation planning.
-   Q-learning for a discrete set of simulated defensive actions.
-   Simulated outcomes, reward tracking, and policy evaluation.
-   Human approval gates, action allowlists, rollback state, and audit
    records.
-   A React-based dashboard and FastAPI backend.

### Out of scope for the first release

-   Autonomous changes to production network controls.
-   Offensive actions against real systems.
-   Unsupervised execution of shell commands or arbitrary
    agent-generated tools.
-   Treating LLM output as authoritative evidence or permission to act.
-   Claims of production-grade protection without independent security
    testing.

------------------------------------------------------------------------

## 3. High-Level Architecture

``` mermaid
flowchart TD
    A[Dataset Files / Simulated Events] --> B[Ingestion and Validation]
    B --> C[Normalization and Feature Engineering]
    C --> D[Threat Detection Service]
    D --> E[Incident Orchestrator]

    E --> F[Detection Agent]
    E --> G[Investigation and Correlation Agent]
    E --> H[Risk Assessment Agent]
    E --> I[Mitigation Planning Agent]

    F --> J[Shared Incident State]
    G --> J
    H --> J
    I --> J

    J --> K[Policy and Safety Gate]
    K --> L[Reinforcement Learning Policy]
    L --> M[Action Allowlist Validator]
    M --> N[Simulation / Approval Workflow]

    N --> O[Outcome Evaluator]
    O --> P[Reward and Episode Store]
    P --> L

    E --> Q[PostgreSQL]
    N --> Q
    O --> Q
    Q --> R[FastAPI REST / WebSocket API]
    R --> S[Next.js Dashboard]
```

### Architectural principles

-   **Separation of concerns:** Detection, investigation, policy
    learning, simulation, API, and presentation are independent modules.
-   **Typed contracts:** Agents exchange validated Pydantic models, not
    unrestricted natural-language messages.
-   **Evidence provenance:** Every important claim points to event IDs,
    timestamps, model versions, or derived features.
-   **Deterministic safety controls:** The safety layer is independent
    of the LLM and RL policy.
-   **Reproducibility:** Dataset versions, model versions, policy
    parameters, random seeds, and experiment settings are recorded.
-   **Fail-safe behavior:** If the model, orchestrator, or policy fails,
    no mitigation action is executed; the system records an error and
    raises an alert.

------------------------------------------------------------------------

## 4. Core Components

### 4.1 Data Ingestion Service

**Responsibilities** - Read approved CSV network-flow datasets and
simulator-generated events. - Validate required columns, types, ranges,
timestamps, and missing values. - Attach a unique event ID, source,
ingestion time, and dataset/run identifier. - Reject malformed rows or
route them to a quarantine/error log. - Support deterministic batch
replay for experiments.

**Inputs** - CIC-IDS2017 or UNSW-NB15-derived flow records. - JSON
events generated by the local simulator.

**Outputs** - Validated normalized event records. - Data quality
statistics and ingestion errors.

**Important design note:** Dataset-specific labels and fields must be
mapped to a common internal schema. Never assume that different datasets
use identical features or label definitions.

### 4.2 Preprocessing and Feature Engineering

**Responsibilities** - Apply training-fitted transformations to
inference data. - Handle missing and invalid values. - Encode
categorical fields where needed. - Select and order features exactly as
expected by the trained model. - Track preprocessing and model versions.

**Controls** - Fit preprocessing only on training data. - Prevent
target-label leakage. - Avoid fitting scalers or encoders on test
data. - Split data by time, host, capture, or another defensible
grouping when possible to reduce leakage from correlated flows.

### 4.3 Threat Detection Service

**Initial models** - Baseline: Random Forest. - Comparison: XGBoost, if
available and appropriate. - Optional anomaly detector: Isolation
Forest.

**Output fields** - Predicted class. - Class probabilities or a clearly
documented confidence measure. - Anomaly score, when available. - Model
and preprocessing version. - Top explanatory features, if supported. -
Inference timestamp and processing duration.

A probability from a classifier is not automatically a calibrated
probability of real-world compromise. Evaluate calibration if confidence
values influence decisions.

### 4.4 Agent Orchestrator

The orchestrator manages agent execution, state transitions, validation,
timeouts, and retries.

**Responsibilities** - Create and update an incident record. - Dispatch
validated tasks to specialized agents. - Store each agent's result and
evidence references. - Detect missing, invalid, or contradictory
outputs. - Apply timeouts and bounded retries. - Pass a validated state
to the response policy. - Record the full decision sequence.

The orchestrator, rather than individual agents, owns the incident
lifecycle and controls which components can be called.

### 4.5 Specialized Agents

#### Agent A --- Detection Agent

-   Consumes model predictions and anomaly scores.
-   Creates or updates a candidate alert.
-   Attaches model version and supporting event references.
-   Does not execute mitigations.

#### Agent B --- Investigation and Correlation Agent

-   Groups related events using source/target identifiers, timestamps,
    and behavior.
-   Builds an incident timeline.
-   Counts repeated events and records correlation rules.
-   Marks missing or conflicting evidence explicitly.
-   Avoids claiming an attack path unless supported by evidence.

#### Agent C --- Risk Assessment Agent

-   Combines detection confidence, correlated evidence, asset
    criticality, and potential impact.
-   Produces a documented severity score and priority.
-   Separates observed facts from inferred conclusions.
-   May map supported behavior to MITRE ATT&CK techniques, with evidence
    and uncertainty recorded.

#### Agent D --- Mitigation Planning Agent

-   Proposes actions from a fixed action catalogue.
-   Estimates expected benefit, potential disruption, reversibility, and
    required approval.
-   Provides a concise rationale linked to evidence.
-   Cannot add new action types or execute arbitrary tools.

#### Agent E --- Adaptive Learning / RL Policy Component

-   Observes a validated, discretized state.
-   Selects from permitted actions using the current policy.
-   Receives outcomes only from the controlled simulator or approved
    evaluation harness.
-   Updates policy parameters in training mode.
-   Uses a frozen policy in evaluation mode.
-   Does not control the safety rules, action allowlist, or reward
    definition at runtime.

The RL component is a policy module rather than an unrestricted
autonomous agent. Its actions are always checked by the deterministic
safety gate.

------------------------------------------------------------------------

## 5. Incident Lifecycle

``` mermaid
stateDiagram-v2
    [*] --> Received
    Received --> Validated
    Received --> Rejected: Invalid event
    Validated --> Scored
    Scored --> Investigating
    Investigating --> RiskAssessed
    RiskAssessed --> ResponseProposed
    ResponseProposed --> SafetyCheck
    SafetyCheck --> Simulating: Action permitted
    SafetyCheck --> ApprovalRequired: Human approval needed
    SafetyCheck --> AlertOnly: Action rejected or policy unavailable
    ApprovalRequired --> Simulating: Approved in test workflow
    ApprovalRequired --> AlertOnly: Rejected or expired
    Simulating --> OutcomeRecorded
    AlertOnly --> OutcomeRecorded
    OutcomeRecorded --> Closed
    Rejected --> Closed
    Closed --> [*]
```

### Suggested incident states

-   `received`
-   `validated`
-   `scored`
-   `investigating`
-   `risk_assessed`
-   `response_proposed`
-   `approval_required`
-   `simulating`
-   `outcome_recorded`
-   `closed`
-   `rejected`
-   `error`

Each transition should be validated by the backend. Clients and agents
must not be able to set arbitrary incident states.

------------------------------------------------------------------------

## 6. Shared Data Contracts

Use Pydantic schemas to validate all messages between services.

### Normalized event

``` json
{
  "event_id": "evt-demo-0001",
  "event_time": "2026-01-01T10:00:00Z",
  "ingested_at": "2026-01-01T10:00:01Z",
  "source": "dataset_replay",
  "source_asset": "sim-host-07",
  "target_asset": "sim-server-02",
  "event_type": "repeated_login_failures",
  "features": {},
  "dataset_id": "demo-dataset-v1",
  "run_id": "run-demo-001"
}
```

### Detection result

``` json
{
  "event_id": "evt-demo-0001",
  "predicted_class": "suspicious",
  "class_scores": {
    "benign": 0.06,
    "suspicious": 0.94
  },
  "anomaly_score": 0.88,
  "model_version": "rf-v1",
  "evidence_feature_names": ["example_feature_a", "example_feature_b"]
}
```

The values above are illustrative placeholders, not benchmark results.

### Incident state

``` json
{
  "incident_id": "inc-demo-0001",
  "status": "investigating",
  "event_ids": ["evt-demo-0001"],
  "severity": "high",
  "risk_score": 0.82,
  "evidence": [],
  "agent_results": [],
  "allowed_actions": [
    "raise_alert",
    "increase_monitoring",
    "request_approval",
    "simulate_block"
  ],
  "created_at": "2026-01-01T10:00:02Z",
  "updated_at": "2026-01-01T10:00:03Z"
}
```

### Response decision

``` json
{
  "decision_id": "dec-demo-0001",
  "incident_id": "inc-demo-0001",
  "policy_version": "qtable-v1",
  "proposed_action": "simulate_block",
  "safety_result": "requires_approval",
  "reason_codes": ["HIGH_RISK", "CORRELATED_EVENTS"],
  "evidence_event_ids": ["evt-demo-0001"],
  "execution_mode": "simulation"
}
```

------------------------------------------------------------------------

## 7. Reinforcement Learning Design

### 7.1 Formulation

Model response selection as a discrete Markov Decision Process (MDP).

**State (`s`)** --- Begin with a small, interpretable feature set: -
Threat score bucket: low, medium, high. - Evidence confidence bucket:
low, medium, high. - Asset criticality: low, medium, high. - Correlated
event count bucket. - Previous response outcome. - Incident recurrence
indicator.

Discretization makes tabular Q-learning practical for a student
prototype. Document how each continuous input is bucketed and test
whether conclusions are sensitive to these choices.

**Action (`a`)** --- A fixed catalogue: - `raise_alert` -
`increase_monitoring` - `escalate_for_approval` - `simulate_block`

**Transition (`s'`)** --- The simulator updates the scenario state after
a selected action. Transition probabilities and assumptions must be
documented. The simulator should include both successful and
unsuccessful response outcomes.

**Reward (`r`)** --- A candidate objective is:

`reward = containment_benefit - false_action_cost - disruption_cost - response_delay_cost`

Choose and justify the numeric weights before final evaluation. Run
sensitivity analysis with alternative weights to identify
reward-function dependence.

### 7.2 Q-learning update

`Q(s, a) = Q(s, a) + alpha * [r + gamma * max_a_prime Q(s_prime, a_prime) - Q(s, a)]`

Where: - `alpha` is the learning rate. - `gamma` is the discount
factor. - `r` is the immediate simulated reward. - `s_prime` is the next
state.

### 7.3 Training and evaluation separation

**Training mode** - Uses simulated episodes only. - Enables exploration,
such as epsilon-greedy action selection. - Updates the Q-table. - Logs
seeds, reward configuration, episode outcomes, and policy version.

**Evaluation mode** - Loads a frozen policy. - Disables learning and
exploratory actions unless the experiment explicitly tests
exploration. - Uses held-out scenarios and multiple random seeds. -
Compares the same scenario seeds across policies where practical.

### 7.4 Baselines

Compare at least: 1. Fixed rule-based response. 2. Simple
threshold-based response. 3. Random permitted-action baseline, as a
lower-bound reference. 4. Q-learning policy.

### 7.5 Metrics

-   Mean cumulative reward and variation across seeds.
-   Simulated containment rate.
-   Unnecessary response rate.
-   Disruption cost.
-   Time to simulated mitigation.
-   Action distribution.
-   Performance under changed scenario mixes.
-   Inference and policy-decision latency.

Do not use reward alone as evidence of improved security. Report the
individual outcome metrics and disclose simulator limitations.

------------------------------------------------------------------------

## 8. Safety and Trust Boundaries

The safety layer must be deterministic, independently testable, and
outside the control of agents and the RL learner.

### Mandatory controls

1.  **Simulation-only execution:** Every action targets a simulator
    object, not a real IP address, firewall, or endpoint.
2.  **Action allowlist:** Reject any action not defined in the
    server-side catalogue.
3.  **Human approval:** Require explicit approval for consequential
    actions in any future integration mode.
4.  **No arbitrary code execution:** Agents cannot run shell commands,
    generate executable scripts, or call arbitrary tools.
5.  **Evidence validation:** Validate event references and ensure
    explanations do not cite nonexistent evidence.
6.  **Policy isolation:** The RL policy cannot change permissions,
    action definitions, or safety checks.
7.  **Fail-safe defaults:** If dependencies fail or output validation
    fails, alert and record the failure; do not execute a mitigation.
8.  **Audit logging:** Record actor/component, action proposal, policy
    version, approval decision, simulator outcome, and timestamp.
9.  **Dataset and model provenance:** Store dataset version,
    preprocessing version, model hash/version, and experiment
    configuration.
10. **Input sanitization:** Treat event fields, log messages, and any
    LLM-provided text as untrusted data.

### LLM usage

An LLM may summarize evidence or convert structured findings into
analyst-friendly explanations. It must not invent evidence, override the
risk policy, grant permissions, or directly execute a response. Prefer
deterministic rules and validated schemas for operational decisions.

------------------------------------------------------------------------

## 9. Backend API Design

Prefix endpoints with `/api/v1`.

  ----------------------------------------------------------------------------------------------
  Method                  Endpoint                                       Purpose
  ----------------------- ---------------------------------------------- -----------------------
  `GET`                   `/health`                                      Health check

  `POST`                  `/events/ingest`                               Ingest a validated
                                                                         event or approved batch

  `GET`                   `/events`                                      Filter and paginate
                                                                         events

  `POST`                  `/replay/start`                                Start an offline replay
                                                                         run

  `POST`                  `/replay/{run_id}/stop`                        Stop a replay run

  `GET`                   `/incidents`                                   List incidents with
                                                                         filters

  `GET`                   `/incidents/{incident_id}`                     Read incident details
                                                                         and evidence

  `POST`                  `/incidents/{incident_id}/investigate`         Trigger/retry
                                                                         investigation

  `POST`                  `/incidents/{incident_id}/simulate-response`   Run a permitted
                                                                         simulated action

  `POST`                  `/incidents/{incident_id}/approval`            Record an authorized
                                                                         approval decision

  `GET`                   `/experiments`                                 List experiment runs

  `POST`                  `/experiments`                                 Start a configured
                                                                         training/evaluation
                                                                         experiment

  `GET`                   `/experiments/{run_id}/metrics`                Fetch experiment
                                                                         metrics

  `GET`                   `/audit`                                       Query audit records

  `WS`                    `/ws/events`                                   Stream event and
                                                                         incident updates
  ----------------------------------------------------------------------------------------------

Add authentication and role checks before exposing any approval or
experiment-control endpoints beyond a local development environment. Use
pagination and request-size limits for batch endpoints.

------------------------------------------------------------------------

## 10. Database Design

Use PostgreSQL for persistent application state. Keep large raw datasets
and trained model artifacts in a separate local data/artifact directory
rather than storing them as database blobs.

### Core tables

  -----------------------------------------------------------------------
  Table                   Key fields              Purpose
  ----------------------- ----------------------- -----------------------
  `dataset_runs`          `id`, `dataset_name`,   Track dataset ingestion
                          `version`,              and replay
                          `started_at`, `status`  

  `events`                `id`, `event_time`,     Store normalized events
                          `source`, `payload`,    
                          `run_id`                

  `detections`            `id`, `event_id`,       Store model output
                          `model_version`,        
                          `predicted_class`,      
                          `scores`                

  `incidents`             `id`, `status`,         Incident lifecycle
                          `severity`,             
                          `risk_score`,           
                          timestamps              

  `incident_events`       `incident_id`,          Link evidence to
                          `event_id`,             incidents
                          `relation_type`         

  `agent_runs`            `id`, `incident_id`,    Trace agent execution
                          `agent_name`, `status`, 
                          `output`, duration      

  `response_decisions`    `id`, `incident_id`,    Record proposals and
                          `action`,               decisions
                          `policy_version`,       
                          `safety_result`         

  `approval_records`      `id`, `decision_id`,    Record human approval
                          `reviewer_id`,          
                          `decision`, `timestamp` 

  `simulation_outcomes`   `id`, `decision_id`,    Record simulated
                          `outcome`, `reward`,    results
                          `episode_id`            

  `rl_policy_versions`    `id`, `parameters`,     Version trained
                          `artifact_path`,        policies
                          `created_at`            

  `experiment_runs`       `id`, `config`, `seed`, Reproduce experiments
                          `metrics`, `status`     

  `audit_logs`            `id`, `actor`,          Append-only audit
                          `operation`,            history
                          `entity_id`, `details`, 
                          `timestamp`             
  -----------------------------------------------------------------------

### Database notes

-   Use UUIDs or another consistent identifier strategy.
-   Add indexes for event time, incident status, severity, run ID, and
    foreign keys.
-   Use JSONB for flexible model/agent metadata, but keep frequently
    queried fields in typed columns.
-   Enforce foreign keys and reasonable payload limits.
-   Store UTC timestamps.
-   Avoid placing secrets, credentials, or unnecessary personal data in
    event payloads.
-   Restrict update/delete access to audit records; application logic
    should append rather than rewrite history.

------------------------------------------------------------------------

## 11. Frontend Architecture

**Stack:** Next.js, React, TypeScript, Tailwind CSS, and a charting
library such as Recharts.

### Main pages

1.  **Overview**
    -   Total events and incidents.
    -   Severity distribution.
    -   Detection trends and simulated response metrics.
    -   Current replay/experiment status.
2.  **Event Explorer**
    -   Search, filters, timestamps, source and target.
    -   Predicted class, score, model version, and feature explanation.
3.  **Incident Detail**
    -   Incident timeline.
    -   Linked event evidence.
    -   Agent findings and disagreements.
    -   Risk assessment and response rationale.
    -   Approval and simulation history.
4.  **Adaptive Response Lab**
    -   Training reward curve.
    -   Baseline comparisons.
    -   Action distribution and disruption metrics.
    -   Scenario and policy-version selection.
5.  **Experiments**
    -   Dataset/model/policy configuration.
    -   Random seed and run status.
    -   Metrics and exportable results.
6.  **Audit Log**
    -   Filterable sequence of proposals, validation results, approvals,
        and outcomes.

### Frontend rules

-   Treat backend responses as untrusted and validate expected shapes.
-   Display model confidence and risk score as different concepts.
-   Distinguish proposed, approved, simulated, and executed states.
-   Never imply a real block occurred when only a simulation ran.
-   Do not store secrets in browser code.

------------------------------------------------------------------------

## 12. Repository Structure

``` text
sentinelx-ai/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── events.py
│   │   │   ├── incidents.py
│   │   │   ├── replay.py
│   │   │   ├── experiments.py
│   │   │   └── audit.py
│   │   ├── agents/
│   │   │   ├── detection_agent.py
│   │   │   ├── investigation_agent.py
│   │   │   ├── risk_agent.py
│   │   │   └── mitigation_agent.py
│   │   ├── orchestration/
│   │   │   ├── coordinator.py
│   │   │   ├── state_machine.py
│   │   │   └── schemas.py
│   │   ├── detection/
│   │   │   ├── preprocessing.py
│   │   │   ├── train.py
│   │   │   ├── inference.py
│   │   │   └── explainability.py
│   │   ├── rl/
│   │   │   ├── state_encoder.py
│   │   │   ├── environment.py
│   │   │   ├── q_learning.py
│   │   │   └── evaluation.py
│   │   ├── simulator/
│   │   │   ├── scenarios.py
│   │   │   ├── transition_model.py
│   │   │   └── outcome_evaluator.py
│   │   ├── safety/
│   │   │   ├── action_catalogue.py
│   │   │   ├── policy_gate.py
│   │   │   └── approval.py
│   │   ├── database/
│   │   │   ├── models.py
│   │   │   ├── session.py
│   │   │   └── repositories.py
│   │   ├── services/
│   │   ├── config.py
│   │   └── main.py
│   ├── migrations/
│   ├── tests/
│   ├── artifacts/             # Local model/policy artifacts; not committed
│   └── requirements.txt
├── frontend/
│   ├── app/
│   ├── components/
│   ├── hooks/
│   ├── lib/
│   └── package.json
├── data/
│   ├── raw/                   # Downloaded datasets; not committed
│   ├── processed/             # Generated locally; not committed
│   └── README.md
├── experiments/
│   ├── configs/
│   ├── results/
│   └── README.md
├── docs/
│   ├── architecture.md
│   ├── api.md
│   ├── experiments.md
│   └── threat-model.md
├── tests/
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

This is a target structure; directories should be introduced as the
corresponding features are implemented rather than created as empty
placeholders all at once.

------------------------------------------------------------------------

## 13. Suggested Development Milestones

### Milestone 1 --- Data and baseline detection

-   Load one dataset.
-   Validate and preprocess features.
-   Train a Random Forest baseline.
-   Produce a confusion matrix and per-class metrics.
-   Expose inference through FastAPI.

### Milestone 2 --- Incident pipeline

-   Create normalized event and incident schemas.
-   Implement incident state transitions.
-   Add the detection, investigation, risk, and mitigation agents.
-   Persist evidence and agent results.

### Milestone 3 --- Simulator and RL

-   Define discrete states and permitted actions.
-   Implement simulated state transitions and reward calculation.
-   Implement Q-learning and a rule-based baseline.
-   Evaluate on held-out scenarios and multiple seeds.

### Milestone 4 --- Dashboard

-   Build overview, incident detail, event explorer, and experiment
    pages.
-   Add WebSocket updates if needed.
-   Display agent evidence and simulated outcomes.

### Milestone 5 --- Research evaluation

-   Compare detector baselines.
-   Run agent ablation experiments.
-   Compare fixed and learned response policies.
-   Test altered scenario distributions and reward weights.
-   Record latency and resource usage.

### Milestone 6 --- Final submission

-   Add automated tests and setup documentation.
-   Freeze model and policy versions for final evaluation.
-   Prepare reproducible experiments and a controlled demonstration.
-   Document limitations, ethical considerations, and future work.

------------------------------------------------------------------------

## 14. Testing Strategy

### Unit tests

-   Schema validation and invalid event handling.
-   Feature ordering and preprocessing consistency.
-   Agent output validation.
-   Incident state transition rules.
-   Action allowlist and approval checks.
-   Q-learning update correctness.
-   Reward calculation and simulator transitions.

### Integration tests

-   Event ingestion to detection.
-   Detection to incident creation.
-   Agent orchestration and evidence persistence.
-   Response proposal through safety validation.
-   Simulation outcome to reward logging.
-   API-to-dashboard data contracts.

### Research tests

-   Train/test leakage checks.
-   Per-class detector performance.
-   Ablation: remove correlation or risk enrichment and measure impact.
-   Rule-based versus RL policy comparisons.
-   Multi-seed RL evaluation.
-   Distribution-shift and reward-weight sensitivity tests.

### Acceptance criteria

Define thresholds before final evaluation. At minimum: - All safety
tests pass. - Invalid actions are always rejected. - A failed dependency
never triggers a mitigation. - Each decision can be traced to its
incident, policy version, and evidence. - Experiment results can be
reproduced from documented configurations. - Performance claims are
supported by measured results.

------------------------------------------------------------------------

## 15. Initial Configuration

Suggested initial defaults; these are starting points to validate, not
guaranteed optimal settings.

``` yaml
app:
  name: SentinelX AI
  environment: development
  execution_mode: simulation
  timezone: UTC

detection:
  baseline_model: random_forest
  anomaly_detector_enabled: true
  save_model_metadata: true

agents:
  require_schema_validation: true
  max_retries: 1
  timeout_seconds: 15
  llm_enabled: false

reinforcement_learning:
  algorithm: q_learning
  training_enabled: true
  evaluation_learning_enabled: false
  action_space:
    - raise_alert
    - increase_monitoring
    - escalate_for_approval
    - simulate_block

safety:
  simulation_only: true
  reject_unknown_actions: true
  require_approval_for_simulated_block: true
  allow_production_actions: false

storage:
  database: postgresql
  audit_logging: true
```

------------------------------------------------------------------------

## 16. Key Risks and Mitigations

  -----------------------------------------------------------------------
  Risk                                Mitigation
  ----------------------------------- -----------------------------------
  Dataset leakage or misleading       Group-aware splits, leakage checks,
  metrics                             held-out evaluation

  Class imbalance                     Per-class metrics, class weighting
                                      or resampling within training data

  Agent hallucinations                Typed outputs, evidence references,
                                      deterministic validation

  RL exploits reward loopholes        Separate metrics, reward
                                      sensitivity analysis, constrained
                                      action space

  Simulator is unrealistic            Document assumptions, vary scenario
                                      parameters, avoid overclaiming
                                      real-world impact

  Conflicting agent outputs           Central orchestrator, explicit
                                      conflict flags, escalation

  Excessive project scope             Deliver detection and simulator
                                      first; add LLM and live streaming
                                      only after core tests pass

  Unsafe mitigation                   Simulation-only execution,
                                      allowlist, independent safety gate

  Hard-to-reproduce experiments       Version datasets, model artifacts,
                                      configs, seeds, and policy versions
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## 17. Recommended Reference Resources

-   **CIC-IDS2017:** https://www.unb.ca/cic/datasets/ids-2017.html
-   **UNSW-NB15:**
    https://research.unsw.edu.au/projects/unsw-nb15-dataset
-   **MITRE ATT&CK:** https://attack.mitre.org/
-   **FastAPI documentation:** https://fastapi.tiangolo.com/
-   **scikit-learn documentation:** https://scikit-learn.org/stable/
-   **Gymnasium documentation:** https://gymnasium.farama.org/

------------------------------------------------------------------------

## 18. Final Architecture Decision

Build SentinelX AI as a **modular monolith first**: one FastAPI
application with separate Python modules for ingestion, detection,
orchestration, agents, reinforcement learning, simulation, safety, and
persistence. Use PostgreSQL for application data and Next.js for the
dashboard.

Avoid starting with microservices, Kafka, Kubernetes, or a large agent
framework. They add operational complexity before the core research is
validated. The modular design can be separated into services later if
measured performance or deployment requirements justify it.

The core contribution should be demonstrated through controlled
experiments: **evidence-based multi-agent investigation plus
reinforcement-guided response selection, evaluated against fixed
baselines under a clearly defined safety model.**
