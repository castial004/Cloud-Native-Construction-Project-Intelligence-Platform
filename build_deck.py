"""Generate project-final.pptx — the final-year project presentation for CCPIP.

Reproducible: run with the platform venv (python-pptx installed).
    platform/.venv/bin/python build_deck.py

Prerequisites for screenshot slides:
    - platform running:  platform/run.sh
    - screenshots captured into docs/screenshots/  (see docs/screenshots/README)
"""
from __future__ import annotations

import os

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

# ---------------------------------------------------------------- theme ----
BG = RGBColor(0x0F, 0x17, 0x2A)
PANEL = RGBColor(0x1E, 0x29, 0x3B)
PANEL2 = RGBColor(0x16, 0x20, 0x33)
LINE = RGBColor(0x33, 0x41, 0x55)
TEXT = RGBColor(0xE2, 0xE8, 0xF0)
MUTED = RGBColor(0x94, 0xA3, 0xB8)
ACCENT = RGBColor(0x38, 0xBD, 0xF8)
ACCENT_DK = RGBColor(0x0B, 0x4F, 0x6C)
GOOD = RGBColor(0x22, 0xC5, 0x5E)
WARN = RGBColor(0xF5, 0x9E, 0x0B)
BAD = RGBColor(0xEF, 0x44, 0x44)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

FONT = "Calibri"
FONT_H = "Calibri"

SHOT_DIR = "docs/screenshots"

TEAM = [
    ("Hasnain Makada", "26MML0031"),
    ("Sahil Mall", "26MML0049"),
    ("Aryan Kishor Sao", "26MML0046"),
]

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]
SW = 13.333
SH = 7.5


# ------------------------------------------------------------- helpers ----
def new_slide():
    s = prs.slides.add_slide(BLANK)
    s.background.fill.solid()
    s.background.fill.fore_color.rgb = BG
    return s


def box(slide, l, t, w, h, fill=PANEL, line=LINE, shape=MSO_SHAPE.RECTANGLE, radius=None):
    sp = slide.shapes.add_shape(shape, Inches(l), Inches(t), Inches(w), Inches(h))
    sp.shadow.inherit = False
    if fill is None:
        sp.fill.background()
    else:
        sp.fill.solid()
        sp.fill.fore_color.rgb = fill
    if line is None:
        sp.line.fill.background()
    else:
        sp.line.color.rgb = line
        sp.line.width = Pt(1)
    if radius is not None and shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        try:
            sp.adjustments[0] = radius
        except Exception:
            pass
    return sp


def text(slide, l, t, w, h, s, size=16, color=TEXT, bold=False, align=PP_ALIGN.LEFT,
         anchor=MSO_ANCHOR.TOP, font=FONT, italic=False, spacing=None):
    tb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = Emu(0)
    tf.margin_right = Emu(0)
    tf.margin_top = Emu(0)
    tf.margin_bottom = Emu(0)
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = s
    f = run.font
    f.name = font
    f.size = Pt(size)
    f.bold = bold
    f.italic = italic
    f.color.rgb = color
    if spacing is not None:
        try:
            run._r.get_or_add_rPr().set("spc", str(int(spacing * 100)))
        except Exception:
            pass
    return tb


def fit_text(shape, s, size=12, color=TEXT, bold=False, align=PP_ALIGN.LEFT,
             anchor=MSO_ANCHOR.MIDDLE, font=FONT):
    tf = shape.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = Inches(0.08)
    tf.margin_right = Inches(0.08)
    tf.margin_top = Inches(0.03)
    tf.margin_bottom = Inches(0.03)
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = s
    run.font.name = font
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    return shape


def bullets(slide, items, l, t, w, h, size=16, color=TEXT):
    tb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    first = True
    for item in items:
        if isinstance(item, tuple):
            a, b = item
            level, s = (a, b) if isinstance(a, int) else (b, a)
        else:
            level, s = 0, item
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.level = level
        p.space_after = Pt(7 if level == 0 else 3)
        bullet = "•  " if level == 0 else "–  "
        run = p.add_run()
        run.text = bullet + s
        run.font.name = FONT
        run.font.size = Pt(size if level == 0 else size - 3)
        run.font.color.rgb = color if level == 0 else MUTED
    return tb


def header(slide, eyebrow, title):
    text(slide, 0.7, 0.48, 12, 0.34, eyebrow.upper(), size=12, color=ACCENT, bold=True, spacing=1.5)
    text(slide, 0.7, 0.82, 12.0, 0.8, title, size=29, color=WHITE, bold=True, font=FONT_H)
    box(slide, 0.72, 1.62, 1.15, 0.06, fill=ACCENT, line=None)


def footer(slide, n, label="CCPIP — Final-Year Project"):
    text(slide, 0.7, 7.02, 7, 0.3, label, size=9, color=MUTED)
    text(slide, 11.9, 7.02, 0.8, 0.3, f"{n:02d}", size=9, color=MUTED, align=PP_ALIGN.RIGHT)


def table(slide, rows, l, t, col_w, font=11, row_h=0.42, header_fill=ACCENT_DK,
          first_col_bold=False):
    nrows, ncols = len(rows), len(rows[0])
    total_w = sum(col_w)
    shp = slide.shapes.add_table(nrows, ncols, Inches(l), Inches(t),
                                 Inches(total_w), Inches(row_h * nrows))
    tbl = shp.table
    for i, cw in enumerate(col_w):
        tbl.columns[i].width = Inches(cw)
    for r in range(nrows):
        tbl.rows[r].height = Inches(row_h)
        for c in range(ncols):
            cell = tbl.cell(r, c)
            cell.margin_left = Inches(0.09)
            cell.margin_right = Inches(0.06)
            cell.margin_top = Inches(0.02)
            cell.margin_bottom = Inches(0.02)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.fill.solid()
            if r == 0:
                cell.fill.fore_color.rgb = header_fill
            else:
                cell.fill.fore_color.rgb = PANEL if r % 2 else PANEL2
            tf = cell.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            run = p.add_run()
            run.text = str(rows[r][c])
            run.font.name = FONT
            run.font.size = Pt(font)
            run.font.bold = (r == 0) or (first_col_bold and c == 0)
            run.font.color.rgb = WHITE if r == 0 else TEXT
    return tbl


