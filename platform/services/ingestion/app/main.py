"""FastAPI ingestion service for the CCPIP platform.

Validates inbound JSON payloads against strict Pydantic schemas, rejecting
malformed data with HTTP 422 (Pydantic default). Persists normalized records
to PostgreSQL via SQLAlchemy.

Run:
    uvicorn services.ingestion.app.main:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import datetime as dt

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from common.db import get_session
from common.models import (
    Activity,
    CostRecord,
    ProgressUpdate,
    Project,
    ResourceRecord,
)
from services.ingestion.app.schemas import (
    ActivityIn,
    CostRecordIn,
    IngestResult,
    ProgressUpdateIn,
    ProjectIn,
    ResourceRecordIn,
)

app = FastAPI(
    title="CCPIP Ingestion Service",
    version="0.1.0",
    description="Validated ingestion of construction project-control records.",
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "ingestion", "time": dt.datetime.now(dt.timezone.utc).isoformat()}


@app.get("/ready")
def ready(session: Session = Depends(get_session)) -> dict:
    from sqlalchemy import text

    session.execute(text("SELECT 1"))
    return {"status": "ready"}


def _payload_to_dicts(items) -> list[dict]:
    return [i.model_dump() for i in items]


@app.post("/projects", response_model=IngestResult, status_code=201)
def ingest_projects(items: list[ProjectIn], session: Session = Depends(get_session)) -> IngestResult:
    if not items:
        raise HTTPException(status_code=422, detail="empty payload")
    rows = _payload_to_dicts(items)
    stmt = pg_insert(Project).values(rows)
    stmt = stmt.on_conflict_do_update(
        index_elements=[Project.project_id],
        set_={
            "name": stmt.excluded.name,
            "contractor": stmt.excluded.contractor,
            "budget_at_completion": stmt.excluded.budget_at_completion,
            "planned_start": stmt.excluded.planned_start,
            "planned_finish": stmt.excluded.planned_finish,
        },
    )
    session.execute(stmt)
    session.commit()
    return IngestResult(inserted=len(rows), rejected=0)


@app.post("/activities", response_model=IngestResult, status_code=201)
def ingest_activities(items: list[ActivityIn], session: Session = Depends(get_session)) -> IngestResult:
    if not items:
        raise HTTPException(status_code=422, detail="empty payload")
    rows = _payload_to_dicts(items)
    # Reject activities referencing unknown projects.
    project_ids = {r["project_id"] for r in rows}
    known = set(session.scalars(select(Project.project_id).where(Project.project_id.in_(project_ids))).all())
    missing = project_ids - known
    if missing:
        raise HTTPException(status_code=422, detail=f"unknown project_id(s): {sorted(missing)}")
    stmt = pg_insert(Activity).values(rows)
    stmt = stmt.on_conflict_do_update(
        index_elements=[Activity.activity_id],
        set_={
            "name": stmt.excluded.name,
            "budget": stmt.excluded.budget,
            "planned_start": stmt.excluded.planned_start,
            "planned_finish": stmt.excluded.planned_finish,
            "is_critical": stmt.excluded.is_critical,
        },
    )
    session.execute(stmt)
    session.commit()
    return IngestResult(inserted=len(rows), rejected=0)


@app.post("/progress", response_model=IngestResult, status_code=201)
def ingest_progress(items: list[ProgressUpdateIn], session: Session = Depends(get_session)) -> IngestResult:
    if not items:
        raise HTTPException(status_code=422, detail="empty payload")
    rows = _payload_to_dicts(items)
    activity_ids = {r["activity_id"] for r in rows}
    known = set(session.scalars(select(Activity.activity_id).where(Activity.activity_id.in_(activity_ids))).all())
    missing = activity_ids - known
    if missing:
        raise HTTPException(status_code=422, detail=f"unknown activity_id(s): {sorted(missing)}")
    stmt = pg_insert(ProgressUpdate).values(rows)
    stmt = stmt.on_conflict_do_update(
        constraint="uq_progress_activity_ts",
        set_={
            "percent_complete": stmt.excluded.percent_complete,
            "earned_value": stmt.excluded.earned_value,
            "planned_value": stmt.excluded.planned_value,
            "notes": stmt.excluded.notes,
        },
    )
    session.execute(stmt)
    session.commit()
    return IngestResult(inserted=len(rows), rejected=0)


@app.post("/costs", response_model=IngestResult, status_code=201)
def ingest_costs(items: list[CostRecordIn], session: Session = Depends(get_session)) -> IngestResult:
    if not items:
        raise HTTPException(status_code=422, detail="empty payload")
    rows = _payload_to_dicts(items)
    activity_ids = {r["activity_id"] for r in rows}
    known = set(session.scalars(select(Activity.activity_id).where(Activity.activity_id.in_(activity_ids))).all())
    missing = activity_ids - known
    if missing:
        raise HTTPException(status_code=422, detail=f"unknown activity_id(s): {sorted(missing)}")
    session.execute(pg_insert(CostRecord).values(rows))
    session.commit()
    return IngestResult(inserted=len(rows), rejected=0)


@app.post("/resources", response_model=IngestResult, status_code=201)
def ingest_resources(items: list[ResourceRecordIn], session: Session = Depends(get_session)) -> IngestResult:
    if not items:
        raise HTTPException(status_code=422, detail="empty payload")
    rows = _payload_to_dicts(items)
    activity_ids = {r["activity_id"] for r in rows}
    known = set(session.scalars(select(Activity.activity_id).where(Activity.activity_id.in_(activity_ids))).all())
    missing = activity_ids - known
    if missing:
        raise HTTPException(status_code=422, detail=f"unknown activity_id(s): {sorted(missing)}")
    session.execute(pg_insert(ResourceRecord).values(rows))
    session.commit()
    return IngestResult(inserted=len(rows), rejected=0)
