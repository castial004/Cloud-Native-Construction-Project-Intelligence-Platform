"""Train and evaluate candidate delay-risk classifiers (IEEE paper Sec. V-B, Table II).

Trains Random Forest, Gradient Boosting and SVM on the generated activity
features, evaluates with stratified cross-validation, picks the best by ROC-AUC,
and persists the chosen model to disk.

Usage:
    python -m services.risk.app.train --data datagen/out/risk_training.csv
"""
from __future__ import annotations

import argparse
import json
import pathlib

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from common.config import settings
from services.risk.app.features import FEATURE_NAMES

MODELS = {
    "RandomForest": Pipeline([
        ("clf", RandomForestClassifier(n_estimators=300, random_state=settings.random_seed,
                                       class_weight="balanced")),
    ]),
    "GradientBoosting": Pipeline([
        ("clf", GradientBoostingClassifier(random_state=settings.random_seed)),
    ]),
    "SVM": Pipeline([
        ("scaler", StandardScaler()),
        # CalibratedClassifierCV replaces the deprecated SVC(probability=True)
        # and yields well-calibrated probabilities for risk scoring.
        ("clf", CalibratedClassifierCV(
            SVC(kernel="rbf", class_weight="balanced", random_state=settings.random_seed),
            ensemble=False,
        )),
    ]),
}

SCORING = {"accuracy": "accuracy", "precision": "precision", "recall": "recall",
           "f1": "f1", "roc_auc": "roc_auc"}


def evaluate(df: pd.DataFrame) -> dict:
    X = df[FEATURE_NAMES].values
    y = df["label"].values
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=settings.random_seed)
    results = {}
    for name, model in MODELS.items():
        scores = cross_validate(model, X, y, cv=cv, scoring=SCORING, n_jobs=-1)
        results[name] = {
            "accuracy": float(np.mean(scores["test_accuracy"])),
            "precision": float(np.mean(scores["test_precision"])),
            "recall": float(np.mean(scores["test_recall"])),
            "f1": float(np.mean(scores["test_f1"])),
            "roc_auc": float(np.mean(scores["test_roc_auc"])),
            "f1_std": float(np.std(scores["test_f1"])),
            "roc_auc_std": float(np.std(scores["test_roc_auc"])),
        }
    return results


def train_best(df: pd.DataFrame, out_path: pathlib.Path) -> tuple[str, dict]:
    results = evaluate(df)
    best_name = max(results, key=lambda k: results[k]["roc_auc"])
    X = df[FEATURE_NAMES].values
    y = df["label"].values
    best_model = MODELS[best_name]
    best_model.fit(X, y)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": best_model, "features": FEATURE_NAMES,
                 "version": settings.risk_model_version}, out_path)
    return best_name, results


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="datagen/out/risk_training.csv")
    ap.add_argument("--out", default=settings.risk_model_path)
    args = ap.parse_args()

    df = pd.read_csv(args.data)
    best_name, results = train_best(df, pathlib.Path(args.out))

    print(f"{'model':<18}{'acc':>8}{'prec':>8}{'rec':>8}{'f1':>8}{'auc':>8}")
    for name, m in results.items():
        print(f"{name:<18}{m['accuracy']:>8.3f}{m['precision']:>8.3f}{m['recall']:>8.3f}"
              f"{m['f1']:>8.3f}{m['roc_auc']:>8.3f}")
    print(f"\nBest model by ROC-AUC: {best_name} -> saved to {args.out}")

    # Persist the comparison table for the paper / eval harness.
    metrics_path = pathlib.Path(args.out).parent / "metrics.json"
    metrics_path.write_text(json.dumps({"best": best_name, "results": results}, indent=2))
    print(f"Metrics written to {metrics_path}")


if __name__ == "__main__":
    main()
