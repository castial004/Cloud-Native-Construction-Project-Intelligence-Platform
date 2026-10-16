# CCPIP on Windows — Complete Guide

How to run the Cloud-Native Construction Project Intelligence Platform on a
**Windows** machine, step by step.

Everything runs inside Docker, so you do **not** need Python, PostgreSQL, or any
other tool installed natively.

---

## 1. Install the prerequisites (once)

### 1.1 Docker Desktop
1. Download from https://www.docker.com/products/docker-desktop/
2. Run the installer and **enable WSL 2** when prompted
   (recommended backend; if not installed, Docker Desktop offers to install it).
3. Restart when asked.
4. Launch **Docker Desktop** and wait until the whale icon says
   **"Docker Desktop is running"**.

Verify in **PowerShell**:
```powershell
docker --version
docker compose version
```
You should see a Docker version and a Compose version (v2.x).

### 1.2 Git (to clone the repo)
Download from https://git-scm.com/download/win and install with defaults.
Verify:
```powershell
git --version
```

> **Tip — WSL 2 vs Linux containers:** Docker Desktop must be in **Linux
> containers** mode (the default). If you see "Switch to Linux containers" in
> the tray menu, click it.

---

## 2. Get the code

Open **PowerShell** and run:
```powershell
git clone https://github.com/castial004/Cloud-Native-Construction-Project-Intelligence-Platform.git
cd Cloud-Native-Construction-Project-Intelligence-Platform\platform
```

If you already have the folder, just:
```powershell
cd "path\to\Cloud-Native-Construction-Project-Intelligence-Platform\platform"
```

---

## 3. Start everything (ONE command)

```powershell
.\run.ps1
```

> **If you see an execution-policy error**, allow the script for this session:
> ```powershell
> Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
> ```
> Then run `.\run.ps1` again.

**What happens:**
1. Builds the Docker image (first run: ~3–5 minutes; later runs: seconds).
2. Starts PostgreSQL, the ingestion API, and the web UI.
3. Runs the pipeline: generate → ingest → EVM → train → score → verify.
4. Prints the dashboard URL.

**Expected final output:**
```
===================================================================
  CCPIP is running. Open the dashboard:

      http://localhost:8080

  Stop:  .\run.ps1 down
  Logs:  .\run.ps1 logs
===================================================================
```

---

## 4. Open the dashboard

In your browser (Edge, Chrome, Firefox) go to:

### http://localhost:8080

Pages: **Overview**, **Cost**, **Schedule**, **Delay-Risk**, **Activities**,
**Data & Actions**.

---

## 5. Everyday commands (PowerShell)

| Goal | Command |
|------|---------|
| Start everything | `.\run.ps1` |
| Stop everything | `.\run.ps1 down` |
| Watch logs | `.\run.ps1 logs` |
| Check services | `docker compose ps` |
| Re-run the pipeline | `docker compose up -d pipeline` |
| Fully reset | `docker compose down -v` |

---

## 6. If `run.ps1` is blocked: run the commands manually

You can always do exactly what the script does, by hand in PowerShell:

```powershell
# 0) go to the platform folder
cd "path\to\Cloud-Native-Construction-Project-Intelligence-Platform\platform"

# 1) create config from the template
Copy-Item .env.example .env

# 2) build the image (host networking avoids Docker DNS issues)
docker build --network=host -t platform-app:latest .

# 3) start database + API + web UI
docker compose up -d db ingestion web

# 4) run the full pipeline (generate -> ingest -> EVM -> train -> score)
docker compose up -d pipeline

# 5) wait for the pipeline to finish, then check its log
docker compose logs pipeline

# 6) open the dashboard
Start-Process "http://localhost:8080"
```

To stop:
```powershell
docker compose down -v
```

---

## 7. Configuration

On first run, `.env` is created from `.env.example`. Open it in Notepad to change:

```ini
WEB_PORT=8080                     # dashboard port
INGESTION_PORT=8000               # API port
DB_PORT=5432                      # database port
CCPIP_RANDOM_SEED=42              # change for a different dataset
CCPIP_DELAY_THRESHOLD_DAYS=5.0    # delay-label threshold
```

```powershell
notepad .env
```

Then re-run `.\run.ps1`.

---

## 8. Verify it works

```powershell
# All pages should return 200
"/", "/cost", "/schedule", "/risk", "/activities", "/data", "/health" | ForEach-Object {
    $code = (Invoke-WebRequest "http://localhost:8080$_" -UseBasicParsing).StatusCode
    Write-Host "$code  $_"
}

# Services should be healthy
docker compose ps

# Pipeline proof (ends with E2E VERIFICATION PASSED)
docker compose logs pipeline | Select-Object -Last 5
```

---

## 9. Troubleshooting (Windows)

| Problem | Cause | Fix |
|---------|-------|-----|
| `docker: command not found` | Docker Desktop not installed/started | Install & launch Docker Desktop |
| `error during connect` / cannot connect to daemon | Docker Desktop not running | Start Docker Desktop, wait for "running" |
| `.\run.ps1 : cannot be loaded because running scripts is disabled` | PowerShell execution policy | `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` |
| Port 8080 already in use | Another app on 8080 | Change `WEB_PORT=9090` in `.env` |
| Build fails with DNS / network errors | Docker DNS hiccup | Retry `.\run.ps1`; ensure Docker Desktop is updated |
| Browser shows nothing | Services still warming up | Wait ~30 s; run `.\run.ps1 logs` |
| Very slow first build | Downloading ~1 GB of images | Normal; subsequent runs are fast |
| `docker compose` unknown | Old standalone docker-compose | Update Docker Desktop (it bundles Compose v2) |

**Check Docker is in Linux-containers mode:** right-click the Docker tray icon →
if it says *"Switch to Windows containers…"*, you are already in Linux mode. If
it says *"Switch to Linux containers…"*, click it.

---

## 10. Optional: run on Kubernetes (Windows)

Requires `kubectl` and `minikube` (choco install minikube kubernetes-cli).

```powershell
minikube start --driver=docker
minikube docker-env | Invoke-Expression      # point docker at minikube's daemon
docker build -t platform-app:latest .
kubectl apply -k k8s/
kubectl -n ccpip get pods
kubectl -n ccpip logs job/ccpip-pipeline
kubectl -n ccpip port-forward svc/web 8080:8080
# open http://localhost:8080
```

---

## 11. Optional: run without Docker (native Python on Windows)

Needs Python 3.10+ and a PostgreSQL instance.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"

# point at your PostgreSQL (create the db first)
$env:CCPIP_DATABASE_URL = "postgresql+psycopg2://ccpip:ccpip@localhost:5432/ccpip"

python -m db.bootstrap            # schema + views
python -m datagen.generate --out datagen/out

# start the API in one terminal:
uvicorn services.ingestion.app.main:app --port 8000

# in another terminal:
python -m datagen.load --in datagen/out --api http://localhost:8000
python -m services.analytics.app.worker
python -m services.risk.app.train
python -m services.risk.app.score
uvicorn services.web.app.main:app --port 8080
# open http://localhost:8080
```

---

## Cheat sheet

```powershell
.\run.ps1              # start  ->  http://localhost:8080
.\run.ps1 logs         # watch logs
.\run.ps1 down         # stop + clean
```
