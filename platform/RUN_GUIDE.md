# CCPIP — Complete Run Guide

A step-by-step guide to run the Cloud-Native Construction Project Intelligence
Platform from scratch. Written for a normal developer with no prior setup.

---

## 0. Prerequisites (install once)

| Tool | Why | Check |
|------|-----|-------|
| **Docker** | Runs the database, API, pipeline, and web UI | `docker --version` |
| **Docker Compose v2** | Orchestrates the containers | `docker compose version` |
| **Git** | Clone the repo | `git --version` |

That's it. Python, Node, and databases all run **inside Docker** — nothing else
to install.

> On Linux, make sure your user can run Docker without sudo:
> `sudo usermod -aG docker $USER` then log out and back in.

---

## 1. Open a terminal in the platform folder

```bash
cd "/media/bruce-wayne/HASNAIN/VIT WORK/VA/Project/Cloud-Native-Construction-Project-Intelligence-Platform/platform"
```

---

## 2. Start everything (ONE command)

**Linux / macOS / Git Bash:**
```bash
./run.sh
```

**Windows (PowerShell):**
```powershell
.\run.ps1
```
> If PowerShell blocks the script:
> `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`
> Full Windows guide: **[WINDOWS.md](WINDOWS.md)**.

**What happens:**
1. Builds the Docker image (first run: ~3–5 min; later runs: seconds).
2. Starts PostgreSQL, the ingestion API, and the web UI.
3. Runs the data pipeline: generate → ingest → EVM → train → score → verify.
4. Prints the dashboard URL.

**Expected final output:**
```
===================================================================
  CCPIP is running. Open the dashboard:

      http://localhost:8080

  Stop:  ./run.sh down
  Logs:  ./run.sh logs
===================================================================
```

---

## 3. Open the dashboard

In your browser go to:

### http://localhost:8080

You'll see these pages (top navigation):

| Page | What you can do |
|------|-----------------|
| **Overview** | Budget, Earned Value, Actual Cost, CPI, SPI, high-risk count; per-project charts |
| **Cost** | Cumulative actual-cost curve; top cost-overrun activities |
| **Schedule** | Planned-vs-earned S-curve; most-delayed activities |
| **Delay-Risk** | Delay-probability histogram; top-risk activities with High/Med/Low badges |
| **Activities** | Filter by project, risk, trade, critical-only |
| **Data & Actions** | Upload CSV, **Recompute EVM + Risk**, **Retrain model** |

---

## 4. Common operations

| Goal | Command |
|------|---------|
| Start everything | `./run.sh` |
| Stop everything (keeps nothing) | `./run.sh down` |
| Watch logs | `./run.sh logs` |
| Change the web port | edit `.env` → `WEB_PORT=9090`, then `./run.sh` |
| Re-run the pipeline | `docker compose up -d pipeline` |

---

## 5. Configuration

On first run, `.env` is auto-created from `.env.example`. Edit it to change:

```ini
WEB_PORT=8080               # dashboard port
INGESTION_PORT=8000         # API port
DB_PORT=5432                # database port
CCPIP_RANDOM_SEED=42        # change for a different synthetic dataset
CCPIP_DELAY_THRESHOLD_DAYS=5.0   # delay label threshold (tau)
```

After editing, just run `./run.sh` again.

---

## 6. Verify it works (optional)

```bash
# 1. All pages return HTTP 200
for p in / /cost /schedule /risk /activities /data /health; do
  echo "$(curl -s -o /dev/null -w '%{http_code}' http://localhost:8080$p)  $p"
done

# 2. Services healthy
docker compose ps

# 3. Pipeline proof
docker compose logs pipeline | tail -5     # ends: E2E VERIFICATION PASSED
```

---

## 7. Troubleshooting

**"docker: command not found"** → Install Docker.
**"Cannot connect to the Docker daemon"** → Start Docker Desktop / `sudo systemctl start docker`.
**Port 8080 already in use** → change `WEB_PORT` in `.env`.
**Build fails with "name resolution" / network error** → rare; re-run `./run.sh`. The build uses host networking to avoid Docker DNS issues.
**Nothing on http://localhost:8080** → run `./run.sh logs`, wait ~30s after the banner (services warm up).
**Want a totally clean slate** → `./run.sh down` (removes containers + database volume).

---

## 8. What the pipeline does (under the hood)

```
Synthetic data generator
        │
        ▼
Ingestion API (FastAPI, validates every record; rejects bad data with HTTP 422)
        │
        ▼
PostgreSQL  ──►  EVM Analytics (CV, SV, CPI, SPI, EAC, TEAC)
        │        └─►  Delay-Risk ML (RandomForest / GradientBoosting / SVM)
        ▼
Curated views  ──►  Web UI  +  Power BI
```

---

## 9. Advanced: run on Kubernetes (optional)

Requires `kubectl` + `minikube`.

```bash
minikube start --driver=docker
# build the image inside minikube's daemon
eval $(minikube docker-env)
docker build -t platform-app:latest .
# deploy
kubectl apply -k k8s/
# watch
kubectl -n ccpip get pods
kubectl -n ccpip logs job/ccpip-pipeline
# access the UI
kubectl -n ccpip port-forward svc/web 8080:8080
```

See `k8s/README.md` for details (self-healing demo, autoscaling).

---

## 10. Advanced: run without Docker (dev mode)

Needs Python 3.10+.

```bash
make install           # create .venv + install deps
make db-up             # start PostgreSQL container
.venv/bin/python -m db.bootstrap     # create schema + views
make gen               # generate synthetic data
# start the API in one terminal:
.venv/bin/uvicorn services.ingestion.app.main:app --port 8000
# in another terminal:
make load              # load data through the API
make evm train score   # analytics + ML
make web               # http://localhost:8080
```

`make help` lists every available target.

---

## Cheat sheet

**Linux / macOS / Git Bash:**
```bash
./run.sh              # start  →  http://localhost:8080
./run.sh logs         # watch logs
./run.sh down         # stop + clean
```

**Windows (PowerShell):**
```powershell
.\run.ps1             # start  →  http://localhost:8080
.\run.ps1 logs        # watch logs
.\run.ps1 down        # stop + clean
```

See **[WINDOWS.md](WINDOWS.md)** for the full Windows walkthrough.
