"""End-to-end pipeline runner: wait for DB -> bootstrap -> ingest -> EVM -> risk.

Used as the compose/k8s 'init' job so the whole flow is reproducible with one
command. Idempotent: re-running re-ingests (upsert) and recomputes outputs.

Usage:
    python -m services.pipeline --api http://ingestion:8000 --data /data
"""
from __future__ import annotations

import argparse
import pathlib
import time

import httpx
from sqlalchemy import create_engine, text

from common.config import settings
from db.bootstrap import apply_views, run_migrations
from datagen import load as dataload


def wait_for_db(timeout: int = 60) -> None:
    engine = create_engine(settings.database_url, future=True)
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with engine.connect() as c:
                c.execute(text("SELECT 1"))
            engine.dispose()
            return
        except Exception:
            time.sleep(2)
    raise RuntimeError("database did not become ready in time")


def wait_for_api(api: str, timeout: int = 60) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if httpx.get(f"{api}/health", timeout=3).status_code == 200:
                return
        except Exception:
            pass
        time.sleep(2)
    raise RuntimeError("ingestion API did not become ready in time")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--api", default="http://localhost:8000")
    ap.add_argument("--data", default="datagen/out")
    args = ap.parse_args()

    print("[1/5] waiting for database ...")
    wait_for_db()
    print("[2/5] running migrations + views ...")
    run_migrations()
    apply_views()

    data_dir = pathlib.Path(args.data)
    if not (data_dir / "project.csv").exists():
        print(f"      generating synthetic data into {data_dir} ...")
        from datagen.generate import generate, write_csvs

        write_csvs(generate(6, 50, settings.random_seed, 2, settings.delay_threshold_days), data_dir)

    print("[3/5] waiting for ingestion API ...")
    wait_for_api(args.api)
    print("[4/5] ingesting data ...")
    import sys

    sys.argv = ["load", "--in", str(data_dir), "--api", args.api]
    dataload.main()

    print("[5/5] computing EVM + risk scores ...")
    import pandas as pd

    from services.analytics.app.worker import run as run_evm
    from services.risk.app.score import run as run_risk
    from services.risk.app.train import train_best

    print(f"      EVM KPI rows: {run_evm()}")
    df = pd.read_csv(data_dir / "risk_training.csv")
    train_best(df, pathlib.Path(settings.risk_model_path))
    print(f"      risk scores: {run_risk()}")

    print("[verify] end-to-end consistency checks ...")
    from eval.verify_e2e import main as verify_main

    rc = verify_main()
    if rc != 0:
        raise SystemExit(rc)
    print("Pipeline complete.")


if __name__ == "__main__":
    main()
