# SentinelX AI --- Phase-Wise Component Implementation Plan

> **Project:** SentinelX AI --- Multi-Agentic AI Framework with
> Autonomous Reasoning and Reinforcement-Guided Adaptive Response for
> Cyber Threat Detection and Mitigation\
> **Purpose:** A buildable, component-by-component implementation plan
> derived from `architecture.md`\
> **Recommended approach:** Build and test a modular monolith before
> considering distributed services\
> **Initial operating mode:** Offline dataset replay and controlled
> simulation only

------------------------------------------------------------------------

## How to Use This Plan

Implement the phases in order. Each phase defines the objective,
components, tasks, expected files, tests, and a definition of done. Do
not move to the next phase until the current phase's acceptance criteria
pass.

### Global engineering rules

1.  Keep all mitigation actions simulation-only.
2.  Build one working end-to-end vertical slice early; avoid creating
    empty modules for the entire architecture.
3.  Use typed Pydantic schemas for all internal and external data
    contracts.
4.  Keep detection training, RL training, and final evaluation separate.
5.  Use configuration and environment variables for secrets and
    deployment settings.
6.  Record dataset, model, policy, experiment, and configuration
    versions.
7.  Never report expected or illustrative numbers as measured results.
8.  Use small fixtures and synthetic events for tests; do not commit
    large datasets or model artifacts.

## Project Stack

  Component              Technology
  ---------------------- ------------------------------------------------
  Backend API            Python, FastAPI, Pydantic
  ML and preprocessing   pandas, NumPy, scikit-learn; XGBoost optional
  RL                     NumPy-based Q-learning; Gymnasium optional
  Database               PostgreSQL, SQLAlchemy or SQLModel, Alembic
  Frontend               Next.js, React, TypeScript, Tailwind CSS
  Charts                 Recharts
  Tests                  pytest; frontend test tooling added as needed
  Local deployment       Docker Compose
  Live updates           FastAPI WebSockets, only after REST flow works

------------------------------------------------------------------------

# Phase 0 --- Scope, Repository, and Development Environment

## Objective

Create a reproducible repository and establish the safety boundary
before implementing AI logic.

## Components

-   Git repository and folder structure.
-   Python virtual environment.
-   Next.js frontend scaffold.
-   Environment configuration.
-   Formatting, linting, and testing basics.
-   Simulation-only execution configuration.

## Tasks

1.  Create the repository and initial README.
2.  Create `backend/` and initialize a Python virtual environment.
3.  Install FastAPI, Uvicorn, Pydantic, pandas, NumPy, scikit-learn,
    SQLAlchemy, Alembic, psycopg, and pytest.
4.  Create the Next.js TypeScript app in `frontend/`.
5.  Add `.env.example` with non-secret placeholders.
6.  Add `.gitignore` entries for `.env`, virtual environments, datasets,
    caches, model files, experiment outputs, and build directories.
7.  Add a `/health` endpoint.
8.  Add a simple frontend page that calls the health endpoint.
9.  Define a single configuration field such as
    `EXECUTION_MODE=simulation`; reject unsupported modes.
10. Add a basic CI workflow to run backend tests and frontend checks.

## Suggested files

``` text
backend/
  app/
    __init__.py
    main.py
    config.py
  tests/
frontend/
.env.example
.gitignore
README.md
```

## Tests

-   Backend starts locally.
-   `GET /api/v1/health` returns a healthy response.
-   Invalid configuration fails safely.
-   Frontend can display backend health status.
-   No secrets or datasets are tracked by Git.

## Definition of done

A new developer can clone the repository, follow the README, start both
applications, and run tests.

------------------------------------------------------------------------

# Phase 1 --- Domain Schemas and Data Contracts

## Objective

Define stable data models before connecting the components. Every later
phase uses these contracts.

## Components

