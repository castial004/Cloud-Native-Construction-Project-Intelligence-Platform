"""Generate project-final.pptx — the final-year project presentation for CCPIP.

Reproducible: run with the platform venv (python-pptx installed).
    platform/.venv/bin/python build_deck.py

Produces an 18-slide, 16:9 academic-evaluation deck reflecting the *implemented*
system (not just the proposal).
"""
from __future__ import annotations

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
            # 'spc' is in hundredths of a point, as an integer.
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
    bar = box(slide, 0.72, 1.62, 1.15, 0.06, fill=ACCENT, line=None)


def footer(slide, n, label="CCPIP — Final-Year Project"):
    text(slide, 0.7, 7.02, 6, 0.3, label, size=9, color=MUTED)
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
    sp = box(slide, l, t, w, h, fill=color, line=None, shape=MSO_SHAPE.RIGHT_ARROW)
    return sp


# =============================================================== SLIDE 1 ==
s = new_slide()
box(s, 0, 0, SW, 0.16, fill=ACCENT, line=None)
text(s, 0.9, 0.75, 11, 0.4, "FINAL-YEAR PROJECT  •  VISUAL ANALYTICS", size=14, color=ACCENT, bold=True, spacing=2)
text(s, 0.9, 1.55, 11.6, 1.5,
     "Cloud-Native Construction Project\nIntelligence Platform",
     size=44, color=WHITE, bold=True, font=FONT_H)
text(s, 0.9, 3.35, 11.6, 0.9,
     "Predictive Delay-Risk Scoring & Real-Time Performance Analytics",
     size=22, color=MUTED)
box(s, 0.92, 4.45, 1.6, 0.06, fill=ACCENT, line=None)

text(s, 0.9, 4.75, 7, 0.35, "Aryan Kishor Sao", size=18, color=TEXT, bold=True)
text(s, 0.9, 5.12, 7, 0.35, "Dept. of Computer Science & Engineering", size=13, color=MUTED)
text(s, 0.9, 5.42, 7, 0.35, "Bhilai Institute of Technology, Durg, India", size=13, color=MUTED)

techs = ["FastAPI", "PostgreSQL", "scikit-learn", "Power BI", "Docker", "Kubernetes"]
x = 0.9
for tch in techs:
    w = 0.28 + len(tch) * 0.105
    b = box(s, x, 6.15, w, 0.4, fill=PANEL, line=LINE, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.5)
    fit_text(b, tch, size=11, color=ACCENT, bold=True, align=PP_ALIGN.CENTER)
    x += w + 0.15