def chip(slide, l, t, w, h, title, body, accent=ACCENT):
    box(slide, l, t, w, h, fill=PANEL, line=LINE, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.08)
    box(slide, l, t, 0.06, h, fill=accent, line=None)
    text(slide, l + 0.18, t + 0.12, w - 0.3, 0.3, title, size=13, color=WHITE, bold=True)
    text(slide, l + 0.18, t + 0.44, w - 0.3, h - 0.5, body, size=10.5, color=MUTED)


def arrow(slide, l, t, w=0.32, h=0.28, color=ACCENT):
    return box(slide, l, t, w, h, fill=color, line=None, shape=MSO_SHAPE.RIGHT_ARROW)


def screenshot(slide, name, l, t, w, caption=None):
    """Place a screenshot preserving its 16:10 aspect ratio, framed."""
    path = os.path.join(SHOT_DIR, name)
    if not os.path.exists(path):
        box(slide, l, t, w, w / 1.6, fill=PANEL2, line=LINE, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
        text(slide, l + 0.3, t + 0.3, w - 0.6, 0.5, f"[missing: {name}]", size=12, color=MUTED)
        return w / 1.6
    h = w / 1.6
    box(slide, l - 0.04, t - 0.04, w + 0.08, h + 0.08, fill=None, line=LINE,
        shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.02)
    slide.shapes.add_picture(path, Inches(l), Inches(t), Inches(w), Inches(h))
    if caption:
        text(slide, l, t + h + 0.1, w, 0.3, caption, size=10, color=MUTED, italic=True)
    return h


def feature_panel(slide, l, t, w, h, title, items, accent=ACCENT):
    box(slide, l, t, w, h, fill=PANEL2, line=LINE, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.04)
    box(slide, l, t, w, 0.08, fill=accent, line=None)
    text(slide, l + 0.22, t + 0.22, w - 0.4, 0.35, title, size=13, color=WHITE, bold=True, spacing=0.5)
    y = t + 0.72
    for it in items:
        text(slide, l + 0.22, y, 0.25, 0.3, "▸", size=11, color=accent, bold=True)
        tb = text(slide, l + 0.5, y, w - 0.7, 0.7, it, size=10.3, color=TEXT)
        y += 0.62


# =============================================================== SLIDE 1 ==
s = new_slide()
box(s, 0, 0, SW, 0.16, fill=ACCENT, line=None)
text(s, 0.9, 0.7, 11, 0.4, "FINAL-YEAR PROJECT  •  VISUAL ANALYTICS", size=14, color=ACCENT, bold=True, spacing=2)
text(s, 0.9, 1.4, 11.6, 1.5,
     "Cloud-Native Construction Project\nIntelligence Platform",
     size=42, color=WHITE, bold=True, font=FONT_H)
text(s, 0.9, 3.15, 11.6, 0.8,
     "Predictive Delay-Risk Scoring & Real-Time Performance Analytics",
     size=21, color=MUTED)
box(s, 0.92, 4.12, 1.6, 0.06, fill=ACCENT, line=None)

text(s, 0.9, 4.4, 6, 0.35, "TEAM", size=11, color=ACCENT, bold=True, spacing=1.5)
tx = 0.9
for name, roll in TEAM:
    text(s, tx, 4.72, 4.0, 0.35, name, size=15, color=WHITE, bold=True)
    text(s, tx, 5.06, 4.0, 0.3, roll, size=11, color=MUTED)
    tx += 4.05
text(s, 0.9, 5.55, 11.6, 0.35, "Dept. of Computer Science & Engineering  ·  Bhilai Institute of Technology, Durg",
     size=11, color=MUTED)

techs = ["FastAPI", "PostgreSQL", "scikit-learn", "Power BI", "Docker", "Kubernetes"]
x = 0.9
for tch in techs:
    w = 0.28 + len(tch) * 0.105
    b = box(s, x, 6.15, w, 0.4, fill=PANEL, line=LINE, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.5)
    fit_text(b, tch, size=11, color=ACCENT, bold=True, align=PP_ALIGN.CENTER)
    x += w + 0.15

# =============================================================== SLIDE 2 ==
s = new_slide()
header(s, "Team", "Project Team")
for i, (name, roll) in enumerate(TEAM):
    cx = 0.7 + i * 4.05
    box(s, cx, 2.1, 3.85, 3.5, fill=PANEL, line=LINE, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.06)
    box(s, cx, 2.1, 3.85, 0.1, fill=[ACCENT, GOOD, WARN][i], line=None)
    # avatar circle with initials
    initials = "".join(p[0] for p in name.split()[:2])
    av = box(s, cx + 1.42, 2.45, 1.0, 1.0, fill=PANEL2, line=[ACCENT, GOOD, WARN][i],
             shape=MSO_SHAPE.OVAL)
    fit_text(av, initials, size=22, color=WHITE, bold=True, align=PP_ALIGN.CENTER)
    text(s, cx + 0.2, 3.65, 3.45, 0.4, name, size=16, color=WHITE, bold=True, align=PP_ALIGN.CENTER)
    text(s, cx + 0.2, 4.05, 3.45, 0.3, roll, size=12, color=MUTED, align=PP_ALIGN.CENTER)

box(s, 0.7, 5.85, 11.95, 0.95, fill=PANEL2, line=ACCENT, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.12)
text(s, 0.95, 5.98, 11.5, 0.7,
     "The project spans data engineering, analytics, machine learning, "
     "visualization, and cloud-native deployment — delivered as one integrated system.",
     size=12.5, color=TEXT, anchor=MSO_ANCHOR.MIDDLE)
footer(s, 2)

# =============================================================== SLIDE 3 ==
s = new_slide()
header(s, "Overview", "Agenda")
agenda = [
    ("01", "Introduction & Motivation", "Why construction control needs a deployable platform"),
    ("02", "Problem Definition", "Fragmentation, retrospection, and the analytics–deployment gap"),
    ("03", "Literature Review", "What prior work covers — and leaves open"),
    ("04", "Research Gap & Objectives", "The missing link and the seven objectives"),
    ("05", "System Architecture", "Ingestion → storage → analytics → visualization"),
    ("06", "Data Model & Implementation", "Schema, EVM, ML risk, web UI, Power BI"),
    ("07", "Live Platform Walkthrough", "Screenshots of the working dashboard"),
    ("08", "Deployment & Results", "Kubernetes, benchmarks, validation"),
    ("09", "Conclusion & Future Work", "Contributions and next steps"),
]
col_x = [0.7, 6.9]
for i, (num, title, sub) in enumerate(agenda):
    cx = col_x[i // 5]
    cy = 1.95 + (i % 5) * 1.0
    text(s, cx, cy, 0.9, 0.6, num, size=24, color=ACCENT, bold=True, font=FONT_H)
    text(s, cx + 0.8, cy + 0.02, 5.2, 0.35, title, size=14, color=WHITE, bold=True)
    text(s, cx + 0.8, cy + 0.38, 5.2, 0.45, sub, size=10.5, color=MUTED)
footer(s, 3)

# =============================================================== SLIDE 4 ==
s = new_slide()
header(s, "01 — Introduction", "Motivation")
bullets(s, [
    "Construction project control depends on the triple constraint: schedule, cost, and scope.",
    "Despite tools like Primavera P6 and MS Project, cost overruns and schedule slippage remain endemic.",
    "A root cause is delayed visibility: progress and cost data are collected through manual site logs, spreadsheets, and disconnected subcontractor reports.",
    ("Variances are identified only at periodic commercial meetings — long after corrective action could help.", 1),
    "Industry 4.0 (BIM, IoT, QR capture) and BI dashboards (Power BI) show value individually, but remain siloed.",
    ("The need: continuous, evidence-based monitoring — not retrospective reporting.", 1),
], 0.7, 2.0, 11.9, 4.4, size=16)

chip(s, 0.7, 5.95, 3.8, 0.85, "Triple Constraint", "Schedule · Cost · Scope tracked together", ACCENT)
chip(s, 4.75, 5.95, 3.8, 0.85, "Delayed Visibility", "Data fragmented and reported late", WARN)
chip(s, 8.8, 5.95, 3.85, 0.85, "Our Aim", "Continuous, predictive project control", GOOD)
footer(s, 4)

# =============================================================== SLIDE 5 ==
s = new_slide()
header(s, "01 — Problem", "Three Systemic Deficiencies")
cards = [
    ("1. Data Fragmentation & Latency",
     "Site records, cost sheets, and baselines live in siloed applications with no unified schema. Teams manually rebuild reporting models every cycle.", WARN),
    ("2. Retrospective, Not Predictive",
     "CPI and SPI describe historical performance. They offer no probabilistic forecast to warn of activity-level delay before the critical path slips.", BAD),
    ("3. Analytics Disconnected from Deployment",
     "Advanced predictive models exist as isolated research scripts — not reproducible, containerized, auto-scaling systems.", ACCENT),
]
x = 0.7
for title, body, col in cards:
    box(s, x, 2.1, 3.9, 3.2, fill=PANEL, line=LINE, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.06)
    box(s, x, 2.1, 3.9, 0.1, fill=col, line=None)
    text(s, x + 0.25, 2.4, 3.4, 0.8, title, size=16, color=WHITE, bold=True)
    text(s, x + 0.25, 3.25, 3.4, 1.9, body, size=12.5, color=MUTED)
    x += 4.1
box(s, 0.7, 5.65, 11.95, 1.05, fill=PANEL2, line=ACCENT, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.12)
text(s, 1.0, 5.82, 11.35, 0.75,
     "Consequence: schedule and cost variances are discovered too late for preventive "
     "intervention — and there is no single reproducible system to fix it.",
     size=14, color=TEXT, anchor=MSO_ANCHOR.MIDDLE)
footer(s, 5)

# =============================================================== SLIDE 6 ==
s = new_slide()
header(s, "03 — Literature Review", "Related Work — Part I")
table(s, [
    ["Study", "Purpose", "Key Observation", "Limitation"],
    ["Chiu & Russell (2011)",
     "Construction data visualization environment",
     "Visual frameworks improve schedule comprehension vs. Gantt charts",
     "Schedule-only; no cost, resources, or prediction"],
    ["Al-Sulaiti et al. (2021)",
     "Power BI dashboards for EPC KPIs",
     "Dynamic reporting elevates management visibility",
     "Descriptive assessment; not predictive or cloud-native"],
    ["Radman et al. (2022)",
     "Digital delay-management lifecycle (DC → DA → DP)",
     "Integrated data lifecycle is essential to cut latency",
     "Conceptual architecture; no ML or containerization"],
], 0.7, 2.0, col_w=[2.6, 3.1, 3.3, 3.1], font=11.5, row_h=1.15, first_col_bold=True)
text(s, 0.7, 6.5, 11.9, 0.4,
     "Visualization and data-lifecycle work is mature — but stays descriptive and schedule-centric.",
     size=12, color=MUTED, italic=True)
footer(s, 6)

# =============================================================== SLIDE 7 ==
s = new_slide()
header(s, "03 — Literature Review", "Related Work — Part II")
table(s, [
    ["Study", "Purpose", "Key Observation", "Limitation"],
    ["Gajera (2023)",
     "Power BI integrated with project controls",
     "Dynamic cost tracking; ~25% lower reporting latency",
     "Descriptive visualization; no predictive model"],
    ["Zhang & Wang (2023)",
     "Probabilistic schedule risk (SORM + softmax CPM)",
     "Differentiable reliability finds most-probable failure point",
     "Isolated numerical model; no ingestion or UI"],
    ["Radman et al. / RealCONs (2026)",
     "QR + BIM + SQL + Power BI field monitoring",
     "Strong data continuity (SPI 1.01 vs 0.89)",
     "Deterministic EV; no predictive ML or containers"],
], 0.7, 2.0, col_w=[2.6, 3.1, 3.3, 3.1], font=11.5, row_h=1.15, first_col_bold=True)
text(s, 0.7, 6.5, 11.9, 0.4,
     "Predictive and deployment techniques exist in isolation — never combined into one platform.",
     size=12, color=MUTED, italic=True)
footer(s, 7)

# =============================================================== SLIDE 8 ==
s = new_slide()
header(s, "04 — Research Gap", "The Missing Link")
box(s, 0.7, 2.05, 11.95, 1.35, fill=PANEL2, line=ACCENT, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.1)
text(s, 1.05, 2.25, 11.25, 1.0,
     "No study presents a single, reproducible architecture that ingests heterogeneous "
     "project data, computes EVM, predicts delay risk with machine learning, visualizes "
     "results, and deploys reproducibly — all in one system.",
     size=16, color=TEXT, anchor=MSO_ANCHOR.MIDDLE)
gaps = [
    ("Separation", "Predictive algorithms live apart from visual business intelligence."),
    ("Fragile Pipelines", "Manual, spreadsheet-bound data preparation."),
    ("No Reproducibility", "No containerized, auto-scaling deployment architecture."),
]
x = 0.7
for title, body in gaps:
    chip(s, x, 3.85, 3.9, 1.5, title, body, ACCENT)
    x += 4.1
text(s, 0.7, 5.75, 11.9, 0.6,
     "→ The platform we build closes all three gaps in one deployable system.",
     size=15, color=GOOD, bold=True)
footer(s, 8)

# =============================================================== SLIDE 9 ==
s = new_slide()
header(s, "04 — Objectives", "Seven Objectives")
objs = [
    ("1", "Unified Data Model", "Project, activity, progress, cost, resource, KPI, risk entities"),
    ("2", "Validated Ingestion", "FastAPI microservice rejecting malformed data (HTTP 422)"),
    ("3", "Automated EVM", "CV, SV, CPI, SPI, EAC, TEAC computed in the pipeline"),
    ("4", "Delay-Risk Engine", "ML classifiers + probabilistic reliability formulation"),
    ("5", "Multi-tier Dashboard", "Executive, cost, schedule, and risk views"),
    ("6", "Cloud-Native Deploy", "Docker + Kubernetes with probes, HPA, persistence"),
    ("7", "Evaluation Method", "Analytical correctness, prediction quality, deployment repeatability"),
]
for i, (num, title, sub) in enumerate(objs):
    col = i % 2
    row = i // 2
    cx = 0.7 + col * 6.15
    cy = 2.0 + row * 1.2
    box(s, cx, cy, 5.85, 1.02, fill=PANEL, line=LINE, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.1)
    text(s, cx + 0.2, cy + 0.2, 0.7, 0.6, num, size=26, color=ACCENT, bold=True, font=FONT_H)
    text(s, cx + 0.95, cy + 0.14, 4.7, 0.35, title, size=14, color=WHITE, bold=True)
    text(s, cx + 0.95, cy + 0.5, 4.7, 0.4, sub, size=10.5, color=MUTED)
footer(s, 9)

# =============================================================== SLIDE 10 ==
s = new_slide()
header(s, "05 — Stack", "Technology Stack")
groups = [
    ("INGESTION & COMPUTE", [
        ("Python", "Core language for all services"),
        ("FastAPI", "Async REST layer + validation"),
        ("Pydantic", "Strict schema validation (422)"),
    ], ACCENT),
    ("STORAGE & ANALYTICS", [
        ("PostgreSQL", "3-tier relational store"),
        ("SQLAlchemy + Alembic", "ORM + migrations"),
        ("Pandas / NumPy", "EVM computation"),
        ("scikit-learn", "Delay-risk classifiers"),
    ], GOOD),
    ("PRESENTATION & DEPLOY", [
        ("Web UI (Jinja2 + Chart.js)", "Interactive dashboard"),
        ("Microsoft Power BI", "DAX decision layer"),
        ("Docker", "Reproducible images"),
        ("Kubernetes", "Orchestration, HPA, probes"),
    ], WARN),
]
x = 0.7
for title, items, col in groups:
    box(s, x, 2.0, 3.9, 4.3, fill=PANEL2, line=LINE, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.05)
    text(s, x + 0.22, 2.15, 3.5, 0.35, title, size=12, color=col, bold=True, spacing=1)
    y = 2.65
    for name, desc in items:
        text(s, x + 0.22, y, 3.5, 0.3, name, size=12.5, color=WHITE, bold=True)
        text(s, x + 0.22, y + 0.28, 3.5, 0.3, desc, size=9.5, color=MUTED)
        y += 0.85
    x += 4.1
footer(s, 10)

# =============================================================== SLIDE 11 ==
s = new_slide()
header(s, "05 — Architecture", "End-to-End Data Flow")
stages = [
    ("Data Sources", "CSV / REST / site updates", ACCENT),
    ("Ingestion API", "FastAPI + Pydantic validation", ACCENT),
    ("PostgreSQL", "3-tier schema + views", ACCENT),
    ("Analytics + ML", "EVM + delay-risk scoring", GOOD),
    ("Curated Views", "Reporting-ready data", GOOD),
    ("Web UI / Power BI", "Dashboards & alerts", WARN),
]
bw = 1.78
gap = 0.34
x = 0.55
for title, sub, col in stages:
    box(s, x, 2.2, bw, 1.5, fill=PANEL, line=LINE, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.08)
    box(s, x, 2.2, bw, 0.08, fill=col, line=None)
    text(s, x + 0.1, 2.42, bw - 0.2, 0.5, title, size=11.5, color=WHITE, bold=True, align=PP_ALIGN.CENTER)
    text(s, x + 0.08, 2.95, bw - 0.16, 0.65, sub, size=8.8, color=MUTED, align=PP_ALIGN.CENTER)
    x += bw
    if title != "Web UI / Power BI":
        arrow(s, x + 0.05, 2.82, w=gap - 0.1, h=0.3)
        x += gap

box(s, 0.55, 4.1, 12.2, 0.8, fill=PANEL2, line=ACCENT, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.15)
text(s, 0.8, 4.22, 11.8, 0.55,
     "Kubernetes orchestrates every backend service — health probes, autoscaling, persistent storage.",
     size=13.5, color=TEXT, bold=True, anchor=MSO_ANCHOR.MIDDLE)
bullets(s, [
    "Separation of concerns: ingestion, storage, analytics, and presentation are independent.",
    ("A dashboard outage never compromises data capture; analytics scales without redesign.", 1),
    "Power BI consumes curated views (not the live OLTP tables), keeping the BI model simple.",
], 0.7, 5.2, 11.9, 1.6, size=13)
footer(s, 11)

# =============================================================== SLIDE 12 ==
s = new_slide()
header(s, "06 — Data Model", "A Three-Tier Relational Schema")
tiers = [
    ("MASTER ENTITIES", [
        ("Project", "id · name · contractor · BAC · baseline dates"),
        ("Activity", "id · WBS · trade · planned dates · budget · float · criticality"),
    ], ACCENT),
    ("TIME-SERIES (append-only)", [
        ("ProgressUpdate", "activity · timestamp · % complete · PV · EV"),
        ("CostRecord", "activity · timestamp · actual cost"),
        ("ResourceRecord", "workers · equipment · material"),
    ], GOOD),
    ("COMPUTED OUTPUTS", [
        ("KPIResult", "PV · EV · AC · CV · SV · CPI · SPI · EAC · TEAC"),
        ("RiskResult", "delay probability · category · model version · top features"),
    ], WARN),
]
x = 0.7
for title, ents, col in tiers:
    box(s, x, 2.05, 3.85, 3.9, fill=PANEL2, line=LINE, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.05)
    text(s, x + 0.2, 2.2, 3.5, 0.35, title, size=12, color=col, bold=True, spacing=1)
    ey = 2.7
    for name, fields in ents:
        box(s, x + 0.18, ey, 3.5, 1.05, fill=PANEL, line=LINE, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.08)
        text(s, x + 0.32, ey + 0.1, 3.2, 0.3, name, size=12, color=WHITE, bold=True)
        text(s, x + 0.32, ey + 0.42, 3.2, 0.6, fields, size=9.3, color=MUTED)
        ey += 1.2
    x += 4.15
text(s, 0.7, 6.15, 11.9, 0.5,
     "Curated SQL views (v_activity_current, v_project_summary, v_progress_trend, v_cost_trend) "
     "expose reporting-ready fields to the UI and Power BI.",
     size=12, color=MUTED)
footer(s, 12)

# =============================================================== SLIDE 13 ==
s = new_slide()
header(s, "06 — Implementation", "Validated Ingestion Pipeline")
bullets(s, [
    "FastAPI exposes async REST endpoints for projects, activities, progress, costs, and resources.",
    "Every payload is validated against strict Pydantic schemas before touching the database.",
    ("Malformed data is rejected with HTTP 422 — bad records never reach storage.", 1),
    ("Negative budgets, finish-before-start dates, naive timestamps, and out-of-range values are all caught.", 1),
    "Records are upserted idempotently (PostgreSQL ON CONFLICT), so re-running is safe.",
    "Alembic migrations build the schema; curated views are re-applied idempotently.",
], 0.7, 1.95, 11.9, 3.5, size=15)

box(s, 0.7, 5.5, 5.8, 1.2, fill=PANEL2, line=BAD, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.08)
text(s, 0.95, 5.62, 5.4, 0.35, "REJECTED (HTTP 422)", size=10.5, color=BAD, bold=True, spacing=1)
text(s, 0.95, 5.98, 5.4, 0.6, 'percent_complete = 150  ·  naive timestamp  ·  budget = -5',
     size=11.5, color=TEXT)
box(s, 6.85, 5.5, 5.8, 1.2, fill=PANEL2, line=GOOD, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.08)
text(s, 7.1, 5.62, 5.4, 0.35, "ACCEPTED & STORED", size=10.5, color=GOOD, bold=True, spacing=1)
text(s, 7.1, 5.98, 5.4, 0.6, "19,317 records ingested — 0 rejected in the verified run",
     size=11.5, color=TEXT)
footer(s, 13)

# =============================================================== SLIDE 14 ==
s = new_slide()
header(s, "06 — Implementation", "Earned Value Management")
bullets(s, [
    "The analytics worker computes EVM as of a per-project status date (midpoint of each project's reporting window).",
    "PV/EV come from the latest progress snapshot at or before the status date; AC is cumulative cost to that date.",
    "Indicators are persisted to KPIResult for downstream UI and Power BI consumption.",
], 0.7, 1.9, 11.9, 1.5, size=14)

evm = [
    ("CV", "EV − AC", "Cost Variance"),
    ("SV", "EV − PV", "Schedule Variance"),
    ("CPI", "EV / AC", "Cost Performance Index"),
    ("SPI", "EV / PV", "Schedule Performance Index"),
    ("EAC", "BAC / CPI", "Estimate At Completion"),
    ("TEAC", "Duration / SPI", "Time Estimate At Completion"),
]
for i, (k, formula, desc) in enumerate(evm):
    col = i % 3
    row = i // 3
    cx = 0.7 + col * 4.1
    cy = 3.55 + row * 1.35
    box(s, cx, cy, 3.9, 1.15, fill=PANEL, line=LINE, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.1)
    text(s, cx + 0.2, cy + 0.12, 1.0, 0.4, k, size=18, color=ACCENT, bold=True, font=FONT_H)
    text(s, cx + 0.2, cy + 0.55, 3.5, 0.3, formula, size=12, color=WHITE, bold=True)
    text(s, cx + 0.2, cy + 0.82, 3.5, 0.3, desc, size=9.5, color=MUTED)
text(s, 0.7, 6.5, 11.9, 0.4,
     "Every KPI row is verified: CV = EV − AC, SV = EV − PV, CPI = EV / AC, SPI = EV / PV.",
     size=11.5, color=GOOD, italic=True)
footer(s, 14)

# =============================================================== SLIDE 15 ==
s = new_slide()
header(s, "06 — Implementation", "Predictive Delay-Risk Modeling")
box(s, 0.7, 1.9, 5.8, 2.05, fill=PANEL2, line=ACCENT, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.08)
text(s, 0.95, 2.05, 5.3, 0.35, "SUPERVISED BINARY CLASSIFICATION", size=11, color=ACCENT, bold=True)
text(s, 0.95, 2.45, 5.3, 0.45, "yᵢ = 1  if  (ActualFinishᵢ − PlannedFinishᵢ) > τ", size=15, color=WHITE, bold=True)
text(s, 0.95, 3.0, 5.3, 0.8,
     "τ = acceptable schedule buffer. Features: planned duration, total float, "
     "predecessor count, subcontractor delay rate, criticality, SPI trend.",
     size=10.5, color=MUTED)

box(s, 6.85, 1.9, 5.8, 2.05, fill=PANEL2, line=GOOD, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.08)
text(s, 7.1, 2.05, 5.3, 0.35, "PROBABILISTIC RELIABILITY", size=11, color=GOOD, bold=True)
text(s, 7.1, 2.45, 5.3, 0.45, "Sᵢ = Softmax(Eⱼ)", size=15, color=WHITE, bold=True)
text(s, 7.1, 3.0, 5.3, 0.8,
     "A temperature-scaled softmax surrogate of the CPM max operator locates "
     "the most-probable failure point across the activity network.",
     size=10.5, color=MUTED)

text(s, 0.7, 4.2, 11.9, 0.35, "MODEL SELECTION", size=11, color=ACCENT, bold=True, spacing=1)
table(s, [
    ["Model", "Acc.", "Prec.", "Rec.", "F1", "ROC-AUC"],
    ["Random Forest", "0.880", "0.704", "0.805", "0.746", "0.955"],
    ["Gradient Boosting", "0.903", "0.820", "0.713", "0.762", "0.943"],
    ["SVM (selected)", "0.920", "0.849", "0.791", "0.811", "0.969"],
], 0.7, 4.6, col_w=[2.4, 1.1, 1.1, 1.1, 1.1, 1.35], font=11, row_h=0.44, first_col_bold=True)
text(s, 8.9, 4.75, 3.8, 1.3,
     "Each activity gets a delay probability → Low / Medium / High category, "
     "surfaced as early-warning alerts.",
     size=11, color=MUTED)
footer(s, 15)

# =============================================================== SLIDE 16 ==
s = new_slide()
header(s, "07 — Live Platform", "Interactive Web Dashboard — Overview")
feature_panel(s, 9.0, 1.95, 3.65, 5.0, "WHAT IT SHOWS", [
    "Portfolio KPIs: budget, EV, AC",
    "CPI and SPI with colour status",
    "High-risk activity count",
    "Per-project CPI / SPI chart",
    "Risk distribution doughnut",
], ACCENT)
screenshot(s, "01-overview.png", 0.7, 1.95, 8.0,
           "Live dashboard — Executive Overview")
footer(s, 16)

# =============================================================== SLIDE 17 ==
s = new_slide()
header(s, "07 — Live Platform", "Cost & Schedule Performance")
screenshot(s, "02-cost.png", 0.7, 1.95, 5.9,
           "Cost — cumulative actual-cost curve + overruns")
screenshot(s, "03-schedule.png", 6.73, 1.95, 5.9,
           "Schedule — planned vs earned value S-curve")
box(s, 0.7, 5.95, 11.93, 0.85, fill=PANEL2, line=ACCENT, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.12)
text(s, 0.95, 6.07, 11.4, 0.6,
     "Both views recompute live from PostgreSQL — no manual refresh, no spreadsheet.",
     size=12.5, color=TEXT, anchor=MSO_ANCHOR.MIDDLE)
footer(s, 17)

# =============================================================== SLIDE 18 ==
s = new_slide()
header(s, "07 — Live Platform", "Delay-Risk & Activity Explorer")
screenshot(s, "04-risk.png", 0.7, 1.95, 5.9,
           "Delay-Risk — probability histogram + top-risk list")
screenshot(s, "05-activities.png", 6.73, 1.95, 5.9,
           "Activities — filterable explorer")
box(s, 0.7, 5.95, 11.93, 0.85, fill=PANEL2, line=WARN, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.12)
text(s, 0.95, 6.07, 11.4, 0.6,
     "Every activity carries a delay probability and a Low / Medium / High risk badge.",
     size=12.5, color=TEXT, anchor=MSO_ANCHOR.MIDDLE)
footer(s, 18)

# =============================================================== SLIDE 19 ==
s = new_slide()
header(s, "07 — Live Platform", "Data & Actions — Full Control from the UI")
screenshot(s, "06-data.png", 0.7, 1.95, 8.0,
           "Data & Actions — upload, recompute, retrain")
feature_panel(s, 9.0, 1.95, 3.65, 5.0, "ACTIONS", [
    "Upload CSV (validated via API)",
    "Recompute EVM + Risk",
    "Retrain the ML model",
    "See live row counts",
    "No CLI required",
], GOOD)
footer(s, 19)

# =============================================================== SLIDE 20 ==
s = new_slide()
header(s, "07 — Power BI", "Decision Layer")
bullets(s, [
    "Power BI connects to curated PostgreSQL views (import or DirectQuery) — not the raw OLTP tables.",
    "DAX measures compute cumulative PV/EV/AC curves and portfolio-level CPI/SPI.",
    "Four report pages mirror the platform's decision tiers.",
], 0.7, 1.95, 11.9, 1.6, size=14)
pages = [
    ("Executive Overview", "Budget vs. EV vs. AC · CPI · SPI · high-risk count"),
    ("Cost Performance", "Budget/actual/earned curves · cost-variance trend"),
    ("Schedule Performance", "Planned vs. actual · SV · SPI trend · delayed list"),
    ("Delay-Risk View", "Risk probability · category · contributing features"),
]
for i, (title, sub) in enumerate(pages):
    cx = 0.7 + (i % 2) * 6.15
    cy = 3.7 + (i // 2) * 1.25
    box(s, cx, cy, 5.85, 1.08, fill=PANEL, line=LINE, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.1)
    text(s, cx + 0.25, cy + 0.18, 5.3, 0.35, title, size=14, color=ACCENT, bold=True)
    text(s, cx + 0.25, cy + 0.58, 5.3, 0.4, sub, size=10.8, color=MUTED)
text(s, 0.7, 6.35, 11.9, 0.4,
     "Reproducible even offline: curated views export to CSV for template import.",
     size=11.5, color=MUTED, italic=True)
footer(s, 20)

# =============================================================== SLIDE 21 ==
s = new_slide()
header(s, "08 — Deployment", "Cloud-Native on Kubernetes")
box(s, 0.7, 1.95, 12.0, 4.15, fill=PANEL2, line=ACCENT, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.04)
text(s, 0.95, 2.05, 11.5, 0.35, "KUBERNETES CLUSTER", size=12, color=ACCENT, bold=True, spacing=1.5)
comps = [
    ("StatefulSet: db", "PostgreSQL + PVC", 0.95, 2.55, 2.55, GOOD),
    ("Deployment: ingestion", "2 replicas · HPA 2–6", 3.7, 2.55, 2.55, ACCENT),
    ("Deployment: web", "1 replica · health probes", 6.45, 2.55, 2.55, ACCENT),
    ("Job: pipeline", "migrate → ingest → train → verify", 9.2, 2.55, 3.2, WARN),
]
for title, sub, cx, cy, w, col in comps:
    box(s, cx, cy, w, 1.3, fill=PANEL, line=LINE, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.08)
    box(s, cx, cy, w, 0.08, fill=col, line=None)
    text(s, cx + 0.15, cy + 0.2, w - 0.3, 0.4, title, size=12, color=WHITE, bold=True)
    text(s, cx + 0.15, cy + 0.65, w - 0.3, 0.55, sub, size=9.5, color=MUTED)
caps = ["Liveness / readiness probes", "Horizontal Pod Autoscaling", "Persistent Volume Claims",
        "Secrets isolation", "Declarative manifests (kustomize)"]
x = 0.95
row_y = 4.25
for c in caps:
    w = 0.3 + len(c) * 0.093
    if x + w > 11.9:
        x = 0.95
        row_y += 0.62
    b = box(s, x, row_y, w, 0.5, fill=PANEL, line=LINE, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.5)
    fit_text(b, c, size=9.5, color=TEXT, align=PP_ALIGN.CENTER)
    x += w + 0.14
bullets(s, [
    "Docker packages a single shared image; Kubernetes provides reproducible orchestration.",
    "Self-healing verified: a deleted ingestion pod is rescheduled in ~1 second.",
], 0.7, 6.2, 11.9, 0.9, size=13)
footer(s, 21)

# =============================================================== SLIDE 22 ==
s = new_slide()
header(s, "08 — Results", "Model Benchmark")
text(s, 0.7, 1.9, 6, 0.35, "TABLE II — DELAY-RISK CLASSIFIERS (5-FOLD CV)", size=11, color=ACCENT, bold=True, spacing=1)
table(s, [
    ["Model", "Acc.", "Prec.", "Rec.", "F1", "ROC-AUC"],
    ["Random Forest", "0.880", "0.704", "0.805", "0.746", "0.955"],
    ["Gradient Boosting", "0.903", "0.820", "0.713", "0.762", "0.943"],
    ["SVM (selected)", "0.920", "0.849", "0.791", "0.811", "0.969"],
], 0.7, 2.35, col_w=[2.3, 1.05, 1.05, 1.05, 1.05, 1.3], font=12, row_h=0.52, first_col_bold=True)
text(s, 0.7, 4.75, 6.5, 0.35, "SVM selected by highest ROC-AUC (0.969).", size=12, color=GOOD, italic=True)

box(s, 7.0, 1.9, 5.6, 4.6, fill=PANEL2, line=LINE, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.05)
text(s, 7.25, 2.1, 5.1, 0.35, "WHY IT MATTERS", size=12, color=ACCENT, bold=True, spacing=1)
bullets(s, [
    "Accuracy alone is misleading on imbalanced delay data.",
    "ROC-AUC 0.969 means strong separation of delayed vs. on-time activities.",
    "F1 0.811 balances precision and recall for actionable alerts.",
    "Calibrated SVM probabilities feed the risk categories directly.",
], 7.25, 2.6, 5.1, 3.6, size=12.5)
footer(s, 22)

# =============================================================== SLIDE 23 ==
s = new_slide()
header(s, "08 — Validation", "Correctness, Reliability & Reproducibility")
checks = [
    ("EVM correctness", "All KPI rows satisfy CV = EV − AC, SV = EV − PV, CPI = EV / AC, SPI = EV / PV", ACCENT),
    ("End-to-end verification", "Automated E2E check passes: row counts, identities, risk bounds, non-empty views", GOOD),
    ("Self-healing", "A deleted ingestion pod is rescheduled by Kubernetes in ~1 second", GOOD),
    ("Autoscaling", "HPA scales the ingestion tier between 2 and 6 replicas on CPU", WARN),
    ("Ingestion integrity", "19,317 records ingested, 0 rejected; malformed payloads return HTTP 422", ACCENT),
    ("Reproducibility", "One-command launch; seeded synthetic dataset; identical results every run", GOOD),
]
for i, (title, body, col) in enumerate(checks):
    cx = 0.7 + (i % 2) * 6.15
    cy = 1.95 + (i // 2) * 1.62
    box(s, cx, cy, 5.85, 1.42, fill=PANEL, line=LINE, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.08)
    box(s, cx, cy, 0.07, 1.42, fill=col, line=None)
    text(s, cx + 0.25, cy + 0.16, 0.4, 0.4, "✓", size=16, color=col, bold=True)
    text(s, cx + 0.65, cy + 0.16, 5.0, 0.35, title, size=13.5, color=WHITE, bold=True)
    text(s, cx + 0.65, cy + 0.55, 5.0, 0.8, body, size=10.3, color=MUTED)
footer(s, 23)

# =============================================================== SLIDE 24 ==
s = new_slide()
header(s, "08 — Reproducibility", "One Command to Run Everything")
box(s, 0.7, 1.95, 11.95, 1.5, fill=PANEL2, line=ACCENT, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.1)
text(s, 1.0, 2.1, 5.6, 0.3, "LINUX / macOS", size=10.5, color=ACCENT, bold=True, spacing=1)
text(s, 1.0, 2.42, 5.6, 0.4, "./run.sh", size=22, color=WHITE, bold=True, font="Consolas")
text(s, 6.9, 2.1, 5.6, 0.3, "WINDOWS (POWERSHELL)", size=10.5, color=ACCENT, bold=True, spacing=1)
text(s, 6.9, 2.42, 5.6, 0.4, r".\run.ps1", size=22, color=WHITE, bold=True, font="Consolas")
text(s, 1.0, 2.95, 11.3, 0.4, "→ builds image · starts DB + API + UI · runs pipeline · prints http://localhost:8080",
     size=12, color=MUTED)

flow = [
    ("Generate", "seeded synthetic data"),
    ("Ingest", "validated via API"),
    ("Store", "PostgreSQL"),
    ("Analyse", "EVM metrics"),
    ("Predict", "train + score risk"),
    ("Verify", "E2E checks"),
]
x = 0.7
for i, (t, sub) in enumerate(flow):
    box(s, x, 3.9, 1.75, 1.15, fill=PANEL, line=LINE, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.1)
    text(s, x + 0.12, 4.05, 1.55, 0.35, t, size=12, color=ACCENT, bold=True, align=PP_ALIGN.CENTER)
    text(s, x + 0.08, 4.45, 1.6, 0.5, sub, size=8.5, color=MUTED, align=PP_ALIGN.CENTER)
    x += 1.75
    if i < 5:
        arrow(s, x + 0.03, 4.35, w=0.18, h=0.25, color=MUTED)
        x += 0.24
box(s, 0.7, 5.45, 11.95, 1.0, fill=PANEL2, line=GOOD, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.12)
text(s, 0.95, 5.57, 11.4, 0.75,
     "Deliverables: source code, Docker + Kubernetes manifests, web UI, Power BI layer, "
     "tests, and full documentation — all open and reproducible.",
     size=12.5, color=TEXT, anchor=MSO_ANCHOR.MIDDLE)
footer(s, 24)

# =============================================================== SLIDE 25 ==
s = new_slide()
header(s, "09 — Conclusion", "Contributions")
bullets(s, [
    "One reproducible, cloud-native platform unifying ingestion, storage, EVM analytics, ML risk, and visualization.",
    "Genuine EVM and a valid delay-risk classifier — enabled by an activity-level dataset with real baselines.",
    "Calibrated SVM achieving 0.969 ROC-AUC on delay prediction.",
    "Self-healing Kubernetes deployment with autoscaling and validated failover.",
    "An interactive web UI plus a Power BI decision layer over curated views.",
    "Open, one-command launch across Linux, macOS, and Windows.",
], 0.7, 2.0, 11.9, 4.4, size=16)
box(s, 0.7, 6.15, 11.95, 0.8, fill=PANEL2, line=ACCENT, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.15)
text(s, 0.95, 6.27, 11.4, 0.55,
     "From retrospective reporting → continuous, evidence-based project control.",
     size=14, color=TEXT, bold=True, anchor=MSO_ANCHOR.MIDDLE)
footer(s, 25)

# =============================================================== SLIDE 26 ==
s = new_slide()
header(s, "09 — Future Work", "Next Steps")
items = [
    ("Live Vision Feeds", "Computer-vision progress capture from on-site cameras."),
    ("4D BIM Integration", "Embed 4D BIM models directly within the dashboard canvas."),
    ("Real-World Validation", "Validate on real historical project portfolios."),
    ("Graph Risk Features", "Extend the risk model with schedule-network graph features."),
    ("Access Control", "Role-based access control and multi-tenant support."),
    ("Cost Forecasting", "Probabilistic cost-overrun forecasting alongside delay risk."),
]
for i, (title, body) in enumerate(items):
    cx = 0.7 + (i % 2) * 6.15
    cy = 1.95 + (i // 2) * 1.55
    box(s, cx, cy, 5.85, 1.32, fill=PANEL, line=LINE, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.08)
    text(s, cx + 0.25, cy + 0.18, 5.3, 0.35, title, size=14, color=WARN, bold=True)
    text(s, cx + 0.25, cy + 0.6, 5.3, 0.6, body, size=11, color=MUTED)
footer(s, 26)

# =============================================================== SLIDE 27 ==
s = new_slide()
header(s, "References", "Selected Sources")
refs = [
    "Chiu & Russell (2011). Design of a construction management data visualization environment. Automation in Construction, 20(4), 399–417.",
    "Al-Sulaiti et al. (2021). Using data analytics and visualization dashboards for EPC performance assessment. IEEE ICIEA, 207–211.",
    "Radman et al. (2022). Digital technologies and data-driven delay management. Frontiers in Built Environment, 8, 1029586.",
    "Gajera (2023). Integrating Power BI with project control systems. IJSRCE, 7(5), 154–160.",
    "Zhang & Wang (2023). Quantifying schedule delay risk with BIM and probabilistic reliability. Advances in Civil Engineering, 5525655.",
    "Radman et al. (2026). RealCONs: digital monitoring, delay detection and visualization framework. Automation in Construction, 183, 106781.",
    "Ghosh et al. (2024). Use of visual dashboards in construction projects. ASC Intl. Conference, EPIC Series, 5, 486–494.",
]
tb = s.shapes.add_textbox(Inches(0.7), Inches(1.95), Inches(12.0), Inches(4.9))
tf = tb.text_frame
tf.word_wrap = True
for i, r in enumerate(refs):
    p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
    p.space_after = Pt(12)
    run = p.add_run()
    run.text = f"[{i + 1}]  {r}"
    run.font.name = FONT
    run.font.size = Pt(12.5)
    run.font.color.rgb = TEXT
footer(s, 27)

# ------------------------------------------------------------------ save --
out = "project-final.pptx"
prs.save(out)
print(f"Saved {out} with {len(prs.slides)} slides")