-   Normalized event schema.
-   Detection result schema.
-   Evidence reference schema.
-   Agent result schema.
-   Incident schema and status enum.
-   Response decision schema.
-   Experiment configuration and result schemas.

## Tasks

1.  Implement Pydantic models for all primary entities.
2.  Use UUIDs or consistent string IDs.
3.  Use timezone-aware UTC timestamps.
4.  Define enums for incident statuses, severities, agent names, action
    types, execution modes, and approval statuses.
5.  Validate numeric ranges, payload sizes, and required fields.
6.  Distinguish observed evidence from inferred findings.
7.  Require agent findings to reference event IDs or other traceable
    evidence.
8.  Add schema version fields where evolution is likely.
9.  Create JSON fixtures for valid and invalid payloads.

## Suggested files

``` text
backend/app/
  schemas/
    __init__.py
    events.py
    detections.py
    evidence.py
    agents.py
    incidents.py
    decisions.py
    experiments.py
```

## Tests

-   Valid records parse correctly.
-   Missing IDs, invalid timestamps, invalid scores, and unknown
    statuses are rejected.
-   Agent output cannot include an unregistered action as an executable
    action.
-   Schema serialization is deterministic enough for test fixtures.

## Definition of done

All components can exchange validated structured records without relying
on ad hoc dictionaries or free-form text.

------------------------------------------------------------------------

# Phase 2 --- Data Ingestion and Dataset Adapter

## Objective

Ingest offline network-flow data and simulator events through one
normalized interface.

## Components

-   Dataset adapter.
-   CSV reader.
-   Field mapping.
-   Validation and quarantine handling.
-   Batch replay interface.
-   Dataset/run metadata.

## Tasks

1.  Start with one dataset, preferably CIC-IDS2017.
2.  Inspect columns, labels, nulls, duplicate rows, and class
    distribution.
3.  Write a dataset-specific adapter that maps source columns to an
    internal feature schema.
4.  Separate features from labels; labels must never be sent to model
    inference as input.
5.  Add row validation and error reporting.
6.  Generate an `event_id`, `dataset_id`, and `run_id` for each
    normalized record.
7.  Implement bounded batch iteration rather than loading the entire
    dataset into memory.
8.  Add a small synthetic fixture dataset for tests.
9.  Document how users download datasets; do not commit the full
    dataset.
10. Add a replay service that emits events in deterministic order.

## Suggested files

``` text
backend/app/
  ingestion/
    __init__.py
    base.py
    cic_ids2017.py
    csv_reader.py
    validation.py
    replay.py
  schemas/events.py
data/
  README.md
  samples/
```

## Tests

-   Correct column mapping on fixture rows.
-   Malformed rows are rejected or quarantined.
-   Batch replay emits records in stable order.
-   Labels are stored as metadata but excluded from inference features.
-   Dataset statistics match the fixture's known values.

## Definition of done

A small offline fixture can be ingested and replayed into normalized
event records without requiring a trained model.

------------------------------------------------------------------------

# Phase 3 --- Feature Engineering and Baseline Threat Detector

## Objective

Build a reproducible ML pipeline with a simple baseline before
introducing agent coordination.

## Components

-   Preprocessing pipeline.
-   Training script.
-   Model artifact and metadata.
-   Inference service.
-   Evaluation report.
-   Optional explainability module.

## Tasks

1.  Define the feature allowlist for the selected dataset.
2.  Handle missing values and invalid numeric values.
3.  Encode categorical variables where needed.
4.  Split training and testing data in a way that reduces leakage from
    duplicate or correlated flows.
5.  Fit all preprocessing steps on training data only.
6.  Train a Random Forest baseline.
7.  Optionally train XGBoost as a comparison.
8.  Evaluate precision, recall, macro-F1, false-positive rate, and
    confusion matrix.
9.  Add model version and feature-schema metadata to the saved artifact.
10. Implement inference that enforces the exact training feature order.
11. Add optional SHAP explanations only after the base model is stable.
12. Document class imbalance and label mapping.