# =============================================================== SLIDE 2 ==
s = new_slide()
header(s, "Overview", "Agenda")
agenda = [
    ("01", "Introduction & Motivation", "Why construction control needs a deployable intelligence platform"),
    ("02", "Problem Definition", "Fragmentation, retrospection, and the analytics–deployment gap"),
    ("03", "Literature Review", "What prior work covers — and what it leaves open"),
    ("04", "Research Gap & Objectives", "The missing link and the seven objectives"),
    ("05", "System Architecture", "Ingestion → storage → analytics → visualization"),
    ("06", "Implementation", "Data model, EVM, ML risk, web UI, Power BI, deployment"),
    ("07", "Results & Validation", "Model benchmark, EVM correctness, self-healing"),
    ("08", "Conclusion & Future Work", "Contributions and next steps"),
]
col_x = [0.7, 6.9]
for i, (num, title, sub) in enumerate(agenda):
    cx = col_x[i // 4]
    cy = 2.05 + (i % 4) * 1.18
    text(s, cx, cy, 0.9, 0.7, num, size=30, color=ACCENT, bold=True, font=FONT_H)
    text(s, cx + 0.85, cy + 0.05, 5.2, 0.4, title, size=16, color=WHITE, bold=True)
    text(s, cx + 0.85, cy + 0.45, 5.2, 0.5, sub, size=11.5, color=MUTED)
footer(s, 2)

# =============================================================== SLIDE 3 ==
s = new_slide()
header(s, "01 — Introduction", "Motivation")
bullets(s, [
    "Construction project control depends on the triple constraint: schedule, cost, and scope.",
    "Despite tools like Primavera P6 and MS Project, cost overruns and schedule slippage remain endemic.",
    "A root cause is delayed visibility: progress and cost data are collected through manual site logs, spreadsheets, and disconnected subcontractor reports.",
    ("Variances are identified only at periodic commercial meetings — long after corrective action could help.", 1),
    "Industry 4.0 (BIM, IoT, QR capture) and BI dashboards (Power BI) show value individually, but remain siloed.",
    ("The need: continuous, evidence-based monitoring — not retrospective reporting.", 1),
], 0.7, 2.0, 11.9, 4.6, size=17)

chip(s, 0.7, 5.9, 3.8, 0.9, "Triple Constraint", "Schedule · Cost · Scope tracked together", ACCENT)
chip(s, 4.75, 5.9, 3.8, 0.9, "Delayed Visibility", "Data fragmented and reported late", WARN)
chip(s, 8.8, 5.9, 3.8, 0.9, "Our Aim", "Continuous, predictive project control", GOOD)
footer(s, 3)

# =============================================================== SLIDE 4 ==
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
box(s, 0.7, 5.65, 11.9, 1.05, fill=PANEL2, line=ACCENT, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.12)
text(s, 1.0, 5.82, 11.3, 0.75,
     "Consequence:  schedule and cost variances are discovered too late for preventive intervention — "
     "and there is no single reproducible system to fix it.",
     size=14, color=TEXT, anchor=MSO_ANCHOR.MIDDLE)
footer(s, 4)

# =============================================================== SLIDE 5 ==
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
footer(s, 5)

# =============================================================== SLIDE 6 ==
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
footer(s, 6)

# =============================================================== SLIDE 7 ==
s = new_slide()
header(s, "04 — Research Gap", "The Missing Link")
box(s, 0.7, 2.05, 11.9, 1.35, fill=PANEL2, line=ACCENT, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.1)
text(s, 1.05, 2.25, 11.2, 1.0,
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
footer(s, 7)

# =============================================================== SLIDE 8 ==
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
footer(s, 8)

# =============================================================== SLIDE 9 ==
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
    box(s, x, 2.25, bw, 1.45, fill=PANEL, line=LINE, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.08)
    box(s, x, 2.25, bw, 0.08, fill=col, line=None)
    text(s, x + 0.1, 2.45, bw - 0.2, 0.5, title, size=11.5, color=WHITE, bold=True, align=PP_ALIGN.CENTER)
    text(s, x + 0.08, 2.95, bw - 0.16, 0.65, sub, size=8.8, color=MUTED, align=PP_ALIGN.CENTER)
    x += bw
    if title != "Web UI / Power BI":
        arrow(s, x + 0.05, 2.83, w=gap - 0.1, h=0.3)
        x += gap

box(s, 0.55, 4.15, 12.2, 0.85, fill=PANEL2, line=ACCENT, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.15)
text(s, 0.8, 4.3, 11.8, 0.55,
     "Kubernetes orchestrates every backend service — health probes, autoscaling, persistent storage.",
     size=13.5, color=TEXT, bold=True, anchor=MSO_ANCHOR.MIDDLE)
bullets(s, [
    "Separation of concerns: ingestion, storage, analytics, and presentation are independent.",
    ("A dashboard outage never compromises data capture; analytics scales without redesign.", 1),
    "Power BI consumes curated views (not the live OLTP tables), keeping the BI model simple.",
], 0.7, 5.35, 11.9, 1.5, size=13)
footer(s, 9)

# =============================================================== SLIDE 10 ==
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
footer(s, 10)

# =============================================================== SLIDE 11 ==
s = new_slide()
header(s, "06 — Implementation", "Data Pipeline & Earned Value Management")
bullets(s, [
    "FastAPI ingestion validates every record against strict Pydantic schemas — malformed payloads are rejected with HTTP 422.",
    "Alembic migrations build the schema; curated views are (re)applied idempotently.",
    "The analytics worker computes EVM as of a per-project status date (midpoint of each project's reporting window).",
], 0.7, 1.95, 11.9, 1.7, size=14)

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
    cy = 3.75 + row * 1.35
    box(s, cx, cy, 3.9, 1.15, fill=PANEL, line=LINE, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.1)
    text(s, cx + 0.2, cy + 0.12, 1.0, 0.4, k, size=18, color=ACCENT, bold=True, font=FONT_H)
    text(s, cx + 0.2, cy + 0.55, 3.5, 0.3, formula, size=12, color=WHITE, bold=True)
    text(s, cx + 0.2, cy + 0.82, 3.5, 0.3, desc, size=9.5, color=MUTED)
text(s, 0.7, 6.55, 11.9, 0.4,
     "Every KPI row is verified: CV = EV − AC, SV = EV − PV, CPI = EV / AC, SPI = EV / PV.",
     size=11.5, color=GOOD, italic=True)
footer(s, 11)

# =============================================================== SLIDE 12 ==
s = new_slide()
header(s, "06 — Implementation", "Predictive Delay-Risk Modeling")
box(s, 0.7, 1.95, 5.8, 2.0, fill=PANEL2, line=ACCENT, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.08)
text(s, 0.95, 2.1, 5.3, 0.35, "SUPERVISED BINARY CLASSIFICATION", size=11, color=ACCENT, bold=True)
text(s, 0.95, 2.5, 5.3, 0.45, "yᵢ = 1  if  (ActualFinishᵢ − PlannedFinishᵢ) > τ", size=16, color=WHITE, bold=True)
text(s, 0.95, 3.05, 5.3, 0.75,
     "τ = acceptable schedule buffer. Features: planned duration, total float, "
     "predecessor count, subcontractor delay rate, criticality, SPI trend.",
     size=10.5, color=MUTED)

box(s, 6.9, 1.95, 5.7, 2.0, fill=PANEL2, line=GOOD, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.08)
text(s, 7.15, 2.1, 5.2, 0.35, "PROBABILISTIC RELIABILITY", size=11, color=GOOD, bold=True)
text(s, 7.15, 2.5, 5.2, 0.45, "Sᵢ = Softmax(Eⱼ)", size=16, color=WHITE, bold=True)
text(s, 7.15, 3.05, 5.2, 0.75,
     "A temperature-scaled softmax surrogate of the CPM max operator locates "
     "the most-probable failure point across the activity network.",
     size=10.5, color=MUTED)

bullets(s, [
    "Three candidate classifiers compared with 5-fold cross-validation: Random Forest, Gradient Boosting, SVM.",
    "SVM (calibrated) selected by ROC-AUC and persisted for scoring.",
    "Every activity receives a delay probability → Low / Medium / High risk category.",
], 0.7, 4.35, 11.9, 1.8, size=14)
text(s, 0.7, 6.35, 11.9, 0.4,
     "Ties the predictive layer directly to project-control features — not generic signals.",
     size=11.5, color=ACCENT, italic=True)
footer(s, 12)

# =============================================================== SLIDE 13 ==
s = new_slide()
header(s, "06 — Implementation", "Interactive Web Dashboard")
bullets(s, [
    "FastAPI + Jinja2 + Chart.js — no build step, containerized like every other service.",
], 0.7, 1.9, 11.9, 0.5, size=13)
pages = [
    ("Overview", "Budget, EV, AC, CPI, SPI, high-risk count; per-project charts", ACCENT),
    ("Cost", "Cumulative actual-cost curve; top cost overrun activities", ACCENT),
    ("Schedule", "Planned-vs-earned S-curve; most-delayed activities", GOOD),
    ("Delay-Risk", "Probability histogram; top-risk activities with badges", WARN),
    ("Activities", "Filterable explorer (project / risk / trade / critical)", GOOD),
    ("Data & Actions", "CSV upload · Recompute EVM+Risk · Retrain model", BAD),
]
for i, (title, sub, col) in enumerate(pages):
    colx = i % 3
    rowy = i // 3
    cx = 0.7 + colx * 4.1
    cy = 2.5 + rowy * 1.55
    box(s, cx, cy, 3.9, 1.3, fill=PANEL, line=LINE, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.08)
    box(s, cx, cy, 0.07, 1.3, fill=col, line=None)
    text(s, cx + 0.22, cy + 0.15, 3.5, 0.35, title, size=14, color=WHITE, bold=True)
    text(s, cx + 0.22, cy + 0.58, 3.5, 0.6, sub, size=10.3, color=MUTED)
box(s, 0.7, 5.75, 11.9, 0.95, fill=PANEL2, line=ACCENT, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.12)
text(s, 0.95, 5.9, 11.4, 0.65,
     "One command launches everything — ./run.sh (Linux/macOS) or .\\run.ps1 (Windows) → http://localhost:8080",
     size=13.5, color=TEXT, bold=True, anchor=MSO_ANCHOR.MIDDLE)
footer(s, 13)

# =============================================================== SLIDE 14 ==
s = new_slide()
header(s, "06 — Implementation", "Power BI Decision Layer")
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
footer(s, 14)

# =============================================================== SLIDE 15 ==
s = new_slide()
header(s, "06 — Deployment", "Cloud-Native on Kubernetes")
# cluster box
box(s, 0.7, 1.95, 12.0, 4.15, fill=PANEL2, line=ACCENT, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.04)
text(s, 0.95, 2.05, 11.5, 0.35, "KUBERNETES CLUSTER", size=12, color=ACCENT, bold=True, spacing=1.5)
# inner components
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
# capabilities row (wrapped to fit within the cluster box)
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
footer(s, 15)

# =============================================================== SLIDE 16 ==
s = new_slide()
header(s, "07 — Results", "Model Benchmark & Validation")
text(s, 0.7, 1.9, 6, 0.35, "TABLE II — DELAY-RISK CLASSIFIERS (5-FOLD CV)", size=11, color=ACCENT, bold=True, spacing=1)
table(s, [
    ["Model", "Acc.", "Prec.", "Rec.", "F1", "ROC-AUC"],
    ["Random Forest", "0.880", "0.704", "0.805", "0.746", "0.955"],
    ["Gradient Boosting", "0.903", "0.820", "0.713", "0.762", "0.943"],
    ["SVM (selected)", "0.920", "0.849", "0.791", "0.811", "0.969"],
], 0.7, 2.35, col_w=[2.3, 1.05, 1.05, 1.05, 1.05, 1.3], font=12, row_h=0.52, first_col_bold=True)
text(s, 0.7, 4.7, 8, 0.35, "SVM selected by highest ROC-AUC.", size=11, color=GOOD, italic=True)

# right: validation panel
box(s, 8.3, 1.9, 4.3, 4.7, fill=PANEL2, line=GOOD, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.06)
text(s, 8.55, 2.05, 3.9, 0.35, "VALIDATION", size=12, color=GOOD, bold=True, spacing=1.5)
checks = [
    ("EVM correctness", "All KPI rows satisfy CV, SV, CPI, SPI identities"),
    ("End-to-end", "E2E verification passes (pipeline + views)"),
    ("Self-healing", "Ingestion pod rescheduled in ~1 s"),
    ("Autoscaling", "HPA 2–6 replicas on the ingestion tier"),
    ("Reproducible", "One-command launch, seeded dataset"),
]
cy = 2.5
for title, sub in checks:
    text(s, 8.55, cy, 0.35, 0.35, "✓", size=15, color=GOOD, bold=True)
    text(s, 8.9, cy, 3.6, 0.35, title, size=12.5, color=WHITE, bold=True)
    text(s, 8.9, cy + 0.32, 3.6, 0.5, sub, size=9.8, color=MUTED)
    cy += 0.82
footer(s, 16)

# =============================================================== SLIDE 17 ==
s = new_slide()
header(s, "08 — Conclusion", "Contributions & Future Work")
text(s, 0.7, 1.9, 6, 0.35, "CONTRIBUTIONS", size=12, color=GOOD, bold=True, spacing=1.5)
bullets(s, [
    "One reproducible, cloud-native platform unifying ingestion, storage, EVM analytics, ML risk, and visualization.",
    "Genuine EVM and a valid delay-risk classifier — enabled by an activity-level dataset with real baselines.",
    "Calibrated SVM achieving 0.969 ROC-AUC on delay prediction.",
    "Self-healing Kubernetes deployment with autoscaling and validated failover.",
    "Open, one-command launch across Linux, macOS, and Windows.",
], 0.7, 2.35, 6.0, 3.9, size=12.5)

text(s, 7.0, 1.9, 6, 0.35, "FUTURE WORK", size=12, color=WARN, bold=True, spacing=1.5)
bullets(s, [
    "Live computer-vision progress feeds from site cameras.",
    "Embed 4D BIM models directly within the dashboard canvas.",
    "Validate on real historical project portfolios.",
    "Extend the risk model with schedule-network graph features.",
    "Role-based access control and multi-tenant support.",
], 7.0, 2.35, 5.6, 3.9, size=12.5)
box(s, 0.7, 6.3, 11.9, 0.7, fill=PANEL2, line=ACCENT, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.15)
text(s, 0.95, 6.4, 11.4, 0.5,
     "From retrospective reporting → continuous, evidence-based project control.",
     size=14, color=TEXT, bold=True, anchor=MSO_ANCHOR.MIDDLE)
footer(s, 17)

# =============================================================== SLIDE 18 ==
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
footer(s, 18)

# ------------------------------------------------------------------ save --
out = "project-final.pptx"
prs.save(out)
print(f"Saved {out} with {len(prs.slides)} slides")
