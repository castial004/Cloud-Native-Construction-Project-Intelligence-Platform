# Architecture Notes

## Data model (3 tiers)
- **Master:** `project`, `activity` (baselines, budgets, schedule bounds).
- **Time-series (append-only):** `progress_update` (PV/EV), `cost_record` (AC),
  `resource_record`.
- **Computed:** `kpi_result` (EVM), `risk_result` (delay probability).

## EVM evaluation
EVM is computed **as of a per-project status date** (midpoint of that project's
reporting window). This is required because the portfolio staggers projects over
time; a single global date would leave early projects complete (SPI saturated at
1.0). Activities not yet started as of the status date are skipped.

Formulas: CV=EV-AC, SV=EV-PV, CPI=EV/AC, SPI=EV/PV, EAC=BAC/CPI, TEAC=Dur/SPI.

## Delay-risk modeling
Binary target (paper Eq. 7): `y = 1 if (ActualFinish - PlannedFinish) > tau`.
Features: planned duration, total float, predecessor count, subcontractor delay
rate, criticality, SPI at mid-duration, SPI trend. Candidate models compared by
ROC-AUC; SVM (calibrated) selected. Reliability: a temperature-scaled softmax
surrogate of the CPM max operator locates the most probable failure point.

## Why synthetic data
The source CSVs in the repo had **zero label variance** (all rows one
performance class) and no activity/baseline structure, so neither genuine EVM nor
a valid classifier was possible. `datagen/` produces a valid activity-level
dataset with baselines and a non-degenerate delay label (seeded, reproducible).