## Suggested files

``` text
backend/app/detection/
  __init__.py
  feature_schema.py
  preprocessing.py
  train.py
  inference.py
  evaluation.py
  explainability.py
backend/artifacts/       # local only; not committed
experiments/results/
```

## Tests

-   Training and inference use the same feature order.
-   Test data is not used to fit preprocessing.
-   Unknown or missing features cause a controlled validation error.
-   Saved model can be loaded in a clean process.
-   Evaluation metrics can be regenerated from a recorded configuration.

## Definition of done

The API or a local service can score one normalized event and return a
predicted class, score information, model version, and inference
duration.

------------------------------------------------------------------------

# Phase 4 --- Event and Incident Persistence

## Objective

Persist events, detections, incidents, and component activity in
PostgreSQL.

## Components

-   Database configuration.
-   SQLAlchemy/SQLModel models.
-   Alembic migrations.
-   Repository/data-access layer.
-   Incident lifecycle service.
-   Audit log.

## Tasks

1.  Configure PostgreSQL through environment variables.
2.  Create database models for events, detections, incidents,
    incident-event links, agent runs, response decisions, audit logs,
    and experiment runs.
3.  Add Alembic migrations.
4.  Add foreign keys and indexes for timestamps, statuses, severity, run
    IDs, and relationships.
5.  Implement repositories to keep SQL operations out of API routes.
6.  Use UTC timestamps consistently.
7.  Add transaction boundaries for incident creation and state changes.
8.  Make ingestion idempotent where practical, so replaying the same
    event does not create uncontrolled duplicates.
9.  Ensure audit records are append-oriented.
10. Add database health checking.

## Suggested files

``` text
backend/app/
  database/
    base.py
    session.py
    models.py
    repositories/
  services/
    incident_service.py
backend/migrations/
```

## Tests

-   Migrations create the schema from an empty database.
-   Foreign-key constraints behave correctly.
-   Event and incident records persist and can be queried.
-   Duplicate event ingestion follows the documented idempotency policy.
-   Database unavailability causes a controlled error, not a false
    success.

## Definition of done

Events and incidents survive backend restarts and can be retrieved with
their linked records.

------------------------------------------------------------------------

# Phase 5 --- Detection Agent and Incident Orchestrator

## Objective

Create the first working agent workflow using deterministic behavior and
explicit state transitions.

## Components

-   Detection agent wrapper.
-   Agent interface/protocol.
-   Orchestrator/coordinator.
-   Incident state machine.
-   Agent run tracking.
-   Timeout and failure handling.

## Tasks

1.  Define a common agent interface with input schema, output schema,
    and component version.
2.  Wrap the ML inference service as the Detection Agent.
3.  Create an orchestrator that accepts a normalized event and obtains a
    detection result.
4.  Create an incident when the configured candidate criteria are met.
5.  Define allowed incident state transitions in one state-machine
    module.
6.  Persist agent inputs/outputs or safe summaries and execution
    durations.
7.  Add bounded timeouts and retries.
8.  Handle malformed outputs and component failures.
9.  Ensure agent output never directly triggers mitigation.
10. Keep thresholds configurable and treat them as experimental
    parameters.

## Suggested files

``` text
backend/app/
  agents/
    base.py
    detection_agent.py
  orchestration/
    coordinator.py
    state_machine.py
```

## Tests

-   A benign fixture does not create an incident unless the configured
    policy says it should.
-   A suspicious fixture creates a traceable incident.
-   Invalid agent output is rejected.
-   Repeated events follow a documented deduplication/correlation
    policy.
-   Model failure leads to an error/alert state and never to a
    mitigation.

## Definition of done

One normalized event can travel through detection and incident creation
with all decisions traceable in storage.

------------------------------------------------------------------------

# Phase 6 --- Investigation and Correlation Agent

## Objective

