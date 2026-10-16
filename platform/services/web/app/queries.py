"""Read-only queries backing the web dashboard (curated views + tables)."""
from __future__ import annotations

import pandas as pd

from common.db import engine


def _df(sql: str, params: dict | None = None) -> pd.DataFrame:
    return pd.read_sql(sql, engine, params=params or {})


def project_summary() -> pd.DataFrame:
    return _df("SELECT * FROM v_project_summary ORDER BY project_id")


def activity_current(project_id: str | None = None,
                     risk: str | None = None,
                     trade: str | None = None,
                     critical_only: bool = False) -> pd.DataFrame:
    sql = "SELECT * FROM v_activity_current WHERE 1=1"
    params: dict = {}
    if project_id:
        sql += " AND project_id = %(project_id)s"
        params["project_id"] = project_id
    if risk:
        sql += " AND risk_category = %(risk)s"
        params["risk"] = risk
    if trade:
        sql += " AND trade_category = %(trade)s"
        params["trade"] = trade
    if critical_only:
        sql += " AND is_critical = TRUE"
    sql += " ORDER BY delay_probability DESC NULLS LAST"
    return _df(sql, params)


def overall_kpis() -> dict:
    df = _df("""
        SELECT
            COALESCE(SUM(ev),0) AS total_ev,
            COALESCE(SUM(ac),0) AS total_ac,
            COALESCE(SUM(pv),0) AS total_pv,
            COALESCE(SUM(budget),0) AS total_budget
        FROM v_activity_current
    """)
    risk = _df("""
        SELECT risk_category, COUNT(*) AS n
        FROM v_activity_current GROUP BY risk_category
    """)
    counts = {r["risk_category"]: int(r["n"]) for _, r in risk.iterrows()}
    r = df.iloc[0]
    ev, ac, pv, budget = float(r.total_ev), float(r.total_ac), float(r.total_pv), float(r.total_budget)
    return {
        "total_ev": ev, "total_ac": ac, "total_pv": pv, "total_budget": budget,
        "cpi": (ev / ac) if ac else None,
        "spi": (ev / pv) if pv else None,
        "cv": ev - ac,
        "sv": ev - pv,
        "eac": (budget / (ev / ac)) if ac and ev else None,
        "high_risk": counts.get("High", 0),
        "medium_risk": counts.get("Medium", 0),
        "low_risk": counts.get("Low", 0),
    }


def _daily_carry_forward(raw: pd.DataFrame, value_col: str) -> pd.Series:
    """Sum per-activity cumulative values across a daily grid, forward-filled.

    Each activity's snapshot is cumulative but only exists on report dates;
    between reports its last known value still holds. We pivot to one row per
    (day, activity), forward-fill within each activity, then sum across
    activities for each day.
    """
    if raw.empty:
        return pd.Series(dtype=float)
    raw = raw.copy()
    raw["day"] = pd.to_datetime(raw["day"])
    grid = pd.date_range(raw["day"].min(), raw["day"].max(), freq="D")
    wide = raw.pivot_table(index="day", columns="activity_id",
                           values=value_col, aggfunc="last")
    wide = wide.reindex(grid).ffill().fillna(0.0)
    return wide.sum(axis=1)


def progress_trend(project_id: str) -> pd.DataFrame:
    """Project-level planned vs earned value S-curve (cumulative, no double-count)."""
    raw = _df("""
        SELECT to_char(date_trunc('day', timestamp), 'YYYY-MM-DD') AS day,
               activity_id, planned_value AS pv, earned_value AS ev
        FROM v_progress_trend
        WHERE project_id = %(project_id)s
        ORDER BY timestamp
    """, {"project_id": project_id})
    if raw.empty:
        return pd.DataFrame(columns=["day", "pv", "ev"])
    raw["day"] = pd.to_datetime(raw["day"])
    pv = _daily_carry_forward(raw, "pv")
    ev = _daily_carry_forward(raw, "ev")
    out = pd.DataFrame({"day": pv.index.strftime("%Y-%m-%d"), "pv": pv.values, "ev": ev.values})
    # Keep the S-curve compact: one point per 3 days.
    return out.iloc[::3].reset_index(drop=True)


def cost_trend(project_id: str) -> pd.DataFrame:
    """Project-level cumulative actual cost (carried forward per activity)."""
    raw = _df("""
        SELECT to_char(date_trunc('day', timestamp), 'YYYY-MM-DD') AS day,
               activity_id, cumulative_actual_cost
        FROM v_cost_trend
        WHERE project_id = %(project_id)s
        ORDER BY timestamp
    """, {"project_id": project_id})
    if raw.empty:
        return pd.DataFrame(columns=["day", "ac_cum"])
    raw["day"] = pd.to_datetime(raw["day"])
    ac = _daily_carry_forward(raw, "cumulative_actual_cost")
    out = pd.DataFrame({"day": ac.index.strftime("%Y-%m-%d"), "ac_cum": ac.values})
    return out.iloc[::3].reset_index(drop=True)


def risk_histogram() -> pd.DataFrame:
    return _df("""
        SELECT width_bucket(delay_probability, 0, 1, 10) AS bucket,
               COUNT(*) AS n
        FROM v_activity_current
        GROUP BY 1 ORDER BY 1
    """)


def list_projects() -> list[str]:
    return list(_df("SELECT project_id FROM project ORDER BY project_id")["project_id"])


def list_trades() -> list[str]:
    return list(_df("SELECT DISTINCT trade_category FROM activity WHERE trade_category IS NOT NULL ORDER BY 1")["trade_category"])


def row_counts() -> dict:
    df = _df("""
        SELECT
          (SELECT COUNT(*) FROM project)         AS projects,
          (SELECT COUNT(*) FROM activity)        AS activities,
          (SELECT COUNT(*) FROM progress_update) AS progress,
          (SELECT COUNT(*) FROM cost_record)     AS costs,
          (SELECT COUNT(*) FROM kpi_result)      AS kpis,
          (SELECT COUNT(*) FROM risk_result)     AS risks
    """)
    return {k: int(v) for k, v in df.iloc[0].items()}
