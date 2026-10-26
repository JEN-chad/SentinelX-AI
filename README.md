# SentinelX AI

> **SentinelX: A Multi-Agentic AI Framework with Autonomous Reasoning and Reinforcement-Guided Adaptive Response for Cyber Threat Detection and Mitigation**
> Final-Year B.Tech AI & Data Science Project

---

## 1. Project Overview

SentinelX AI combines machine-learning-based threat detection, multi-agent incident investigation, dynamic risk assessment, and reinforcement-learning-guided defensive response selection.

The primary operational paradigm of SentinelX AI is strictly **offline dataset replay and controlled simulation mode**. No autonomous actions are executed on real production networks or endpoints.

---

## 2. Core Architectural Principles & Safety

1. **Simulation-Only Execution:** Every mitigation action targets a controlled simulation environment. Real network execution is blocked by deterministic safety gates.
2. **Action Catalogue Allowlist:** Agents and RL policies may only recommend actions defined in the system catalogue (`raise_alert`, `increase_monitoring`, `escalate_for_approval`, `simulate_block`).
3. **Traceable Evidence:** Inferred conclusions and agent recommendations must link directly to observable events (`event_id`) and metrics.
4. **Typed Schema Contracts:** All component interactions and data exchanges occur via strongly-typed Pydantic contracts.

---

## 3. Development Phases

- **Phase 0:** Scope, Repository, and Environment Setup *(Complete)*
- **Phase 1:** Domain Schemas & Data Contracts *(Complete)*
- **Phase 2:** Data Ingestion & Dataset Adapter
- **Phase 3:** Feature Engineering & Baseline Threat Detector
- **Phase 4:** Agent Orchestration & Investigation Pipeline
- **Phase 5:** Simulation Environment & Reinforcement Learning Response Policy
- **Phase 6:** Full-Stack Dashboard & API Integration
- **Phase 7:** Research Evaluation & Benchmarking

---

## 4. Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+ (for frontend)

### Backend Setup
```bash
# Navigate to backend
cd backend

# Create virtual environment (if not already created)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run test suite
pytest
```

### Running the API
```bash
python -m uvicorn app.main:app --reload --port 8000
```
Health endpoint: `http://127.0.0.1:8000/api/v1/health`
Interactive API Docs: `http://127.0.0.1:8000/docs`