Correlate related events and construct an evidence-backed incident
timeline.

## Components

-   Correlation rules.
-   Time-window grouping.
-   Evidence collection.
-   Incident timeline.
-   Confidence/uncertainty representation.

## Tasks

1.  Define correlation keys appropriate to the dataset, such as
    source/target identifiers and time windows.
2.  Implement deterministic correlation rules first.
3.  Group related events into an incident without double-counting
    evidence.
4.  Record why each event was associated with an incident.
5.  Add repeated-event counts and timeline ordering.
6.  Represent missing or conflicting evidence explicitly.
7.  Keep observed event facts separate from inferred conclusions.
8.  Optionally add an LLM-generated summary after structured evidence is
    reliable; treat it as untrusted presentation text.

## Suggested files

``` text
backend/app/agents/
  investigation_agent.py
backend/app/services/
  correlation_service.py
  timeline_service.py
```

## Tests

-   Events inside a defined correlation window are grouped.
-   Events outside the window are not grouped unless another rule
    applies.
-   Timeline is ordered and retains event IDs.
-   Duplicate events do not inflate evidence counts.
-   Contradictory data is surfaced rather than silently discarded.

## Definition of done

An incident detail response includes linked events, correlation reasons,
a timeline, and evidence gaps.

------------------------------------------------------------------------

# Phase 7 --- Risk Assessment Agent

## Objective

Turn model outputs and correlated evidence into a documented risk
estimate.

## Components

-   Risk feature schema.
-   Risk scoring function.
-   Severity mapping.
-   Asset criticality configuration.
-   Evidence-aware risk explanation.

## Tasks

1.  Define risk inputs: detection score, confidence quality, event
    recurrence, correlated evidence, and asset criticality.
2.  Implement a transparent baseline risk formula or scoring table.
3.  Define severity bands in configuration and document them.
4.  Distinguish detection confidence from risk and severity.
5.  Attach evidence references and list missing information.
6.  Avoid claiming a real-world impact that the available telemetry
    cannot establish.
7.  Optionally map supported behaviors to MITRE ATT&CK techniques with
    source evidence.
8.  Evaluate risk scoring on labeled or simulated scenarios; do not tune
    it against the final test set.

## Suggested files

``` text
backend/app/agents/
  risk_agent.py
backend/app/services/
  risk_scoring.py
backend/app/config/
  risk_policy.yaml
```

## Tests

-   Risk score remains within its defined range.
-   Identical inputs produce identical scores.
-   Increasing a risk factor behaves as documented.
-   Missing evidence is handled explicitly.
-   Severity mapping has boundary tests.

## Definition of done

Every incident includes a reproducible risk score, severity, rationale,
and evidence references.

------------------------------------------------------------------------

# Phase 8 --- Mitigation Planning and Deterministic Safety Gate

## Objective

Generate safe response proposals and validate them independently of
agents and the RL policy.

## Components

-   Fixed action catalogue.
-   Mitigation planning agent.
-   Safety gate.
-   Approval workflow.
-   Simulated action executor.
-   Rollback/status records.

## Tasks

1.  Define the only allowed actions: `raise_alert`,
    `increase_monitoring`, `escalate_for_approval`, and
    `simulate_block`.
2.  Define action prerequisites, reversibility, disruption estimate, and
    approval requirement.
3.  Implement the mitigation planner to rank only known actions.
4.  Implement a server-side allowlist validator.
5.  Reject unknown actions even if a model or agent proposes them.
6.  Require approval for simulated blocking according to the project's
    policy.
7.  Implement a simulator-only executor that changes simulated state,
    never real network state.
8.  Record proposed, rejected, approved, simulated, and completed states
    distinctly.
9.  Add rollback metadata for reversible simulator actions.
10. Make the default action on any error `alert-only` or `no-action`.

## Suggested files

``` text
backend/app/
  agents/mitigation_agent.py
  safety/
    action_catalogue.py
    policy_gate.py
    approval.py
  simulator/
    action_executor.py
```

