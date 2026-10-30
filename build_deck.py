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


def reorder_slides(prs, order):
    """Reorder slides in-place. 'order' is a list of original 0-based indices."""
    sldIdLst = prs.slides._sldIdLst
    ids = list(sldIdLst)
    for el in ids:
        sldIdLst.remove(el)
    for i in order:
        sldIdLst.append(ids[i])


def renumber_footers(prs):
    """Rewrite the page-number box on every slide to its final position."""
    E = 914400
    for idx, slide in enumerate(prs.slides, 1):
        for sh in slide.shapes:
            if not sh.has_text_frame:
                continue
            l = (sh.left or 0) / E
            t = (sh.top or 0) / E
            if t > 6.9 and l > 11.0 and sh.text_frame.text.strip().isdigit():
                p = sh.text_frame.paragraphs[0]
                for r in list(p.runs):
                    r._r.getparent().remove(r._r)
                run = p.add_run()
                run.text = f"{idx:02d}"
                run.font.name = FONT
                run.font.size = Pt(9)
                run.font.color.rgb = MUTED


def add_notes(prs, notes_list):
    """Attach speaker notes to each slide (in final order)."""
    for slide, txt in zip(prs.slides, notes_list):
        slide.notes_slide.notes_text_frame.text = txt


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
text(s, 0.9, 5.55, 11.6, 0.35, "Dept. of Computer Science & Engineering  ·  Vellore Institute of Technology, Vellore",
     size=11, color=MUTED)
text(s, 0.9, 5.88, 11.6, 0.32,
     "Guide: Dr. Manikandan K  ·  Professor Grade 2, Department of Database Systems, SCSE",
     size=11, color=WHITE, bold=True)

techs = ["FastAPI", "PostgreSQL", "scikit-learn", "Power BI", "Docker", "Kubernetes"]
x = 0.9
for tch in techs:
    w = 0.28 + len(tch) * 0.105
    b = box(s, x, 6.32, w, 0.4, fill=PANEL, line=LINE, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.5)
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
header(s, "02 — Overview", "Agenda")
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
text(s, 7.1, 5.98, 5.4, 0.6, "13,980 records ingested — 0 rejected in the verified run",
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
    ["Random Forest", "0.900", "0.700", "0.856", "0.763", "0.960"],
    ["Gradient Boosting (selected)", "0.913", "0.789", "0.730", "0.748", "0.976"],
    ["Calibrated SVM", "0.920", "0.799", "0.785", "0.784", "0.949"],
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
    ["Random Forest", "0.900", "0.700", "0.856", "0.763", "0.960"],
    ["Gradient Boosting (selected)", "0.913", "0.789", "0.730", "0.748", "0.976"],
    ["Calibrated SVM", "0.920", "0.799", "0.785", "0.784", "0.949"],
], 0.7, 2.35, col_w=[2.3, 1.05, 1.05, 1.05, 1.05, 1.3], font=12, row_h=0.52, first_col_bold=True)
text(s, 0.7, 4.75, 6.5, 0.35, "Gradient Boosting selected by highest ROC-AUC (0.976).", size=12, color=GOOD, italic=True)

