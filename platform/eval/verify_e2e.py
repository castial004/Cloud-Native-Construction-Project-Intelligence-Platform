"""End-to-end verification: assert the pipeline produced a consistent DB.

Checks (fail loudly -> non-zero exit so compose reports failure):
  1. Master + fact tables populated.
  2. KPI rows exist with sane EVM relationships (CV=EV-AC, SV=EV-PV).
  3. Risk rows exist with probabilities in [0,1] and valid categories.
  4. Curated views are queryable and non-empty.
"""
from __future__ import annotations

import sys

from sqlalchemy import text

from common.db import engine


def _scalar(conn, sql: str):
    return conn.execute(text(sql)).scalar()


def main() -> int:
    failures: list[str] = []
    with engine.connect() as conn:
        counts = {
            "project": _scalar(conn, "SELECT COUNT(*) FROM project"),
            "activity": _scalar(conn, "SELECT COUNT(*) FROM activity"),
            "progress_update": _scalar(conn, "SELECT COUNT(*) FROM progress_update"),
            "cost_record": _scalar(conn, "SELECT COUNT(*) FROM cost_record"),
            "kpi_result": _scalar(conn, "SELECT COUNT(*) FROM kpi_result"),
            "risk_result": _scalar(conn, "SELECT COUNT(*) FROM risk_result"),
        }
        print("Row counts:", counts)

        for table, n in counts.items():
            if not n:
                failures.append(f"{table} is empty")

        # EVM identity checks.
        bad_cv = _scalar(conn, "SELECT COUNT(*) FROM kpi_result WHERE ABS(cv - (ev - ac)) > 1e-6")
        bad_sv = _scalar(conn, "SELECT COUNT(*) FROM kpi_result WHERE ABS(sv - (ev - pv)) > 1e-6")
        if bad_cv:
            failures.append(f"{bad_cv} KPI rows violate CV = EV - AC")
        if bad_sv:
            failures.append(f"{bad_sv} KPI rows violate SV = EV - PV")

        # Risk sanity.
        bad_prob = _scalar(conn, "SELECT COUNT(*) FROM risk_result WHERE delay_probability < 0 OR delay_probability > 1")
        bad_cat = _scalar(conn, "SELECT COUNT(*) FROM risk_result WHERE risk_category NOT IN ('Low','Medium','High')")
        if bad_prob:
            failures.append(f"{bad_prob} risk rows have probability outside [0,1]")
        if bad_cat:
            failures.append(f"{bad_cat} risk rows have invalid category")

        # Curated views.
        for view in ["v_project_summary", "v_activity_current", "v_progress_trend", "v_cost_trend"]:
            n = _scalar(conn, f"SELECT COUNT(*) FROM {view}")
            print(f"  view {view:22s}: {n} rows")
            if not n:
                failures.append(f"view {view} is empty")

    if failures:
        print("\nE2E VERIFICATION FAILED:")
        for f in failures:
            print("  -", f)
        return 1
    print("\nE2E VERIFICATION PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