## Tests

-   Unknown action is always rejected.
-   An action with missing prerequisites is rejected.
-   Approval-required actions cannot bypass approval.
-   Simulator cannot contact external hosts or execute OS commands.
-   Errors result in alert/no-action and are audited.
-   Rollback returns simulated state to the documented prior state.

## Definition of done

The system can recommend an action, validate it, obtain approval where
required, and execute it only against a simulated asset.

------------------------------------------------------------------------

# Phase 9 --- Incident Simulator and Outcome Evaluator

## Objective

Create reproducible scenarios that model threat behavior, defensive
actions, and operational consequences.

## Components

-   Scenario definitions.
-   Simulator state.
-   Transition model.
-   Outcome evaluator.
-   Seed control.
-   Episode logger.

## Tasks

1.  Define a small set of scenarios such as benign burst, repeated login
    failures, scanning-like flow patterns, and high-volume traffic
    anomalies.
2.  Give every scenario explicit initial state, event sequence,
    ground-truth scenario label, and parameters.
3.  Model each allowed action's potential benefit and cost.
4.  Include uncertainty: an action should not always succeed.
5.  Model false alarms and service disruption for benign scenarios.
6.  Use a seeded random generator for reproducibility.
7.  Ensure the simulator outcome is independent of the policy's chosen
    action where ground truth should be fixed.
8.  Record action, transition, outcome, and reason for each episode
    step.
9.  Keep the simulator model documented as an approximation, not a
    faithful reproduction of real networks.

## Suggested files

``` text
backend/app/simulator/
  scenarios.py
  environment.py
  transition_model.py
  outcome_evaluator.py
```

## Tests

-   Same seed and configuration produce the same episode.
-   Every action has a defined transition behavior.
-   Benign scenarios can incur a cost for unnecessary blocking.
-   Ground-truth labels cannot be read by the policy as input features.
-   Invalid actions are rejected by the simulator.

## Definition of done

A complete simulated incident episode can be run repeatedly and returns
a structured outcome suitable for RL training and evaluation.

------------------------------------------------------------------------

# Phase 10 --- Reinforcement Learning Policy

## Objective

Train and evaluate a Q-learning policy to choose defensive actions in
the simulator.

## Components

-   State encoder/discretizer.
-   Q-table.
-   Epsilon-greedy training loop.
-   Reward calculator.
-   Policy versioning.
-   Frozen evaluation runner.
-   Baseline policies.

## Tasks

1.  Define a compact state vector from risk, confidence, recurrence,
    asset criticality, and previous outcomes.
2.  Discretize continuous inputs and document bucket boundaries.
3.  Define the fixed action index mapping.
4.  Implement Q-learning using NumPy.
5.  Add configurable learning rate, discount factor, exploration
    schedule, episode count, and random seed.
6.  Implement a reward function for containment benefit minus
    false-action, disruption, and delay costs.
7.  Unit-test the Q-value update with a hand-calculated example.
8.  Implement fixed rule-based, threshold, and random permitted-action
    baselines.
9.  Train on training scenarios only.
10. Save the policy table and all configuration/metadata.
11. Evaluate a frozen policy on held-out scenario seeds without learning
    updates.
12. Compare multiple seeds and report reward and individual outcome
    metrics.
13. Run sensitivity experiments on reward weights and scenario
    distribution.

## Suggested files

``` text
backend/app/rl/
  state_encoder.py
  q_learning.py
  policy.py
  reward.py
  evaluation.py
experiments/
  configs/
  results/
```

## Tests

-   Q-learning update matches expected numeric output.
-   Policy only returns a valid action index.
-   Evaluation mode does not update the Q-table.
-   Training with the same seed/configuration is reproducible.
-   Metrics are computed from episode outcomes, not inferred from reward
    alone.
-   A policy artifact records its state/action mapping and
    configuration.