box(s, 7.0, 1.9, 5.6, 4.6, fill=PANEL2, line=LINE, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.05)
text(s, 7.25, 2.1, 5.1, 0.35, "WHY IT MATTERS", size=12, color=ACCENT, bold=True, spacing=1)
bullets(s, [
    "Accuracy alone is misleading on imbalanced delay data.",
    "ROC-AUC 0.976 means strong separation of delayed vs. on-time activities.",
    "F1 0.784 balances precision and recall for actionable alerts.",
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
    ("Ingestion integrity", "13,980 records ingested, 0 rejected; malformed payloads return HTTP 422", ACCENT),
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
    "Gradient Boosting achieving 0.976 ROC-AUC on delay prediction.",
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

# ============================================================== SLIDE A ===
# "Project at a Glance" — a plain-language explainer placed right after Agenda.
s = new_slide()
header(s, "02 — Overview", "Project at a Glance")
text(s, 0.7, 1.95, 11.9, 0.6,
     "In one sentence: we built a working web platform that watches a construction project's "
     "cost and schedule in near real time, predicts which activities will run late, and shows it all on a dashboard.",
     size=15, color=TEXT)

glance = [
    ("THE PROBLEM", "Project teams learn about cost overruns and delays too late — data lives in spreadsheets, and analytics is disconnected from the tools people actually use.", BAD),
    ("WHAT WE BUILT", "A containerized system: a validated API ingests project data, a database stores it, analytics compute standard project-control metrics, a model predicts delay risk, and a web dashboard (plus Power BI) presents it.", ACCENT),
    ("WHY IT MATTERS", "Managers get an early warning and a single, trustworthy view — instead of reconstructing reports by hand every cycle.", GOOD),
]
y = 2.75
for title, body, col in glance:
    box(s, 0.7, y, 11.95, 1.15, fill=PANEL, line=LINE, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.06)
    box(s, 0.7, y, 0.08, 1.15, fill=col, line=None)
    text(s, 1.0, y + 0.14, 2.5, 0.35, title, size=12, color=col, bold=True, spacing=1)
    text(s, 3.5, y + 0.14, 8.9, 0.9, body, size=12.5, color=TEXT, anchor=MSO_ANCHOR.MIDDLE)
    y += 1.3

text(s, 0.7, 6.55, 11.9, 0.4,
     "Everything is reproducible: one command builds and runs the whole platform, on Linux, macOS, or Windows.",
     size=11.5, color=ACCENT, italic=True)
footer(s, 99)

# ============================================================== SLIDE B ===
# Key Concepts glossary — makes the jargon understandable to a general reader.
s = new_slide()
header(s, "02 — Overview", "Key Concepts (Plain Language)")
concepts = [
    ("EVM", "Earned Value Management", "A standard way to measure project health by comparing planned work, work actually done, and money spent."),
    ("PV", "Planned Value", "The budgeted cost of the work that should be done by a given date."),
    ("EV", "Earned Value", "The budgeted cost of the work actually completed by that date."),
    ("AC", "Actual Cost", "The real money spent so far."),
    ("CPI", "Cost Performance Index", "EV / AC. Above 1 = under budget; below 1 = over budget."),
    ("SPI", "Schedule Performance Index", "EV / PV. Above 1 = ahead of schedule; below 1 = behind."),
    ("EAC", "Estimate At Completion", "A forecast of the final project cost based on current performance."),
    ("Delay Risk", "Predictive score", "A model's probability (0–1) that an activity will finish later than planned."),
]
y = 1.95
for i, (abbr, name, desc) in enumerate(concepts):
    col = i % 2
    row = i // 2
    cx = 0.7 + col * 6.15
    cy = 1.95 + row * 1.2
    box(s, cx, cy, 5.85, 1.05, fill=PANEL, line=LINE, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.08)
    b = box(s, cx + 0.15, cy + 0.22, 0.9, 0.6, fill=PANEL2, line=ACCENT, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.12)
    fit_text(b, abbr, size=14, color=ACCENT, bold=True, align=PP_ALIGN.CENTER)
    text(s, cx + 1.2, cy + 0.13, 4.5, 0.3, name, size=12, color=WHITE, bold=True)
    text(s, cx + 1.2, cy + 0.45, 4.5, 0.55, desc, size=9.5, color=MUTED)
footer(s, 99)

# ============================================================== SLIDE C ===
# Worked EVM example — shows the math with real numbers.
s = new_slide()
header(s, "06 — Implementation", "Worked Example: Reading the Metrics")
text(s, 0.7, 1.9, 11.9, 0.4,
     "Suppose one activity has a budget (BAC) of ₹100,000 and is planned to be 50% done today.",
     size=14, color=TEXT)
box(s, 0.7, 2.4, 5.85, 2.2, fill=PANEL2, line=LINE, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.06)
text(s, 0.95, 2.55, 5.3, 0.35, "THE INPUTS", size=11, color=ACCENT, bold=True, spacing=1)
inputs = [
    ("PV (planned value)", "₹50,000", "half the budget should be earned"),
    ("EV (earned value)", "₹40,000", "only 40% actually completed"),
    ("AC (actual cost)", "₹45,000", "we have spent ₹45k so far"),
]
iy = 2.95
for name, val, note in inputs:
    text(s, 0.95, iy, 3.0, 0.3, name, size=11.5, color=WHITE, bold=True)
    text(s, 3.9, iy, 1.4, 0.3, val, size=11.5, color=ACCENT, bold=True, align=PP_ALIGN.RIGHT)
    text(s, 0.95, iy + 0.28, 5.3, 0.3, note, size=9, color=MUTED)
    iy += 0.55

box(s, 6.85, 2.4, 5.8, 2.2, fill=PANEL2, line=LINE, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.06)
text(s, 7.1, 2.55, 5.3, 0.35, "THE INTERPRETATION", size=11, color=GOOD, bold=True, spacing=1)
text(s, 7.1, 2.95, 5.3, 1.6,
     "CPI = 40,000 / 45,000 = 0.89  →  over budget\n"
     "SPI = 40,000 / 50,000 = 0.80  →  behind schedule\n"
     "SV  = 40,000 − 50,000 = −10,000  →  ₹10k of work behind\n"
     "EAC = 100,000 / 0.89 ≈ ₹112,000  →  forecast overrun",
     size=11.5, color=TEXT)

box(s, 0.7, 4.85, 11.95, 1.35, fill=PANEL, line=WARN, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.08)
text(s, 0.95, 5.0, 11.4, 0.35, "WHAT A MANAGER SEES", size=11, color=WARN, bold=True, spacing=1)
text(s, 0.95, 5.35, 11.4, 0.75,
     "Two red flags on one activity: cost is trending ~12% over, and work is ~20% behind. "
     "The platform surfaces exactly this, per activity and rolled up per project.",
     size=12, color=TEXT)
text(s, 0.7, 6.4, 11.9, 0.4,
     "This is the manual arithmetic the platform automates for every activity, every time data changes.",
     size=11, color=MUTED, italic=True)
footer(s, 99)

# ============================================================== SLIDE D ===
# Limitations — intellectual honesty for an academic evaluation.
s = new_slide()
header(s, "09 — Limitations", "Honest Boundaries of the Work")
lims = [
    ("Synthetic dataset", "The bundled data is generated, not real. It has realistic structure and a valid delay label, but real megaprojects may need model recalibration."),
    ("Model, not causality", "The classifier predicts delay probability from features; it does not prove why an activity is late."),
    ("EVM needs baselines", "Genuine EVM requires planned values and budgets. The original source CSVs lacked these — hence the generator."),
    ("Single-node scope", "Kubernetes was validated on a local (minikube) cluster, not a production multi-node cloud."),
    ("No authentication", "The web UI is open by design for demonstration; production needs role-based access control."),
    ("Network dependency", "Live sync assumes connectivity; remote sites would need offline queuing."),
]
for i, (title, body) in enumerate(lims):
    col = i % 2
    row = i // 2
    cx = 0.7 + col * 6.15
    cy = 1.95 + row * 1.55
    box(s, cx, cy, 5.85, 1.35, fill=PANEL, line=LINE, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.08)
    text(s, cx + 0.22, cy + 0.15, 5.4, 0.35, title, size=13, color=WARN, bold=True)
    text(s, cx + 0.22, cy + 0.52, 5.4, 0.75, body, size=10, color=MUTED)
footer(s, 99)

# ------------------------------------------------------------------ reorder -
# New slides were appended at the end; move them to their logical positions.
# Current order (0-based): 0..26 = original 27, then 27=A,28=B,29=C,30=D
# Target:
#   0 Title, 1 Team, 2 Agenda, 27(Glance), 28(Concepts),
#   3..12 (Motivation .. Data Model),
#   13 Ingestion,14 EVM, 29(Worked example),15 ML,
#   16..18 screenshots, 19 Data&Actions, 20 PowerBI, 21 Deploy,
#   22 Results, 23 Validation, 24 Repro, 25 Conclusion,
#   30(Limitations), 26 Future, ... wait - need Future & References at end
# Original index map: 0 Title,1 Team,2 Agenda,3 Intro,4 Problem,5 Lit1,6 Lit2,
#   7 Gap,8 Objectives,9 Stack,10 Arch,11 DataModel,12 Ingestion,13 EVM,14 ML,
#   15 Shot1,16 Shot2,17 Shot3,18 Shot4,19 PowerBI,20 Deploy,21 Results,
#   22 Validation,23 Repro,24 Conclusion,25 Future,26 References
order = [
    0,    # Title
    1,    # Team
    2,    # Agenda
    27,   # A: Project at a Glance
    28,   # B: Key Concepts
    3,    # Motivation
    4,    # Problem
    5, 6, # Literature I, II
    7,    # Research Gap
    8,    # Objectives
    9,    # Stack
    10,   # Architecture
    11,   # Data Model
    12,   # Ingestion
    13,   # EVM
    29,   # C: Worked Example
    14,   # ML
    15, 16, 17, 18,  # screenshots
    19,   # Power BI
    20,   # Deploy
    21,   # Results
    22,   # Validation
    23,   # Reproducibility
    24,   # Conclusion
    30,   # D: Limitations
    25,   # Future Work
    26,   # References
]
reorder_slides(prs, order)
renumber_footers(prs)

# ------------------------------------------------------------------ notes --
NOTES = [
    # 1 Title
    "Title slide. Introduce the team and the one-line pitch: a working, cloud-native platform for construction project controls that predicts delay risk and visualizes cost/schedule health.",
    # 2 Team
    "Each member's area: Hasnain (data/platform), Sahil (analytics/ML), Aryan (architecture/visualization). Stress that it was delivered as one integrated system, not three separate pieces.",
    # 3 Agenda
    "Walk the audience through the flow: why (motivation) -> what's missing (gap) -> how we built it -> proof it works (live screenshots + results) -> conclusion.",
    # 4 Project at a Glance
    "Plain-language summary. If someone remembers nothing else, they should remember: 'it turns scattered project data into early warnings on a dashboard.'",
    # 5 Key Concepts
    "Define the jargon before using it. EVM, PV, EV, AC, CPI, SPI, EAC and delay-risk. Point out CPI and SPI rule of thumb: >1 good, <1 bad.",
    # 6 Motivation
    "Construction runs on the triple constraint. Despite P6/MS Project, overruns persist because data is fragmented and reported late. Industry 4.0 tools exist but are siloed.",
    # 7 Problem
    "Three deficiencies: fragmentation, retrospection (EVM is backward-looking), and analytics disconnected from deployment. The consequence is reacting too late.",
    # 8 Lit I
    "Prior visualization and lifecycle work is mature but descriptive and schedule-centric. Cite Chiu & Russell, Al-Sulaiti, Radman.",
    # 9 Lit II
    "Predictive and deployment techniques exist (Gajera, Zhang & Wang, RealCONs) but never combined. That isolation is the opening for our work.",
    # 10 Gap
    "No single reproducible system does all of: ingest, compute EVM, predict with ML, visualize, and deploy. We close all three gaps in one platform.",
    # 11 Objectives
    "Seven concrete objectives mapping to the system layers. Each is testable — see the validation slide later.",
    # 12 Stack
    "Explain why each tool: FastAPI for async validation, PostgreSQL for ACID + time series, scikit-learn for ML, Power BI for BI, Docker/K8s for reproducibility.",
    # 13 Architecture
    "Walk the data-flow arrows left to right. Emphasize separation of concerns: a dashboard outage never stops data capture.",
    # 14 Data Model
    "Three tiers: master entities, append-only time series, computed outputs. Curated views keep the BI model simple.",
    # 15 Ingestion
    "Show that validation is real: bad payloads get HTTP 422. In the verified run, 13,980 records were ingested with 0 rejected.",
    # 16 EVM
    "These six formulas are the backbone. The worker computes them as of a per-project status date.",
    # 17 Worked Example
    "Concrete numbers. CPI 0.89 = over budget, SPI 0.80 = behind, EAC forecasts an overrun. This is exactly what the platform automates.",
    # 18 ML
    "Delay label is defined by a finish-date threshold tau. Features are project-control signals. Gradient Boosting won on ROC-AUC (0.976). Softmax/MPP adds a probabilistic reliability view.",
    # 19 Screenshot 1
    "This is the real dashboard, not a mockup. Point out CPI 0.982 and SPI 0.991 and the 57 high-risk activities.",
    # 20 Screenshot 2
    "Cost page shows cumulative actual cost; schedule page shows planned-vs-earned S-curve. Both recompute live from the database.",
    # 21 Screenshot 3
    "Risk page shows the probability distribution and the top-risk list with badges; the explorer lets you filter by project, risk, trade, criticality.",
    # 22 Screenshot 4
    "Data & Actions page: upload CSV, recompute EVM+Risk, retrain the model — all from the browser, no CLI.",
    # 23 Power BI
    "Power BI is the enterprise BI layer. It reads curated views, not raw tables, and reproduces the four decision tiers with DAX.",
    # 24 Deploy
    "Kubernetes gives health probes, autoscaling, and persistent storage. Self-healing was verified: a deleted pod returns in ~1 second.",
    # 25 Results
    "Table II: Gradient Boosting best at ROC-AUC 0.976; calibrated SVM best F1 0.784. Explain why ROC-AUC/F1 matter more than raw accuracy on imbalanced delay data.",
    # 26 Validation
    "Six checks passed: EVM identities, E2E verification, self-healing, autoscaling, ingestion integrity, reproducibility.",
    # 27 Reproducibility
    "One command on Linux/macOS (./run.sh) or Windows (.\run.ps1). The six-stage flow runs automatically and prints the dashboard URL.",
    # 28 Conclusion
    "Six contributions. The headline: one reproducible platform that unifies the whole project-control pipeline.",
    # 29 Limitations
    "Be honest: synthetic data, correlational model, baseline dependency, single-node cluster, no auth, network dependency. Each has a path forward.",
    # 30 Future Work
    "Vision feeds, 4D BIM, real-world validation, graph features, access control, cost forecasting.",
    # 31 References
    "Full citations for the literature underpinning the design.",
]
if len(NOTES) != len(prs.slides):
    print(f"WARNING: {len(NOTES)} notes vs {len(prs.slides)} slides")
add_notes(prs, NOTES)

# ------------------------------------------------------------------ save --
out = "project-final.pptx"
prs.save(out)
print(f"Saved {out} with {len(prs.slides)} slides")
