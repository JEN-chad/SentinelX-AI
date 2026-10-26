"""Tests for SentinelX AI Health and Boundary Checks."""

import pytest
from httpx import AsyncClient
from app.config import Settings, ExecutionMode


def test_health_endpoint(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app"] == "SentinelX AI"
    assert data["execution_mode"] == "simulation"
    assert data["simulation_only"] is True
    assert "version" in data
    assert "timestamp" in data


def test_safety_boundary_execution_mode():
    """Verify that settings reject production execution mode."""
    with pytest.raises(ValueError, match="SAFETY VIOLATION"):
        Settings(EXECUTION_MODE="production")

    with pytest.raises(ValueError, match="SAFETY VIOLATION"):
        Settings(EXECUTION_MODE="live_firewall")

    # Valid simulation mode passes
    valid_settings = Settings(EXECUTION_MODE="simulation")
    assert valid_settings.execution_mode == "simulation"


def test_safety_boundary_allow_production_actions():
    """Verify that allow_production_actions cannot be set to True."""
    with pytest.raises(ValueError, match="SAFETY VIOLATION"):
        Settings(allow_production_actions=True)
