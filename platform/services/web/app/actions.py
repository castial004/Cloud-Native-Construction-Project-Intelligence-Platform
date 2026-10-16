"""Write actions triggered from the UI: CSV upload + pipeline re-runs.

CSV uploads are validated and pushed through the *ingestion service* (same path
as the CLI loader), so the UI never bypasses validation.
"""
from __future__ import annotations

import csv
import io
import threading

import httpx

from common.config import settings
from services.analytics.app.worker import run as run_evm
from services.risk.app.score import run as run_risk

# Endpoint -> required columns (validated before forwarding to ingestion).
UPLOAD_SPECS = {
    "projects": {
        "endpoint": "/projects",
        "columns": {"project_id", "name", "budget_at_completion", "planned_start", "planned_finish"},
    },
    "activities": {
        "endpoint": "/activities",
        "columns": {"activity_id", "project_id", "name", "planned_start", "planned_finish",
                    "planned_duration_days", "budget"},
    },
    "progress": {
        "endpoint": "/progress",
        "columns": {"activity_id", "timestamp", "percent_complete", "earned_value", "planned_value"},
    },
    "costs": {
        "endpoint": "/costs",
        "columns": {"activity_id", "timestamp", "actual_cost"},
    },
}

# In-memory job status for pipeline re-runs (single-node demo).
_PIPELINE_STATUS: dict = {"running": False, "last": None}


def _parse_csv(content: bytes) -> list[dict]:
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    return [row for row in reader]


def upload_csv(kind: str, content: bytes, api: str) -> dict:
    if kind not in UPLOAD_SPECS:
        return {"ok": False, "error": f"unknown upload kind '{kind}'"}
    spec = UPLOAD_SPECS[kind]
    try:
        rows = _parse_csv(content)
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": f"could not parse CSV: {e}"}
    if not rows:
        return {"ok": False, "error": "CSV is empty"}

    missing = spec["columns"] - set(rows[0].keys())
    if missing:
        return {"ok": False, "error": f"missing columns: {sorted(missing)}"}

    inserted = rejected = 0
    with httpx.Client(base_url=api, timeout=60.0) as client:
        for i in range(0, len(rows), 500):
            chunk = rows[i:i + 500]
            resp = client.post(spec["endpoint"], json=chunk)
            if resp.status_code >= 400:
                rejected += len(chunk)
                return {"ok": False, "error": f"ingestion rejected: {resp.text[:300]}",
                        "inserted": inserted, "rejected": rejected}
            inserted += resp.json().get("inserted", len(chunk))
    return {"ok": True, "inserted": inserted, "rejected": rejected}


def recompute() -> dict:
    """Re-run EVM analytics + risk scoring synchronously."""
    evm_rows = run_evm()
    risk_rows = run_risk()
    return {"ok": True, "evm_rows": evm_rows, "risk_rows": risk_rows}


def _run_async(fn):
    def target():
        try:
            _PIPELINE_STATUS["last"] = fn()
        except Exception as e:  # noqa: BLE001
            _PIPELINE_STATUS["last"] = {"ok": False, "error": str(e)}
        finally:
            _PIPELINE_STATUS["running"] = False
    _PIPELINE_STATUS["running"] = True
    _PIPELINE_STATUS["last"] = None
    threading.Thread(target=target, daemon=True).start()


def retrain_async(data_path: str) -> None:
    import pathlib

    import pandas as pd

    from services.risk.app.train import train_best

    def job():
        df = pd.read_csv(data_path)
        best, results = train_best(df, pathlib.Path(settings.risk_model_path))
        return {"ok": True, "best_model": best, "results": results}

    _run_async(job)


def status() -> dict:
    return dict(_PIPELINE_STATUS)
