# Cloud-Native Construction Project Intelligence Platform

A reproducible, cloud-native platform for construction project controls:
validated data ingestion, PostgreSQL storage, **Earned Value Management (EVM)**
analytics, **machine-learning delay-risk scoring**, an interactive **web
dashboard**, and **Power BI** decision support — packaged with Docker and
orchestrated on Kubernetes.

This repository contains both the **research material** (manuscripts, literature,
datasets) and the **working implementation** (`platform/`).

---

## 🚀 Quick start

```bash
cd platform
./run.sh
```

That single command builds the image, starts the database + API + web UI, runs
the full data pipeline, and prints the dashboard URL:

### → http://localhost:8080

Stop everything with `./run.sh down`. Requirements: **Docker + Docker Compose** only.

See **[platform/RUN_GUIDE.md](platform/RUN_GUIDE.md)** for the complete step-by-step guide.

---

## What's in the platform

| Layer | Component | Tech |
|-------|-----------|------|
| **Web UI** | Dashboards, activity explorer, data actions | FastAPI, Jinja2, Chart.js |
| **Ingestion** | Validated REST API (rejects bad data with HTTP 422) | FastAPI, Pydantic |
| **Storage** | 3-tier relational schema + curated reporting views | PostgreSQL, SQLAlchemy, Alembic |
| **Analytics** | EVM: CV, SV, CPI, SPI, EAC, TEAC | Pandas, NumPy |
| **Risk** | Delay-risk classifiers + softmax/MPP reliability | scikit-learn |
| **Decision support** | Dashboards + DAX measures | Power BI |
| **Deployment** | Containers, autoscaling, health probes | Docker, Kubernetes |

**Data flow:** Project Data → Ingestion API → PostgreSQL → Analytics + Delay-Risk Service → Curated Views → Web UI / Power BI

---

## Results (reproducible)

**Delay-risk classifiers (5-fold cross-validation):**

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC |
|-------|----------|-----------|--------|----|---------|
| RandomForest | 0.880 | 0.704 | 0.805 | 0.746 | 0.955 |
| GradientBoosting | 0.903 | 0.820 | 0.713 | 0.762 | 0.943 |
| SVM (best) | 0.920 | 0.849 | 0.791 | 0.811 | 0.969 |

**EVM correctness:** every KPI row satisfies CV = EV − AC, SV = EV − PV,
CPI = EV / AC, SPI = EV / PV.

---

## Repository layout

```
platform/           Working implementation
├── common/         shared config + SQLAlchemy models
├── db/             Alembic migrations, bootstrap, curated views
├── datagen/        synthetic activity-level data generator + API loader
├── services/       web (UI), ingestion, analytics (EVM), risk (ML), pipeline
├── powerbi/        DAX measures, connect guide, view exporter
├── k8s/            Kubernetes manifests (kustomize)
├── eval/           E2E verification, EVM validation, model benchmark
├── tests/          unit + validation tests
├── run.sh          one-command launcher
├── RUN_GUIDE.md    full run instructions
└── VERIFY.md       manual verification checklist

*.pdf, *.docx, *.pptx    Research manuscripts & literature
archive (2).zip          Source construction datasets
archive (3).zip          Cognitive-load survey responses
Project Performance Tracker PowerBI Template.pbit
```

---

## Documentation

- **[platform/RUN_GUIDE.md](platform/RUN_GUIDE.md)** — run it, step by step
- **[platform/README.md](platform/README.md)** — architecture & development
- **[platform/VERIFY.md](platform/VERIFY.md)** — verify every layer manually
- **[platform/k8s/README.md](platform/k8s/README.md)** — Kubernetes deployment
- **[platform/powerbi/CONNECT.md](platform/powerbi/CONNECT.md)** — Power BI setup

---

## Research context

Implements the architecture described in the manuscript
*"Cloud-Native Construction Project Intelligence Platform for Predictive
Delay-Risk Scoring and Real-Time Performance Analytics"* (`IEEE_Conference_Paper.docx`).

The platform addresses the gap identified across prior work: the absence of a
single, reproducible, scalable system that combines integrated construction data,
predictive project-control analytics, Power BI visualization, and cloud-native
orchestration.

### Note on the datasets
The bundled CSVs had **zero label variance** and no activity/baseline structure,
so they cannot support genuine EVM or a valid classifier. The platform therefore
ships a **seeded, reproducible activity-level generator** (`datagen/`) that
produces real baselines and a non-degenerate delay label. The original CSVs are
preserved and can be adapted as an alternative data source.
