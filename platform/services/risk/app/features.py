"""Feature extraction for the delay-risk model (IEEE paper Sec. V-B).

Training uses datagen/out/risk_training.csv. Production scoring derives the same
feature vector directly from the database (Activity master + ProgressUpdate
history) so training and inference stay consistent.

Feature vector:
    planned_duration_days, total_float_days, predecessor_count,
    subcontractor_delay_rate, is_critical, spi_mid, spi_trend
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from common.models import Activity, ProgressUpdate

FEATURE_NAMES = [
    "planned_duration_days",
    "total_float_days",
    "predecessor_count",
    "subcontractor_delay_rate",
    "is_critical",
    "spi_mid",
    "spi_trend",
]


def _spi_at(history: list[tuple[float, float, float]], target_day: float) -> float:
    """SPI = EV/PV at the snapshot closest to *target_day*.

    history: list of (day_offset, pv, ev) sorted by day_offset.
    """
    if not history:
        return 1.0
    best = min(history, key=lambda h: abs(h[0] - target_day))
    _, pv, ev = best
    if pv <= 1e-9:
        return 1.0
    return float(ev / pv)


def _history_for(session: Session, activity: Activity) -> list[tuple[float, float, float]]:
    rows = session.scalars(
        select(ProgressUpdate)
        .where(ProgressUpdate.activity_id == activity.activity_id)
        .order_by(ProgressUpdate.timestamp.asc())
    ).all()
    if not rows:
        return []
    start = rows[0].timestamp
    out = []
    for r in rows:
        day = (r.timestamp - start).total_seconds() / 86400.0
        out.append((day, float(r.planned_value), float(r.earned_value)))
    return out


def features_for_activity(session: Session, activity: Activity) -> dict:
    duration = float(activity.planned_duration_days)
    history = _history_for(session, activity)
    spi_mid = _spi_at(history, 0.5 * duration)
    spi_late = _spi_at(history, 0.9 * duration)
    return {
        "planned_duration_days": duration,
        "total_float_days": float(activity.total_float_days),
        "predecessor_count": int(activity.predecessor_count),
        "subcontractor_delay_rate": float(activity.subcontractor_delay_rate),
        "is_critical": int(activity.is_critical),
        "spi_mid": spi_mid,
        "spi_trend": spi_late - spi_mid,
    }


def build_feature_matrix(session: Session, project_id: str | None = None):
    stmt = select(Activity)
    if project_id:
        stmt = stmt.where(Activity.project_id == project_id)
    activities = list(session.scalars(stmt).all())
    rows = [(a, features_for_activity(session, a)) for a in activities]
    return rows
