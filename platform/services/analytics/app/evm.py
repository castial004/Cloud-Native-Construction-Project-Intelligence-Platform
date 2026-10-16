"""Earned Value Management computations (IEEE paper Sec. V-A).

Formulas:
    CV   = EV - AC
    SV   = EV - PV
    CPI  = EV / AC
    SPI  = EV / PV
    EAC  = BAC / CPI
    TEAC = Planned Duration / SPI

All functions guard against division by zero and return None where an index is
undefined, so downstream consumers (DB, Power BI) never see NaN/inf.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EVMResult:
    pv: float
    ev: float
    ac: float
    cv: float
    sv: float
    cpi: float | None
    spi: float | None
    eac: float | None
    teac: float | None


def _safe_div(numerator: float, denominator: float) -> float | None:
    if denominator is None or abs(denominator) < 1e-12:
        return None
    return numerator / denominator


def compute_evm(
    pv: float,
    ev: float,
    ac: float,
    bac: float,
    planned_duration_days: float,
) -> EVMResult:
    """Compute the EVM indicator set for one activity as-of a point in time."""
    cv = ev - ac
    sv = ev - pv
    cpi = _safe_div(ev, ac)
    spi = _safe_div(ev, pv)
    eac = _safe_div(bac, cpi) if cpi is not None else None
    teac = _safe_div(planned_duration_days, spi) if spi is not None else None

    return EVMResult(
        pv=pv,
        ev=ev,
        ac=ac,
        cv=cv,
        sv=sv,
        cpi=cpi,
        spi=spi,
        eac=eac,
        teac=teac,
    )
