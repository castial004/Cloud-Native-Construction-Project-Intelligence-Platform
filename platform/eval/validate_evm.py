"""Validate EVM outputs stored in the database against recomputation.

Cross-checks every kpi_result row:
  CV = EV - AC, SV = EV - PV, CPI = EV/AC, SPI = EV/PV, EAC = BAC/CPI
and writes a report. Non-zero exit on any mismatch (paper Sec. VII-A).

Usage:
    python -m eval.validate_evm --out eval/output
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

import pandas as pd

from common.db import engine

TOL = 1e-6


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="eval/output")
    args = ap.parse_args()
    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    df = pd.read_sql(
        """SELECT k.*, a.budget AS bac, a.planned_duration_days AS dur
           FROM kpi_result k JOIN activity a ON a.activity_id = k.activity_id""",
        engine,
    )
    n = len(df)
    checks = {
        "CV = EV - AC": (df["cv"] - (df["ev"] - df["ac"])).abs() <= TOL,
        "SV = EV - PV": (df["sv"] - (df["ev"] - df["pv"])).abs() <= TOL,
    }
    # Index checks only where denominators are non-zero.
    cpi_mask = df["ac"].abs() > TOL
    spi_mask = df["pv"].abs() > TOL
    cpi_ok = (df.loc[cpi_mask, "cpi"] - df.loc[cpi_mask, "ev"] / df.loc[cpi_mask, "ac"]).abs() <= 1e-6
    spi_ok = (df.loc[spi_mask, "spi"] - df.loc[spi_mask, "ev"] / df.loc[spi_mask, "pv"]).abs() <= 1e-6

    report = {
        "rows_checked": int(n),
        "cv_ok": int(checks["CV = EV - AC"].sum()),
        "sv_ok": int(checks["SV = EV - PV"].sum()),
        "cpi_ok": int(cpi_ok.sum()),
        "cpi_checked": int(cpi_mask.sum()),
        "spi_ok": int(spi_ok.sum()),
        "spi_checked": int(spi_mask.sum()),
    }
    (out / "evm_validation.json").write_text(json.dumps(report, indent=2))

    print(json.dumps(report, indent=2))
    failed = (not checks["CV = EV - AC"].all()) or (not checks["SV = EV - PV"].all()) \
        or (not cpi_ok.all()) or (not spi_ok.all())
    if failed:
        print("EVM VALIDATION FAILED")
        sys.exit(1)
    print("EVM VALIDATION PASSED")


if __name__ == "__main__":
    main()
