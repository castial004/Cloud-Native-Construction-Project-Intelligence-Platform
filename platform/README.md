# Cloud-Native Construction Project Intelligence Platform (CCPIP)

A reproducible, cloud-native platform that unifies construction project-control
data ingestion, PostgreSQL storage, Earned Value Management (EVM) analytics,
machine-learning delay-risk scoring, a web dashboard, and Power BI decision
support — packaged with Docker and orchestrated on Kubernetes.

## 🚀 Quick start (one command)

**Linux / macOS / Git Bash:**
```bash
./run.sh
```

**Windows (PowerShell):**
```powershell
.\run.ps1
```
See **[WINDOWS.md](WINDOWS.md)** for the full Windows guide.

That builds the image, starts the database + API + web UI, runs the full data
pipeline (generate → ingest → EVM → train → score → verify), and prints the URL:

**→ http://localhost:8080**

Stop everything with:
```bash
./run.sh down
```

Requirements: Docker + Docker Compose only.

## Web UI
| Page | What it shows |
|------|----------------|
| **Overview** | Budget, EV, AC, CPI, SPI, high-risk count; per-project charts |
| **Cost** | Cumulative actual-cost curve; top cost-overrun activities |
| **Schedule** | Planned-vs-earned S-curve; most-delayed activities |
| **Delay-Risk** | Delay-probability histogram; top-risk activities with badges |
| **Activities** | Filterable explorer (project / risk / trade / critical) |
| **Data & Actions** | CSV upload, **Recompute EVM + Risk**, **Retrain model** |

## Architecture
```
Project Data → Ingestion API → PostgreSQL → Analytics + Delay-Risk Service
             → Curated Views/API → Web UI / Power BI
```
| Layer | Tech |
|-------|------|
| Web UI | FastAPI, Jinja2, Chart.js |
| Ingestion | FastAPI, Pydantic (HTTP 422 on bad payloads) |
| Storage | PostgreSQL, SQLAlchemy, Alembic |
| Analytics | Pandas, NumPy (EVM: CV, SV, CPI, SPI, EAC, TEAC) |
| Risk | scikit-learn (RF / GB / SVM) + softmax/MPP reliability |
| Deployment | Docker, Kubernetes (HPA, health probes, persistent storage) |

## Configuration
Edit `.env` (created from `.env.example` on first run). All settings use the
`CCPIP_` prefix. Key knobs: `WEB_PORT`, `INGESTION_PORT`, `DB_PORT`,
`CCPIP_RANDOM_SEED`, `CCPIP_DELAY_THRESHOLD_DAYS`.

## Results (reproducible)
**Delay-risk classifiers (5-fold CV):**

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC |
|-------|----------|-----------|--------|----|---------|
| RandomForest | 0.880 | 0.704 | 0.805 | 0.746 | 0.955 |
| GradientBoosting | 0.903 | 0.820 | 0.713 | 0.762 | 0.943 |
| SVM (best) | 0.920 | 0.849 | 0.791 | 0.811 | 0.969 |

**EVM:** all KPI rows satisfy CV=EV-AC, SV=EV-PV, CPI=EV/AC, SPI=EV/PV.

## Development (without Docker)
```bash
make install       # create .venv + install
make db-up         # start Postgres
.venv/bin/python -m db.bootstrap    # migrate + views
make gen           # generate synthetic data
# run API:  .venv/bin/uvicorn services.ingestion.app.main:app --port 8000
make load evm train score
make web           # http://localhost:8080
make test          # unit tests
make bench         # reproduce Table II
```
`make help` lists every target.

## Kubernetes
See [k8s/README.md](k8s/README.md). Includes a self-healing demo (deleted pod
rescheduled in ~1s) and an HPA (2–6 replicas).

## Manual verification
See [VERIFY.md](VERIFY.md) for a step-by-step checklist.

## Windows
See **[WINDOWS.md](WINDOWS.md)** — complete step-by-step guide for Windows
(Docker Desktop setup, PowerShell commands, troubleshooting).

## Repository layout
```
common/     shared config + SQLAlchemy models
db/         Alembic migrations, bootstrap, curated views
datagen/    synthetic activity-level data generator + API loader
services/   web (UI), ingestion (FastAPI), analytics (EVM), risk (ML), pipeline
powerbi/    DAX measures, connect guide, view exporter
k8s/        Kubernetes manifests (kustomize)
eval/       E2E verification, EVM validation, model benchmark (Table II)
tests/      unit + validation tests
run.sh      one-command launcher
```
