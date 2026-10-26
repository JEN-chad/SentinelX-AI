"""Pytest fixtures and configuration for SentinelX AI."""

import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from app.main import app

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def load_fixture():
    """Helper to load a JSON fixture file."""
    def _loader(filename: str):
        filepath = FIXTURES_DIR / filename
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return _loader


@pytest.fixture
def valid_event_dict(load_fixture):
    return load_fixture("valid_event.json")


@pytest.fixture
def invalid_event_dict(load_fixture):
    return load_fixture("invalid_event.json")


@pytest.fixture
def valid_detection_dict(load_fixture):
    return load_fixture("valid_detection.json")


@pytest.fixture
def valid_evidence_dict(load_fixture):
    return load_fixture("valid_evidence.json")


@pytest.fixture
def valid_incident_dict(load_fixture):
    return load_fixture("valid_incident.json")


@pytest.fixture
def valid_decision_dict(load_fixture):
    return load_fixture("valid_decision.json")


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client
