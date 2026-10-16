"""Smoke tests: config prefix, DB module import, generator reproducibility."""
from __future__ import annotations

from datagen.generate import generate


def test_generator_reproducible():
    a = generate(1, 5, seed=7, sample_days=2, delay_threshold_days=5.0)
    b = generate(1, 5, seed=7, sample_days=2, delay_threshold_days=5.0)
    assert a["activity"] == b["activity"]
    assert len(a["activity"]) == 5


def test_generator_label_has_both_classes():
    # Over a larger sample the delay label must not be degenerate.
    d = generate(4, 40, seed=1, sample_days=3, delay_threshold_days=5.0)
    labels = {r["label"] for r in d["risk_training"]}
    assert labels == {0, 1}


def test_settings_prefix():
    from common.config import Settings

    s = Settings()
    assert isinstance(s.ingestion_port, int)
    assert s.database_url.startswith("postgresql")
