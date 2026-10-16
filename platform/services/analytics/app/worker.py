"""Analytics worker: compute EVM indicators for every activity and persist KPIResult.

EVM is evaluated **as of a common status date** (textbook practice). PV/EV are
taken from the latest ProgressUpdate at or before the status date; AC is the
cumulative CostRecord up to that date. Activities not yet started as of the
status date are skipped (no meaningful EVM). This avoids the saturation artifact
where reporting each activity at its own completion trivially forces SPI -> 1.

Default status date = median timestamp of all progress updates (a reproducible
mid-project "today"). Override with --as-of.

Usage:
    python -m services.analytics.app.worker
    python -m services.analytics.app.worker --as-of 2023-01-20T00:00:00+00:00
    python -m services.analytics.app.worker --project PRJ-001
"""
from __future__ import annotations

import argparse
import datetime as dt

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from common.db import session_scope
from common.models import Activity, CostRecord, KPIResult, ProgressUpdate
from services.analytics.app.evm import compute_evm


def _project_status_date(session: Session, project_id: str) -> dt.datetime | None:
    """Per-project status date = midpoint of that project's reporting window.

    Projects in the portfolio are staggered over time, so a single global status
    date would leave early projects fully complete (SPI saturated at 1.0) and
    late projects unstarted. A per-project midpoint gives a meaningful
    mid-execution snapshot for every project.
    """
    lo, hi = session.execute(
        select(func.min(ProgressUpdate.timestamp), func.max(ProgressUpdate.timestamp))
        .join(Activity, Activity.activity_id == ProgressUpdate.activity_id)
        .where(Activity.project_id == project_id)
    ).one()
    if lo is None or hi is None:
        return None
    return lo + (hi - lo) / 2


def _asof_progress(session: Session, activity_id: str, status_date: dt.datetime) -> ProgressUpdate | None:
    return session.scalars(
        select(ProgressUpdate)
        .where(
            ProgressUpdate.activity_id == activity_id,
            ProgressUpdate.timestamp <= status_date,
        )
        .order_by(ProgressUpdate.timestamp.desc())
        .limit(1)
    ).first()


def _cumulative_ac(session: Session, activity_id: str, status_date: dt.datetime) -> float:
    total = session.scalar(
        select(func.coalesce(func.sum(CostRecord.actual_cost), 0.0)).where(
            CostRecord.activity_id == activity_id,
            CostRecord.timestamp <= status_date,
        )
    )
    return float(total or 0.0)


def compute_for_activity(session: Session, activity: Activity, status_date: dt.datetime) -> KPIResult | None:
    prog = _asof_progress(session, activity.activity_id, status_date)
    if prog is None:
        return None
    ac = _cumulative_ac(session, activity.activity_id, status_date)
    result = compute_evm(
        pv=float(prog.planned_value),
        ev=float(prog.earned_value),
        ac=ac,
        bac=float(activity.budget),
        planned_duration_days=float(activity.planned_duration_days),
    )
    return KPIResult(
        activity_id=activity.activity_id,
        project_id=activity.project_id,
        as_of=status_date,
        pv=result.pv,
        ev=result.ev,
        ac=result.ac,
        cv=result.cv,
        sv=result.sv,
        cpi=result.cpi,
        spi=result.spi,
        eac=result.eac,
        teac=result.teac,
    )


def run(project_id: str | None = None, as_of: dt.datetime | None = None) -> int:
    written = 0
    with session_scope() as session:
        if as_of is not None and as_of.tzinfo is None:
            as_of = as_of.replace(tzinfo=dt.timezone.utc)

        # Resolve the set of projects to process.
        proj_stmt = select(Activity.project_id).distinct()
        if project_id:
            proj_stmt = proj_stmt.where(Activity.project_id == project_id)
        project_ids = list(session.scalars(proj_stmt).all())

        for pid in project_ids:
            status_date = as_of or _project_status_date(session, pid)
            if status_date is None:
                continue
            activities = list(session.scalars(
                select(Activity).where(Activity.project_id == pid)
            ).all())
            for activity in activities:
                session.query(KPIResult).filter(
                    KPIResult.activity_id == activity.activity_id
                ).delete()
                kpi = compute_for_activity(session, activity, status_date)
                if kpi is not None:
                    session.add(kpi)
                    written += 1
    return written


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default=None)
    ap.add_argument("--as-of", default=None, help="ISO timestamp for the status date")
    args = ap.parse_args()
    as_of = dt.datetime.fromisoformat(args.as_of) if args.as_of else None
    n = run(args.project, as_of)
    print(f"EVM KPI rows written: {n}")


if __name__ == "__main__":
    main()
