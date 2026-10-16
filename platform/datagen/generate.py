"""Synthetic activity-level construction dataset generator.

Produces a *valid* project-control dataset that the provided CSVs could not:
- master entities (projects, activities) with real baselines,
- append-only progress / cost / resource time series,
- enough structure to compute genuine EVM (PV, EV, AC -> CV/SV/CPI/SPI/EAC/TEAC),
- a non-degenerate binary delay label per Eq. (7) of the IEEE paper:
      y_i = 1 if (ActualFinish_i - PlannedFinish_i) > tau else 0

Deterministic: driven entirely by --seed.

Usage:
    python -m datagen.generate --out datagen/out
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import math
import pathlib

import numpy as np

TRADES = ["Concrete", "Steel", "MEP", "Electrical", "Finishing", "Earthworks", "Roofing"]
CONTRACTORS = ["AlphaBuild", "BetaCivil", "GammaWorks", "DeltaInfra", "EpsilonEng"]


def smoothstep(t: np.ndarray | float) -> np.ndarray | float:
    """S-curve progress shape on [0, 1]; clamped outside."""
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def _project_start(index: int) -> dt.datetime:
    # Stagger project starts by 3 weeks each, from 2023-01-02 (a Monday).
    return dt.datetime(2023, 1, 2, tzinfo=dt.timezone.utc) + dt.timedelta(weeks=3 * index)


def generate(
    n_projects: int,
    activities_per_project: int,
    seed: int,
    sample_days: int,
    delay_threshold_days: float,
) -> dict[str, list[dict]]:
    rng = np.random.default_rng(seed)

    projects: list[dict] = []
    activities: list[dict] = []
    progress_rows: list[dict] = []
    cost_rows: list[dict] = []
    resource_rows: list[dict] = []
    training_rows: list[dict] = []

    for p in range(n_projects):
        project_id = f"PRJ-{p + 1:03d}"
        p_start = _project_start(p)
        contractor = CONTRACTORS[rng.integers(len(CONTRACTORS))]

        project_activities = []
        # Lay activities across parallel tracks so the schedule overlaps
        # realistically (a project finishes in months, not years).
        n_tracks = 4
        track_cursor = [0.0] * n_tracks
        for a in range(activities_per_project):
            track = a % n_tracks
            activity_id = f"{project_id}-ACT-{a + 1:04d}"
            trade = TRADES[rng.integers(len(TRADES))]
            wbs = f"1.{a // 10 + 1}.{a % 10 + 1}"

            planned_duration = float(rng.integers(8, 36))           # 8..35 days
            budget = float(rng.uniform(20_000, 250_000))
            predecessor_count = int(rng.integers(0, 4))

            # Float and criticality: some activities are on the critical path.
            is_critical = bool(rng.random() < 0.30)
            total_float = 0.0 if is_critical else float(rng.uniform(1, 20))

            subcontractor_delay_rate = float(rng.beta(2, 6))        # skew low, 0..1

            planned_start = p_start + dt.timedelta(days=track_cursor[track])
            planned_finish = planned_start + dt.timedelta(days=planned_duration)

            project_activities.append(
                dict(
                    activity_id=activity_id,
                    project_id=project_id,
                    name=f"{trade} activity {a + 1}",
                    wbs_code=wbs,
                    trade_category=trade,
                    planned_start=planned_start,
                    planned_finish=planned_finish,
                    planned_duration_days=planned_duration,
                    budget=budget,
                    total_float_days=total_float,
                    predecessor_count=predecessor_count,
                    is_critical=is_critical,
                    subcontractor_delay_rate=subcontractor_delay_rate,
                )
            )
            # Advance this track's cursor; tracks run in parallel.
            track_cursor[track] += planned_duration * float(rng.uniform(0.9, 1.05))

        # ---- simulate each activity's execution -------------------------------- #
        for act in project_activities:
            D = act["planned_duration_days"]
            B = act["budget"]
            is_crit = act["is_critical"]
            float_d = act["total_float_days"]
            sub_rate = act["subcontractor_delay_rate"]
            preds = act["predecessor_count"]

            # Delay model: interpretable, feature-dependent, plus irreducible noise.
            expected_work_delay = (
                6.0 * sub_rate * (D / 30.0)
                + 2.0 * (1.0 if is_crit else 0.0)
                + 0.6 * preds
                - 0.4 * min(float_d, 10.0)
            )
            start_delay = max(0.0, float(rng.normal(0.5, 1.5)))
            work_delay = max(0.0, expected_work_delay + float(rng.normal(0.0, 2.0)))
            delay_days = start_delay + work_delay
            actual_finish_offset = D + delay_days

            # Cost performance: activity-level CPI around 1.0.
            cpi_act = float(np.clip(rng.normal(1.0, 0.10), 0.6, 1.6))

            label = int(delay_days > delay_threshold_days)

            # Sampled snapshots from start to actual finish (+ a tail at 100%).
            horizon = actual_finish_offset + 2
            n_steps = int(math.floor(horizon / sample_days)) + 1
            last_ac = 0.0
            snapshots: list[tuple[float, float, float, float]] = []  # t, pct, pv, ev, ac

            for k in range(n_steps + 1):
                t = k * sample_days
                # Planned progress by planned schedule.
                pct_planned = float(smoothstep(t / D)) if D > 0 else 1.0
                # Actual progress: starts after start_delay, finishes at actual_finish.
                if t <= start_delay:
                    pct_actual = 0.0
                elif t >= actual_finish_offset:
                    pct_actual = 1.0
                else:
                    pct_actual = float(
                        smoothstep((t - start_delay) / max(actual_finish_offset - start_delay, 1e-6))
                    )

                pv = B * pct_planned
                ev = B * pct_actual
                ac_cum = ev / cpi_act if cpi_act > 0 else ev
                ts = act["planned_start"] + dt.timedelta(days=float(t))

                progress_rows.append(
                    dict(
                        activity_id=act["activity_id"],
                        timestamp=ts.isoformat(),
                        percent_complete=round(pct_actual * 100.0, 4),
                        earned_value=round(ev, 4),
                        planned_value=round(pv, 4),
                    )
                )
                cost_rows.append(
                    dict(
                        activity_id=act["activity_id"],
                        timestamp=ts.isoformat(),
                        actual_cost=round(ac_cum - last_ac, 4),
                        committed_cost=round(B * 0.05, 4),
                    )
                )
                resource_rows.append(
                    dict(
                        activity_id=act["activity_id"],
                        timestamp=ts.isoformat(),
                        worker_count=int(max(1, rng.integers(3, 30))),
                        equipment_utilization=round(float(rng.uniform(40, 98)), 3),
                        material_usage_kg=round(float(rng.uniform(0, 1200)), 3),
                    )
                )
                last_ac = ac_cum
                snapshots.append((t, pct_actual, pv, ev, ac_cum))

            # ---- training features -------------------------------------------- #
            def spi_at(fraction: float) -> float:
                target = fraction * D
                best = min(snapshots, key=lambda s: abs(s[0] - target))
                _, _, pv, ev, _ = best
                return float(ev / pv) if pv > 1e-9 else 1.0

            spi_mid = spi_at(0.5)
            spi_late = spi_at(0.9)
            spi_trend = spi_late - spi_mid  # negative => schedule slipping

            training_rows.append(
                dict(
                    activity_id=act["activity_id"],
                    project_id=act["project_id"],
                    planned_duration_days=D,
                    total_float_days=float_d,
                    predecessor_count=preds,
                    subcontractor_delay_rate=round(sub_rate, 6),
                    is_critical=int(is_crit),
                    spi_mid=round(spi_mid, 6),
                    spi_trend=round(spi_trend, 6),
                    delay_days=round(delay_days, 4),
                    label=label,
                )
            )

        total_budget = sum(a["budget"] for a in project_activities)
        project_finish = max(a["planned_finish"] for a in project_activities)
        projects.append(
            dict(
                project_id=project_id,
                name=f"Project {p + 1}",
                contractor=contractor,
                budget_at_completion=round(total_budget, 4),
                planned_start=p_start.date().isoformat(),
                planned_finish=project_finish.date().isoformat(),
            )
        )
        activities.extend(project_activities)

    # Serialize master activities.
    act_out = []
    for a in activities:
        act_out.append(
            dict(
                activity_id=a["activity_id"],
                project_id=a["project_id"],
                name=a["name"],
                wbs_code=a["wbs_code"],
                trade_category=a["trade_category"],
                planned_start=a["planned_start"].date().isoformat(),
                planned_finish=a["planned_finish"].date().isoformat(),
                planned_duration_days=a["planned_duration_days"],
                budget=round(a["budget"], 4),
                total_float_days=a["total_float_days"],
                predecessor_count=a["predecessor_count"],
                is_critical=int(a["is_critical"]),
                subcontractor_delay_rate=round(a["subcontractor_delay_rate"], 6),
            )
        )

    return {
        "project": projects,
        "activity": act_out,
        "progress_update": progress_rows,
        "cost_record": cost_rows,
        "resource_record": resource_rows,
        "risk_training": training_rows,
    }


def write_csvs(data: dict[str, list[dict]], out_dir: pathlib.Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, rows in data.items():
        if not rows:
            continue
        path = out_dir / f"{name}.csv"
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate synthetic CCPIP dataset")
    ap.add_argument("--out", default="datagen/out")
    ap.add_argument("--projects", type=int, default=6)
    ap.add_argument("--activities", type=int, default=50)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--sample-days", type=int, default=2)
    ap.add_argument("--delay-threshold-days", type=float, default=5.0)
    args = ap.parse_args()

    data = generate(
        n_projects=args.projects,
        activities_per_project=args.activities,
        seed=args.seed,
        sample_days=args.sample_days,
        delay_threshold_days=args.delay_threshold_days,
    )
    write_csvs(data, pathlib.Path(args.out))

    labels = [r["label"] for r in data["risk_training"]]
    pos = sum(labels)
    print(f"projects           : {len(data['project'])}")
    print(f"activities         : {len(data['activity'])}")
    print(f"progress updates   : {len(data['progress_update'])}")
    print(f"cost records       : {len(data['cost_record'])}")
    print(f"resource records   : {len(data['resource_record'])}")
    print(f"delay labels (1/0) : {pos}/{len(labels) - pos}  (positive rate {pos/len(labels):.1%})")


if __name__ == "__main__":
    main()
