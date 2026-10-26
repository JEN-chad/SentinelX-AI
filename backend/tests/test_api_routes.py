"""Integration tests for FastAPI REST API endpoints."""

from fastapi.testclient import TestClient
import pytest

from app.main import app



def test_api_full_multi_agent_flow(client):
    """Test full Phase 0-8 API sequence:
    replay -> event list -> incident list -> investigation -> risk assessment ->
    mitigation proposal -> analyst approval -> simulated response -> audit trail.
    """
    # 1. Start Replay (Phase 2 & 3 & 5)
    replay_resp = client.post("/api/v1/replay/start?max_rows=12")
    assert replay_resp.status_code == 200
    data = replay_resp.json()
    assert data["status"] == "completed"
    assert data["processed_events"] > 0

    # 2. List Events (Phase 2)
    events_resp = client.get("/api/v1/events?limit=10")
    assert events_resp.status_code == 200
    events = events_resp.json()
    assert len(events) > 0
    assert "event_id" in events[0]
    assert "features" in events[0]

    # 3. List Incidents (Phase 4 & 5)
    incidents_resp = client.get("/api/v1/incidents")
    assert incidents_resp.status_code == 200
    incidents = incidents_resp.json()
    assert len(incidents) > 0

    incident_id = incidents[0]["incident_id"]

    # 4. Incident Detail (Phase 4 & 5)
    detail_resp = client.get(f"/api/v1/incidents/{incident_id}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["incident_id"] == incident_id
    assert len(detail["evidence"]) > 0

    # 5. Trigger Investigation Agent (Phase 6)
    inv_resp = client.post(f"/api/v1/incidents/{incident_id}/investigate?time_window_seconds=600")
    assert inv_resp.status_code == 200
    inv_data = inv_resp.json()
    assert inv_data["incident_id"] == incident_id
    assert inv_data["status"] == "risk_assessed"

    # 6. Trigger Risk Assessment Agent (Phase 7)
    risk_resp = client.post(f"/api/v1/incidents/{incident_id}/risk")
    assert risk_resp.status_code == 200
    risk_data = risk_resp.json()
    assert risk_data["status"] == "response_proposed"
    assert 0.0 <= risk_data["risk_score"] <= 1.0
    assert risk_data["mitre_technique"] is not None

    # 7. Trigger Mitigation Planning Agent (Phase 8)
    mit_resp = client.post(f"/api/v1/incidents/{incident_id}/mitigate")
    assert mit_resp.status_code == 200
    mit_data = mit_resp.json()
    assert mit_data["status"] in ["approval_required", "simulating"]
    assert len(mit_data["mitigation_result"]["proposed_actions"]) > 0

    # 8. Record Human Analyst Approval (Phase 8)
    appr_resp = client.post(
        f"/api/v1/incidents/{incident_id}/approval?reviewer_id=analyst_carol&action=simulate_block&approval_status=approved"
    )
    assert appr_resp.status_code == 200
    appr_data = appr_resp.json()
    assert appr_data["status"] == "approved"

    # 9. Execute Permitted Simulated Response (Phase 8)
    sim_resp = client.post(f"/api/v1/incidents/{incident_id}/simulate-response?action=simulate_block")
    assert sim_resp.status_code == 200
    sim_data = sim_resp.json()
    assert sim_data["status"] == "outcome_recorded"
    assert sim_data["outcome"]["containment_success"] is True

    # 10. Audit Logs (Phase 4 & 8)
    audit_resp = client.get("/api/v1/audit")
    assert audit_resp.status_code == 200
    audits = audit_resp.json()
    assert len(audits) >= 5
    assert all("verification_hash" in a for a in audits)
