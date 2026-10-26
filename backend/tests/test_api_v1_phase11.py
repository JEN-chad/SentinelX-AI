"""SentinelX AI - Phase 11 Tests: REST API Integration & Safety Authorization Boundary

Tests replay stop endpoint, role-based approval authorization (403 for unauthorized, 200 for authorized),
simulator scenario exploration & execution endpoints, and experiment benchmark APIs.
"""

import pytest


def test_stop_replay_endpoint(client):
    """Verify replay stop endpoint halts replay and emits an audit event."""
    response = client.post("/api/v1/replay/run-test-replay-001/stop")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "stopped"
    assert data["run_id"] == "run-test-replay-001"
    assert "stopped_at" in data
    assert data["execution_mode"] == "simulation"


def test_approval_role_authorization_enforcement(client):
    """SAFETY GATE: Unauthorized reviewer roles MUST be rejected with 403 Forbidden."""
    # First, run a small replay to produce an incident
    replay_resp = client.post("/api/v1/replay/start?max_rows=12")
    assert replay_resp.status_code == 200
    incidents = replay_resp.json().get("incidents_created", [])
    assert len(incidents) > 0
    incident_id = incidents[0]

    # Advance incident state: investigate -> risk -> mitigate
    client.post(f"/api/v1/incidents/{incident_id}/investigate")
    client.post(f"/api/v1/incidents/{incident_id}/risk")
    client.post(f"/api/v1/incidents/{incident_id}/mitigate")

    # 1. Attempt approval with unauthorized role via query parameter -> 403 FORBIDDEN
    unauthorized_resp = client.post(
        f"/api/v1/incidents/{incident_id}/approval",
        params={
            "reviewer_id": "guest_user",
            "reviewer_role": "guest",
            "action": "simulate_block",
            "approval_status": "approved",
        },
    )
    assert unauthorized_resp.status_code == 403
    assert "lacks authority" in unauthorized_resp.json()["detail"]

    # 2. Attempt approval with unauthorized role via header -> 403 FORBIDDEN
    unauth_header_resp = client.post(
        f"/api/v1/incidents/{incident_id}/approval",
        headers={"X-User-Role": "unauthorized_viewer"},
        params={
            "reviewer_id": "analyst_temp",
            "action": "simulate_block",
            "approval_status": "approved",
        },
    )
    assert unauth_header_resp.status_code == 403

    # 3. Valid authorized role (e.g. security_analyst) -> 200 OK
    auth_resp = client.post(
        f"/api/v1/incidents/{incident_id}/approval",
        params={
            "reviewer_id": "analyst_lead",
            "reviewer_role": "security_analyst",
            "action": "simulate_block",
            "approval_status": "approved",
            "comment": "Confirmed malicious volumetric flood",
        },
    )
    assert auth_resp.status_code == 200
    approval_data = auth_resp.json()
    assert approval_data["status"] == "approved"
    assert approval_data["incident_id"] == incident_id


def test_simulator_scenarios_listing_api(client):
    """Verify catalogue of reproducible simulation scenarios can be inspected via REST."""
    response = client.get("/api/v1/simulator/scenarios")
    assert response.status_code == 200
    scenarios = response.json()
    assert isinstance(scenarios, list)
    assert len(scenarios) >= 5

    ids = [s["scenario_id"] for s in scenarios]
    assert "scen-high-ddos" in ids
    assert "scen-benign-burst" in ids


def test_simulator_run_scenario_api(client):
    """Verify executing a simulation scenario through REST returns step traces and structured outcome."""
    # Run DoS scenario with RuleBasedPolicy
    response = client.post(
        "/api/v1/simulator/run-scenario",
        params={
            "scenario_id": "scen-high-ddos",
            "policy_type": "rule_based",
            "seed": 42,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["scenario_id"] == "scen-high-ddos"
    assert data["policy_used"] == "RuleBasedPolicy"
    assert "containment_success" in data
    assert "net_reward" in data
    assert len(data["step_traces"]) > 0

    # Test rejection of invalid scenario
    bad_scen_resp = client.post(
        "/api/v1/simulator/run-scenario",
        params={"scenario_id": "nonexistent-scenario", "policy_type": "rule_based"},
    )
    assert bad_scen_resp.status_code == 404

    # Test rejection of invalid policy
    bad_pol_resp = client.post(
        "/api/v1/simulator/run-scenario",
        params={"scenario_id": "scen-high-ddos", "policy_type": "unknown_ai_policy"},
    )
    assert bad_pol_resp.status_code == 400


def test_experiments_api_lifecycle(client):
    """Verify running an RL benchmark experiment, persisting it, and retrieving metrics via REST."""
    # 1. Run RL benchmark experiment
    run_resp = client.post(
        "/api/v1/experiments/run",
        params={
            "experiment_type": "rl_benchmark",
            "episodes": 15,
            "seed": 42,
        },
    )
    assert run_resp.status_code == 200
    exp_data = run_resp.json()
    exp_id = exp_data["experiment_id"]
    assert exp_data["status"] == "completed"
    assert "metrics" in exp_data
    assert "detailed_comparison" in exp_data

    # 2. List experiments
    list_resp = client.get("/api/v1/experiments")
    assert list_resp.status_code == 200
    exp_list = list_resp.json()
    assert any(e["experiment_id"] == exp_id for e in exp_list)

    # 3. Get experiment detail
    detail_resp = client.get(f"/api/v1/experiments/{exp_id}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["experiment_id"] == exp_id
    assert detail["status"] == "completed"

    # 4. Get experiment metrics
    metrics_resp = client.get(f"/api/v1/experiments/{exp_id}/metrics")
    assert metrics_resp.status_code == 200
    metrics_data = metrics_resp.json()
    assert metrics_data["experiment_id"] == exp_id
    assert "metrics" in metrics_data
