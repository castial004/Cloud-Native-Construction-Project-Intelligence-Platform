"""Load generated CSVs into the platform through the ingestion API.

Exercises the real FastAPI validation path (not a direct DB write), so malformed
data is rejected exactly as in production.

Usage:
    python -m datagen.load --in datagen/out --api http://localhost:8000 --batch 500
"""
from __future__ import annotations

import argparse
import csv
import pathlib

import httpx


def _read(path: pathlib.Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _batches(rows: list[dict], size: int):
    for i in range(0, len(rows), size):
        yield rows[i : i + size]


def post(endpoint: str, rows: list[dict], api: str, batch: int) -> tuple[int, int]:
    inserted = 0
    rejected = 0
    with httpx.Client(base_url=api, timeout=60.0) as client:
        for chunk in _batches(rows, batch):
            resp = client.post(endpoint, json=chunk)
            if resp.status_code >= 400:
                rejected += len(chunk)
                print(f"  ! {endpoint} -> {resp.status_code}: {resp.text[:200]}")
            else:
                inserted += resp.json().get("inserted", len(chunk))
    return inserted, rejected


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="in_dir", default="datagen/out")
    ap.add_argument("--api", default="http://localhost:8000")
    ap.add_argument("--batch", type=int, default=500)
    args = ap.parse_args()

    d = pathlib.Path(args.in_dir)
    order = [
        ("project.csv", "/projects"),
        ("activity.csv", "/activities"),
        ("progress_update.csv", "/progress"),
        ("cost_record.csv", "/costs"),
        ("resource_record.csv", "/resources"),
    ]
    total_ins = total_rej = 0
    for fname, endpoint in order:
        path = d / fname
        if not path.exists():
            print(f"skip missing {fname}")
            continue
        rows = _read(path)
        ins, rej = post(endpoint, rows, args.api, args.batch)
        total_ins += ins
        total_rej += rej
        print(f"{endpoint:12s} {ins:6d} inserted, {rej:4d} rejected  ({fname})")
    print(f"TOTAL: {total_ins} inserted, {total_rej} rejected")


if __name__ == "__main__":
    main()
