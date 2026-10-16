# Power BI Connection Guide

The platform exposes **curated PostgreSQL views** purpose-built for reporting.
Power BI (Desktop or Service) connects to these; it is intentionally *not*
containerized (paper Sec. VI).

## Curated views
| View | Grain | Purpose |
|------|-------|---------|
| `v_project_summary`   | project | Portfolio KPIs: CPI, SPI, high-risk count |
| `v_activity_current`  | activity | Current EVM + latest risk score per activity |
| `v_progress_trend`    | activity × timestamp | Planned vs earned value over time |
| `v_cost_trend`        | activity × timestamp | Actual cost + cumulative cost |

## Option A — Direct PostgreSQL connection (recommended)
1. Power BI Desktop → **Get Data → PostgreSQL database**.
2. Server: `localhost:5432` (or the cluster service host), Database: `ccpip`.
3. Data connectivity: **Import** (DirectQuery also supported).
4. Credentials: Database → user `ccpip`, password `ccpip`.
5. Select the four views above.
6. Paste the measures from `DAX_measures.dax` into the model.

## Option B — Offline CSV import (no live DB)
Run the exporter to snapshot the views to CSV, then import those files:

```bash
python -m powerbi.export_views --out powerbi/exports
```

## Dashboard pages (paper Sec. VI)
1. **Executive Overview** — Total Budget, EV, AC, overall completion, CPI, SPI,
   High Risk Activities, projects needing attention.
2. **Cost Performance** — budget vs actual vs earned value, cost-variance trend,
   top cost-overrun activities.
3. **Schedule Performance** — planned vs actual progress, SV, SPI trend, delayed
   activities, critical/high-risk activity list.
4. **Delay-Risk View** — risk probability/score, risk category, top contributing
   features, early-warning time trend.
5. **Operational Health** — last-update timestamp, record counts, ingestion health.

## Slicers
WBS level, trade category, contractor/project — cross-filtering from portfolio to
activity level (paper Sec. VI).
