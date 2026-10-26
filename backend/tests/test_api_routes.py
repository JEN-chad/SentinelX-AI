"""Integration tests for FastAPI REST API endpoints."""

from fastapi.testclient import TestClient
import pytest

from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_api_replay_and_incident_flow(client):
    """Test full API sequence: replay -> event list -> incident list -> incident detail -> investigation."""
    # 1. Start Replay
    replay_resp = client.post("/api/v1/replay/start?max_rows=10")
    assert replay_resp.status_code == 200
    data = replay_resp.json()
    assert data["status"] == "completed"
    assert data["processed_events"] > 0

    # 2. List Events
    events_resp = client.get("/api/v1/events?limit=10")
    assert events_resp.status_code == 200
    events = events_resp.json()
    assert len(events) > 0
    assert "event_id" in events[0]
    assert "features" in events[0]

    # 3. List Incidents
    incidents_resp = client.get("/api/v1/incidents")
    assert incidents_resp.status_code == 200
    incidents = incidents_resp.json()
    assert len(incidents) > 0

    incident_id = incidents[0]["incident_id"]

    # 4. Incident Detail
    detail_resp = client.get(f"/api/v1/incidents/{incident_id}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["incident_id"] == incident_id
    assert len(detail["evidence"]) > 0

    # 5. Trigger Investigation via API
    inv_resp = client.post(f"/api/v1/incidents/{incident_id}/investigate?time_window_seconds=600")
    assert inv_resp.status_code == 200
    inv_data = inv_resp.json()
    assert inv_data["incident_id"] == incident_id
    assert inv_data["status"] == "risk_assessed"

    # 6. Audit Logs
    audit_resp = client.get("/api/v1/audit")
    assert audit_resp.status_code == 200
    audits = audit_resp.json()
    assert len(audits) > 0
    assert "verification_hash" in audits[0]
