"""Export curated views to CSV for offline Power BI import.

Usage:
    python -m powerbi.export_views --out powerbi/exports
"""
from __future__ import annotations

import argparse
import pathlib

import pandas as pd

from common.db import engine

VIEWS = ["v_project_summary", "v_activity_current", "v_progress_trend", "v_cost_trend"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="powerbi/exports")
    args = ap.parse_args()
    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    for view in VIEWS:
        df = pd.read_sql(f"SELECT * FROM {view}", engine)
        path = out / f"{view}.csv"
        df.to_csv(path, index=False)
        print(f"{view:22s} {len(df):6d} rows -> {path}")


if __name__ == "__main__":
    main()
