"""Score activities with the trained delay-risk model and persist RiskResult rows.

Uses the same feature vector as training (features.features_for_activity), maps
the predicted probability to a Low/Medium/High category, and records the model
version plus the most influential features.

Usage:
    python -m services.risk.app.score
    python -m services.risk.app.score --project PRJ-001
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib

import joblib
import numpy as np
from sqlalchemy.orm import Session

from common.config import settings
from common.db import session_scope
from common.models import RiskResult
from services.risk.app.features import FEATURE_NAMES, features_for_activity, build_feature_matrix


def _category(p: float) -> str:
    if p >= 0.66:
        return "High"
    if p >= 0.33:
        return "Medium"
    return "Low"


def load_model(path: str):
    p = pathlib.Path(path)
    if not p.exists():
        raise FileNotFoundError(
            f"model not found at {path}; run 'python -m services.risk.app.train' first"
        )
    return joblib.load(p)


def _top_features(model, feature_row: dict) -> str:
    """Approximate local feature importance via |value| * global importance."""
    clf = model.named_steps.get("clf", model)
    importances = getattr(clf, "feature_importances_", None)
    if importances is None:
        return json.dumps([])
    vals = np.array([feature_row[f] for f in FEATURE_NAMES], dtype=float)
    contrib = np.abs(vals) * importances
    order = np.argsort(contrib)[::-1][:3]
    return json.dumps([FEATURE_NAMES[i] for i in order])


def run(project_id: str | None = None) -> int:
    bundle = load_model(settings.risk_model_path)
    model = bundle["model"]
    version = bundle.get("version", settings.risk_model_version)

    written = 0
    with session_scope() as session:
        rows = build_feature_matrix(session, project_id)
        if not rows:
            return 0
        X = np.array([[feat[f] for f in FEATURE_NAMES] for _, feat in rows], dtype=float)
        probs = model.predict_proba(X)[:, 1]
        now = dt.datetime.now(dt.timezone.utc)
        for (activity, feat), prob in zip(rows, probs):
            session.query(RiskResult).filter(
                RiskResult.activity_id == activity.activity_id
            ).delete()
            session.add(
                RiskResult(
                    activity_id=activity.activity_id,
                    project_id=activity.project_id,
                    as_of=now,
                    delay_probability=float(prob),
                    risk_category=_category(float(prob)),
                    model_version=version,
                    top_features=_top_features(model, feat),
                )
            )
            written += 1
    return written


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default=None)
    args = ap.parse_args()
    n = run(args.project)
    print(f"Risk scores written: {n}")


if __name__ == "__main__":
    main()
