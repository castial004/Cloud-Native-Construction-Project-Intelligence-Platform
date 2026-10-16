"""Ingestion service validation tests (FastAPI TestClient)."""
from __future__ import annotations

import datetime as dt

import pytest
from fastapi.testclient import TestClient

from services.ingestion.app.main import app

client = TestClient(app)


def _iso(days=0):
    return (dt.datetime(2023, 1, 1, tzinfo=dt.timezone.utc) + dt.timedelta(days=days)).isoformat()


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_project_rejects_negative_budget():
    payload = [{
        "project_id": "T-P1", "name": "bad", "contractor": "X",
        "budget_at_completion": -5, "planned_start": "2023-01-01", "planned_finish": "2023-02-01",
    }]
    r = client.post("/projects", json=payload)
    assert r.status_code == 422


def test_project_rejects_finish_before_start():
    payload = [{
        "project_id": "T-P2", "name": "bad", "contractor": "X",
        "budget_at_completion": 1000, "planned_start": "2023-03-01", "planned_finish": "2023-02-01",
    }]
    r = client.post("/projects", json=payload)
    assert r.status_code == 422


def test_progress_rejects_naive_timestamp():
    payload = [{
        "activity_id": "A", "timestamp": "2023-01-01T00:00:00",
        "percent_complete": 10, "earned_value": 1, "planned_value": 2,
    }]
    r = client.post("/progress", json=payload)
    assert r.status_code == 422


def test_progress_rejects_out_of_range_percent():
    payload = [{
        "activity_id": "A", "timestamp": _iso(1),
        "percent_complete": 150, "earned_value": 1, "planned_value": 2,
    }]
    r = client.post("/progress", json=payload)
    assert r.status_code == 422


def test_extra_field_rejected():
    payload = [{
        "project_id": "T-P3", "name": "x", "contractor": "X",
        "budget_at_completion": 1000, "planned_start": "2023-01-01", "planned_finish": "2023-02-01",
        "unexpected": 1,
    }]
    r = client.post("/projects", json=payload)
    assert r.status_code == 422