## Definition of done

A trained, versioned Q-learning policy can be compared fairly against
fixed baselines on held-out simulated episodes.

------------------------------------------------------------------------

# Phase 11 --- REST API Integration

## Objective

Expose stable functionality to the frontend through versioned REST
endpoints.

## Components

-   FastAPI routers.
-   Request/response schemas.
-   Authentication/role boundary for approval endpoints.
-   Pagination and filtering.
-   Error handling.
-   API documentation.

## Tasks

1.  Add `/api/v1` routes for events, incidents, replay, experiments, and
    audit records.
2.  Implement event and incident filtering with pagination.
3.  Add endpoints to start and stop offline replay.
4.  Add incident detail endpoints containing evidence and agent results.
5.  Add a simulated-response endpoint that calls the safety gate.
6.  Add approval endpoint with role checks.
7.  Add experiment start/status/metrics endpoints.
8.  Standardize error response schemas and HTTP status codes.
9.  Add request size limits and validation.
10. Add API integration tests.

## Suggested endpoints

  --------------------------------------------------------------------------------------------
  Method                  Endpoint                                     Purpose
  ----------------------- -------------------------------------------- -----------------------
  `GET`                   `/api/v1/health`                             Health

  `GET`                   `/api/v1/events`                             List/filter events

  `POST`                  `/api/v1/replay/start`                       Start replay

  `POST`                  `/api/v1/replay/{run_id}/stop`               Stop replay

  `GET`                   `/api/v1/incidents`                          List incidents

  `GET`                   `/api/v1/incidents/{id}`                     Incident detail

  `POST`                  `/api/v1/incidents/{id}/investigate`         Run investigation

  `POST`                  `/api/v1/incidents/{id}/simulate-response`   Propose/execute
                                                                       permitted simulation

  `POST`                  `/api/v1/incidents/{id}/approval`            Record approval
                                                                       decision

  `GET`                   `/api/v1/experiments`                        List experiments

  `GET`                   `/api/v1/experiments/{id}/metrics`           Experiment metrics

  `GET`                   `/api/v1/audit`                              Audit records
  --------------------------------------------------------------------------------------------

## Tests

-   Invalid query parameters return validation errors.
-   Unauthorized users cannot approve actions.
-   Simulation endpoint rejects unapproved or unknown actions.
-   Pagination is stable.
-   API responses conform to schemas.

## Definition of done

All core backend capabilities are accessible through documented and
tested APIs.

------------------------------------------------------------------------

# Phase 12 --- Frontend Dashboard

## Objective

Build a useful analyst-facing UI after API contracts stabilize.

## Components

-   Dashboard overview.
-   Event explorer.
-   Incident list and detail.
-   Agent evidence panel.
-   Mitigation approval panel.
-   RL experiment lab.
-   Audit log.
-   Loading, empty, and error states.

## Tasks

1.  Configure a typed API client and environment variable for the
    backend base URL.
2.  Build overview cards and trend charts using actual API data.
3.  Build an event table with filtering and pagination.
4.  Build incident detail with timeline, evidence, severity, and agent
    results.
5.  Clearly distinguish predicted class, classifier score, risk score,
    and ground truth.
6.  Show action proposal, safety result, approval status, and simulator
    outcome separately.
7.  Build experiment charts for reward, containment, false actions,
    disruption, and latency.
8.  Build audit history with filters.
9.  Add loading, retry, empty, and API-error states.
10. Ensure the UI never claims a real mitigation occurred when it was
    simulated.
11. Add frontend linting and basic component tests.

## Suggested files

``` text
frontend/
  app/
    page.tsx
    events/page.tsx
    incidents/page.tsx
    incidents/[id]/page.tsx
    experiments/page.tsx
    audit/page.tsx
  components/
    overview/
    events/
    incidents/
    agents/
    mitigation/
    experiments/
    audit/
  lib/
    api.ts
    types.ts
```

