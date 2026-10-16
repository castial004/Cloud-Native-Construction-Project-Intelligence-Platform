"""Web UI for the CCPIP platform (FastAPI + Jinja2 + Chart.js).

Pages:
  /                     Executive overview
  /cost                 Cost performance
  /schedule             Schedule performance
  /risk                 Delay-risk view
  /activities           Activity explorer (filters)
  /data                 Upload data + trigger pipeline actions
  /health               Liveness

Run:
  uvicorn services.web.app.main:app --host 0.0.0.0 --port 8080
"""
from __future__ import annotations

import pathlib

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from common.config import settings
from services.web.app import actions, queries

BASE = pathlib.Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE / "templates"))

app = FastAPI(title="CCPIP Web UI", version="0.1.0")
INGESTION_API = f"http://{settings.ingestion_host if settings.ingestion_host != '0.0.0.0' else 'localhost'}:{settings.ingestion_port}"
# In-cluster the ingestion service is reachable by name; allow override.
import os

INGESTION_API = os.environ.get("INGESTION_API", INGESTION_API)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "web"}


@app.get("/", response_class=HTMLResponse)
def overview(request: Request):
    kpis = queries.overall_kpis()
    projects = queries.project_summary().to_dict("records")
    counts = queries.row_counts()
    return templates.TemplateResponse(request, "overview.html", {
        "active": "overview",
        "kpis": kpis, "projects": projects, "counts": counts,
    })


@app.get("/cost", response_class=HTMLResponse)
def cost(request: Request, project: str | None = None):
    projects = queries.list_projects()
    project = project or (projects[0] if projects else None)
    trend = queries.cost_trend(project).to_dict("records") if project else []
    activities = queries.activity_current(project_id=project)
    top_over = activities.sort_values("cv").head(10)[
        ["activity_id", "activity_name", "budget", "ev", "ac", "cv", "cpi"]
    ].to_dict("records")
    return templates.TemplateResponse(request, "cost.html", {
        "active": "cost",
        "projects": projects, "project": project,
        "trend": trend, "top_over": top_over,
    })


@app.get("/schedule", response_class=HTMLResponse)
def schedule(request: Request, project: str | None = None):
    projects = queries.list_projects()
    project = project or (projects[0] if projects else None)
    trend = queries.progress_trend(project).to_dict("records") if project else []
    activities = queries.activity_current(project_id=project)
    delayed = activities.sort_values("spi").head(10)[
        ["activity_id", "activity_name", "pv", "ev", "sv", "spi", "is_critical"]
    ].to_dict("records")
    return templates.TemplateResponse(request, "schedule.html", {
        "active": "schedule",
        "projects": projects, "project": project,
        "trend": trend, "delayed": delayed,
    })


@app.get("/risk", response_class=HTMLResponse)
def risk(request: Request, project: str | None = None):
    projects = queries.list_projects()
    project = project or (projects[0] if projects else None)
    hist = queries.risk_histogram().to_dict("records")
    activities = queries.activity_current(project_id=project)
    top = activities.head(15)[
        ["activity_id", "activity_name", "trade_category", "delay_probability",
         "risk_category", "top_features", "is_critical"]
    ].to_dict("records")
    return templates.TemplateResponse(request, "risk.html", {
        "active": "risk",
        "projects": projects, "project": project,
        "hist": hist, "top": top,
    })


@app.get("/activities", response_class=HTMLResponse)
def activity_explorer(request: Request, project: str | None = None,
                      risk: str | None = None, trade: str | None = None,
                      critical: str | None = None):
    rows = queries.activity_current(
        project_id=project, risk=risk, trade=trade, critical_only=(critical == "1")
    )
    table = rows[[
        "project_id", "activity_id", "activity_name", "trade_category",
        "cpi", "spi", "delay_probability", "risk_category", "is_critical",
    ]].to_dict("records")
    return templates.TemplateResponse(request, "activities.html", {
        "active": "activities",
        "projects": queries.list_projects(),
        "trades": queries.list_trades(),
        "selected": {"project": project, "risk": risk, "trade": trade, "critical": critical},
        "rows": table, "total": len(table),
    })


@app.get("/data", response_class=HTMLResponse)
def data_page(request: Request):
    return templates.TemplateResponse(request, "data.html", {
        "active": "data",
        "counts": queries.row_counts(),
        "status": actions.status(),
    })


# ---- JSON action endpoints ------------------------------------------------- #
@app.post("/api/upload/{kind}")
async def upload(kind: str, file: UploadFile = File(...)):
    content = await file.read()
    result = actions.upload_csv(kind, content, INGESTION_API)
    return JSONResponse(result)


@app.post("/api/recompute")
def recompute():
    return JSONResponse(actions.recompute())


@app.post("/api/retrain")
def retrain(data_path: str = Form("datagen/out/risk_training.csv")):
    actions.retrain_async(data_path)
    return JSONResponse({"ok": True, "message": "retraining started"})


@app.get("/api/status")
def status():
    return JSONResponse(actions.status())
