"""Delay-risk service tests: reliability formulation + model behaviour."""
from __future__ import annotations

import numpy as np

from services.risk.app.reliability import softmax, softmax_early_finish, most_probable_failure_point


def test_softmax_sums_to_one():
    x = np.array([1.0, 2.0, 3.0])
    s = softmax(x)
    assert np.isclose(s.sum(), 1.0)


def test_softmax_peaks_on_max():
    x = np.array([0.0, 10.0, 1.0])
    s = softmax(x, temperature=0.5)
    assert np.argmax(s) == 1


def test_softmax_early_finish_no_predecessors():
    ef = softmax_early_finish(np.array([]), duration=7.0)
    assert ef == 7.0


def test_softmax_early_finish_dominated_by_longest():
    preds = np.array([2.0, 20.0, 3.0])
    ef = softmax_early_finish(preds, duration=5.0, temperature=0.5)
    # With low temperature, result approaches max(preds)+duration = 25.
    assert 20.0 < ef <= 25.0


def test_most_probable_failure_point_chain():
    adj = {"A": ["B"], "B": ["C"], "C": []}
    durations = {"A": 3.0, "B": 4.0, "C": 5.0}
    ef = most_probable_failure_point(adj, durations, "A")
    assert set(ef.keys()) == {"A", "B", "C"}
    assert ef["A"] == 3.0
    assert ef["C"] > ef["A"]
