# Manual Verification Guide

Follow these steps in order. Each has an **expected result** so you can confirm
the build works without trusting any summary.

### Easiest path — one command
Run the launcher; it builds everything, runs the full pipeline, and prints the
dashboard URL (http://localhost:8080). Stop it with `./run.sh down`.

    ./run.sh

Then jump to **section 9 (Web UI)** below, or follow the step-by-step levels.

Work from the platform directory:

\`\`\`bash
cd "/media/bruce-wayne/HASNAIN/VIT WORK/VA/Project/Cloud-Native-Construction-Project-Intelligence-Platform/platform"
\`\`\`

---

## 0. Toolchain check
\`\`\`bash
python3 --version        # 3.12.x
docker --version         # 29.x
docker compose version   # v5.x
kubectl version --client # v1.37.x
minikube version         # v1.39.x
\`\`\`

---

## 1. Inspect the codebase (no execution)
\`\`\`bash
find . -type f -not -path './.venv/*' -not -path '*/__pycache__/*' \
  -not -path './datagen/out/*' -not -path './eval/*' -not -path './powerbi/exports/*' | sort
\`\`\`
**Expected:** ~60 files across common/ db/ datagen/ services/ powerbi/ k8s/ eval/ tests/.

Key files to open:
- \`common/models.py\` — the 7-entity 3-tier schema
- \`db/views.sql\` — the 4 curated reporting views
- \`services/analytics/app/evm.py\` — the 6 EVM formulas
- \`services/risk/app/train.py\` — the 3 candidate classifiers
- \`k8s/\` — the Kubernetes manifests

---

## 2. Run the unit test suite (fastest, no infra needed)
\`\`\`bash
.venv/bin/pytest -q
\`\`\`
**Expected:** \`19 passed\` in a few seconds.
Tests cover: ingestion validation (HTTP 422), EVM formulas, risk reliability
softmax, generator reproducibility.

---

## 3. Reproduce the ML benchmark (Table II)
\`\`\`bash
.venv/bin/python -m eval.benchmark_models --out eval/output
cat eval/output/table_ii.md
\`\`\`
**Expected:** table with 3 models; **SVM best ~0.969 ROC-AUC**. Takes ~1–2 min.

---

## 4. Full local stack via Docker Compose
> This tears down any standalone Postgres on port 5432.

\`\`\`bash
docker compose up --abort-on-container-exit --exit-code-from pipeline
\`\`\`
**Expected final lines:**
\`\`\`
Row counts: {'project': 6, 'activity': 300, 'progress_update': 6337, ...}
E2E VERIFICATION PASSED
Pipeline complete.
\`\`\`
It exits on its own. Clean up with \`docker compose down -v\`.

What it does: starts Postgres → migrates → generates data → ingests via the
FastAPI service (expect **19,317 inserted, 0 rejected**) → computes EVM
(**154 rows**) → trains + scores risk (**300 rows**) → verifies consistency.

---

## 5. Kubernetes deployment (already running now)
\`\`\`bash
kubectl -n ccpip get pods
kubectl -n ccpip get hpa
kubectl -n ccpip logs job/ccpip-pipeline --tail=20
\`\`\`
**Expected:**
- \`db-0\` Running, 2 × \`ingestion\` Running, pipeline job \`Completed\`
- pipeline log ends with \`E2E VERIFICATION PASSED\`
- HPA target 2–6 replicas

### Self-healing demo
\`\`\`bash
kubectl -n ccpip delete pod -l app=ingestion --wait=false
watch kubectl -n ccpip get pods
\`\`\`
**Expected:** a replacement pod reaches Running in ~1s. Ctrl-C to stop watch.

---

## 6. Query the live database directly
\`\`\`bash
# forward the in-cluster Postgres to your machine
kubectl -n ccpip port-forward svc/db 15432:5432 &
# then query it (needs psql) or use python:
CCPIP_DATABASE_URL=postgresql+psycopg2://ccpip:ccpip@localhost:15432/ccpip \
  .venv/bin/python -m eval.validate_evm --out eval/output
\`\`\`
**Expected:** all counts equal, ends with \`EVM VALIDATION PASSED\`.
Stop the port-forward with \`pkill -f "port-forward svc/db"\`.

---

## 7. Inspect the Power BI artifacts
\`\`\`bash
# regenerate the CSV snapshots of the curated views
.venv/bin/python -m powerbi.export_views --out powerbi/exports
ls -la powerbi/exports/
head -2 powerbi/exports/v_project_summary.csv
\`\`\`
**Expected:** 4 CSVs (v_project_summary 6 rows, v_activity_current 300,
v_progress_trend 6337, v_cost_trend 6337).
Open \`powerbi/DAX_measures.dax\` and \`powerbi/CONNECT.md\` to see the
dashboard measures and connection steps.

---

## 8. Generated data sanity check
\`\`\`bash
.venv/bin/python - <<'PY'
import pandas as pd
df = pd.read_csv("datagen/out/risk_training.csv")
print("rows:", len(df))
print("label balance:", df["label"].value_counts().to_dict())
print(df[["planned_duration_days","subcontractor_delay_rate","spi_trend","label"]].describe().round(3))
PY
\`\`\`
**Expected:** 300 rows, both classes present (~22% positives), features varied.

---

## 9. Web UI
```bash
# bring up db + ingestion + web, then open the browser
docker compose up -d db ingestion web
# http://localhost:8080

# or run locally (needs a reachable DB):
CCPIP_DATABASE_URL=postgresql+psycopg2://ccpip:ccpip@localhost:5432/ccpip \
  .venv/bin/uvicorn services.web.app.main:app --port 8080
```
**Expected pages (all HTTP 200):** `/` `/cost` `/schedule` `/risk`
`/activities` `/data` `/health`. Charts render; risk page shows coloured
High/Medium/Low badges. On **Data & Actions** you can upload a CSV, click
**Recompute EVM + Risk**, and **Retrain model**.

Quick check without a browser:
```bash
for p in / /cost /schedule /risk /activities /data /health; do
  echo "$(curl -s -o /dev/null -w '%{http_code}' http://localhost:8080$p)  $p"
done
```

## 10. One-command re-run of everything
\`\`\`bash
make compose-up      # full pipeline
make bench           # Table II
make test            # unit tests
make k8s-up          # (re)deploy to Kubernetes
\`\`\`
\`make help\` lists all targets.