## Tests

-   Dashboard renders with fixture API data.
-   Empty and error states are understandable.
-   Incident details display linked evidence.
-   Approval controls are disabled when approval is not permitted.
-   Labels clearly identify simulation mode.

## Definition of done

A user can replay a sample dataset, view resulting incidents, inspect
agent evidence, review a simulated response, and inspect evaluation
metrics from the browser.

------------------------------------------------------------------------

# Phase 13 --- Live Updates and Experiment Management

## Objective

Add real-time presentation and reproducible experiment controls after
the basic system works.

## Components

-   WebSocket event stream.
-   Replay run status.
-   Experiment configuration validation.
-   Background task lifecycle.
-   Progress and cancellation.
-   Experiment artifact storage.

## Tasks

1.  Add a WebSocket endpoint for event/incident updates.
2.  Keep REST as the source of truth; WebSocket messages are
    notifications, not the only copy of data.
3.  Handle disconnect/reconnect and fetch current state after reconnect.
4.  Add experiment run states: queued, running, completed, failed,
    cancelled.
5.  Validate experiment configuration and resource limits.
6.  Store configuration, seed, dataset/model/policy version, metrics,
    and artifact locations.
7.  Avoid running long training jobs inside request handlers; use a
    simple background worker for the prototype.
8.  Add safe cancellation and failure reporting.
9.  Prevent concurrent jobs from overwriting the same output artifact.

## Suggested files

``` text
backend/app/
  api/websocket.py
  experiments/
    runner.py
    registry.py
frontend/components/
  live-event-feed.tsx
  experiment-status.tsx
```

## Tests

-   WebSocket clients receive event notifications.
-   Reconnect can recover current state via REST.
-   Failed jobs are marked failed and preserve error summaries.
-   Two experiment runs do not overwrite each other's artifacts.
-   Cancellation leaves records in a consistent state.

## Definition of done

The dashboard updates as replay runs and experiments progress, with
durable status available through REST.

------------------------------------------------------------------------

# Phase 14 --- Evaluation, Ablation, and Research Report

## Objective

Produce credible experimental evidence for the final-year report.

## Experiments

### Experiment A --- Detector comparison

-   Random Forest baseline versus an optional second classifier.
-   Report per-class precision, recall, F1, confusion matrix, and
    false-positive rate.
-   Document split strategy and leakage checks.

### Experiment B --- Agent ablation

-   Full pipeline versus a pipeline without correlation.
-   Full pipeline versus a pipeline without risk enrichment.
-   Measure changes in investigation quality, decision quality, and
    latency using predefined criteria.

### Experiment C --- Response policy

-   Rule-based baseline versus threshold baseline versus Q-learning.
-   Evaluate on identical held-out scenario seeds.
-   Report containment, unnecessary response rate, disruption, delay,
    and reward.

### Experiment D --- Robustness

-   Change scenario mix and asset criticality.
-   Vary reward weights.
-   Evaluate on new seeds and held-out configurations.
-   Document failure cases and policy brittleness.

### Experiment E --- System performance

-   Measure event throughput, inference time, end-to-end incident
    latency, agent overhead, and memory usage.
-   Report environment/hardware and measurement method.

## Tasks

1.  Freeze the final model, policy, configuration, and dataset split.
2.  Write a script or notebook for every reported metric.
3.  Run multiple seeds for RL comparisons.
4.  Save raw experiment outputs and aggregate summaries.
5.  Use confidence intervals or appropriate variability summaries where
    possible.
6.  Include negative results and limitations.
7.  Separate measured results from expectations.
8.  Create diagrams and tables for the report.

## Definition of done

A reviewer can reproduce the main claims from the repository's
documented setup, configuration, and evaluation commands.

------------------------------------------------------------------------

# Phase 15 --- Hardening, Demo, and Submission

## Objective

Make the project stable, safe, demonstrable, and easy to evaluate.

