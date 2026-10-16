"""Reproduce Table II: classifier comparison for delay-risk prediction.

Regenerates the synthetic dataset (seeded -> reproducible), evaluates RF / GB /
SVM with stratified 5-fold CV, and writes both a machine-readable JSON and a
Markdown table for the paper.

Usage:
    python -m eval.benchmark_models --out eval/output
"""
from __future__ import annotations

import argparse
import json
import pathlib

import pandas as pd

from datagen.generate import generate, write_csvs
from services.risk.app.train import evaluate


def to_markdown(results: dict, best: str) -> str:
    lines = [
        "| Model | Accuracy | Precision | Recall | F1 | ROC-AUC |",
        "|-------|----------|-----------|--------|----|---------|",
    ]
    for name, m in results.items():
        star = " **(best)**" if name == best else ""
        lines.append(
            f"| {name}{star} | {m['accuracy']:.3f} | {m['precision']:.3f} | "
            f"{m['recall']:.3f} | {m['f1']:.3f} | {m['roc_auc']:.3f} |"
        )
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="eval/output")
    ap.add_argument("--data", default="datagen/out/risk_training.csv")
    ap.add_argument("--projects", type=int, default=6)
    ap.add_argument("--activities", type=int, default=50)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    data_path = pathlib.Path(args.data)
    if not data_path.exists():
        data = generate(args.projects, args.activities, args.seed, 2, 5.0)
        write_csvs(data, data_path.parent)

    df = pd.read_csv(data_path)
    results = evaluate(df)
    best = max(results, key=lambda k: results[k]["roc_auc"])

    (out / "table_ii.json").write_text(json.dumps({"best": best, "results": results}, indent=2))
    md = "# Table II. Predictive Delay-Risk Classification Performance\n\n" + to_markdown(results, best)
    (out / "table_ii.md").write_text(md + "\n")

    print(md)
    print(f"\nBest by ROC-AUC: {best}")
    print(f"Written: {out/'table_ii.json'}, {out/'table_ii.md'}")


if __name__ == "__main__":
    main()
