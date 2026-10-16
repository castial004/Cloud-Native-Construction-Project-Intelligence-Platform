"""EVM correctness tests against hand-computed fixtures."""
from __future__ import annotations

import pytest

from services.analytics.app.evm import compute_evm


def test_standard_case():
    # PV=100, EV=90, AC=80, BAC=200, dur=20
    r = compute_evm(pv=100, ev=90, ac=80, bac=200, planned_duration_days=20)
    assert r.cv == pytest.approx(10)
    assert r.sv == pytest.approx(-10)
    assert r.cpi == pytest.approx(90 / 80)
    assert r.spi == pytest.approx(0.9)
    assert r.eac == pytest.approx(200 / (90 / 80))
    assert r.teac == pytest.approx(20 / 0.9)


def test_zero_ac_gives_none_cpi():
    r = compute_evm(pv=100, ev=50, ac=0, bac=200, planned_duration_days=10)
    assert r.cpi is None
    assert r.eac is None
    assert r.cv == pytest.approx(50)


def test_zero_pv_gives_none_spi():
    r = compute_evm(pv=0, ev=10, ac=10, bac=100, planned_duration_days=10)
    assert r.spi is None
    assert r.teac is None


def test_on_schedule_on_budget():
    r = compute_evm(pv=100, ev=100, ac=100, bac=100, planned_duration_days=10)
    assert r.cpi == pytest.approx(1.0)
    assert r.spi == pytest.approx(1.0)
    assert r.cv == pytest.approx(0)
    assert r.sv == pytest.approx(0)


def test_overrun_and_delay():
    r = compute_evm(pv=120, ev=100, ac=130, bac=1000, planned_duration_days=30)
    assert r.cpi is not None and r.cpi < 1  # over budget
    assert r.spi is not None and r.spi < 1  # behind schedule
    assert r.eac is not None and r.eac > 1000