## Tasks

1.  Run all backend and frontend tests from a clean checkout.
2.  Test the complete flow: replay → detection → incident → agent
    investigation → risk → response proposal → safety check → simulation
    → metrics.
3.  Verify all mitigation actions remain simulation-only.
4.  Verify every decision is traceable to evidence and version metadata.
5.  Add database migration and reset instructions for local demo use.
6.  Add Docker Compose only after local development works.
7.  Add a `.env.example` without real credentials.
8.  Document setup, dataset acquisition, training, evaluation, and demo
    commands.
9.  Prepare a scripted demo with one benign scenario and multiple
    suspicious scenarios.
10. Prepare slides covering problem, related work, architecture,
    methods, experiments, results, limitations, and future work.
11. Record known limitations and ethical/safety considerations.

## Definition of done

The full system runs from documented commands, demonstrates the
end-to-end pipeline safely, and supports the measured claims in the
final report.

------------------------------------------------------------------------

# Dependency Map

``` mermaid
flowchart TD
    P0[Phase 0: Setup] --> P1[Phase 1: Schemas]
    P1 --> P2[Phase 2: Ingestion]
    P1 --> P4[Phase 4: Persistence]
    P2 --> P3[Phase 3: Detector]
    P3 --> P5[Phase 5: Orchestrator]
    P4 --> P5
    P5 --> P6[Phase 6: Correlation]
    P6 --> P7[Phase 7: Risk]
    P7 --> P8[Phase 8: Safety and Mitigation]
    P8 --> P9[Phase 9: Simulator]
    P9 --> P10[Phase 10: RL]
    P5 --> P11[Phase 11: REST API]
    P8 --> P11
    P10 --> P11
    P11 --> P12[Phase 12: Dashboard]
    P12 --> P13[Phase 13: Live Updates]
    P10 --> P14[Phase 14: Evaluation]
    P12 --> P14
    P14 --> P15[Phase 15: Submission]
```

The diagram is a logical dependency map; persistence work can proceed in
parallel with ingestion after the schemas are stable.

------------------------------------------------------------------------

# Recommended First End-to-End Vertical Slice

Before implementing all agents, complete this small flow:

1.  Load three to ten synthetic normalized events.
2.  Validate them using Pydantic.
3.  Run a placeholder or baseline detector.
4.  Create an incident record for a suspicious event.
5.  Persist the event and incident in PostgreSQL.
6.  Return the incident from FastAPI.
7.  Display the incident in a simple Next.js page.
8.  Add a simulated `raise_alert` action and an audit record.

This proves the contracts, persistence, API, and frontend are connected.
Then replace the placeholder detector and expand agent behavior in later
phases.

------------------------------------------------------------------------

# Suggested Project Commands

Exact commands depend on the chosen package manager and deployment
setup. Document the commands actually implemented in the repository. A
typical development workflow should provide equivalents for:

``` bash
# Backend
cd backend
python -m venv .venv
# Activate the virtual environment for your OS
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend (in a separate terminal)
cd frontend
npm install
npm run dev

# Tests
cd backend
pytest
```

Database startup and migration commands should be added once PostgreSQL
and Alembic are configured.

------------------------------------------------------------------------

# Final Implementation Priorities

If time is limited, prioritize these deliverables in order:

1.  **Must have:** data schema, one dataset adapter, baseline detector,
    incident persistence, orchestrator, safe simulator, rule-based
    response, Q-learning comparison, API, and basic dashboard.
2.  **Should have:** evidence correlation, risk scoring, audit UI,
    repeatable experiments, and ablation studies.
3.  **Stretch goals:** optional LLM summaries, second dataset, SHAP
    explanations, WebSockets, and richer scenario generation.

Do not sacrifice experimental validity or safety to add more frameworks.
A small, reproducible multi-agent system with a measured RL comparison
is stronger than a large collection of loosely connected components.
