"""Render the ER diagram (Mermaid CLI), the pipeline architecture SVG and dashboard wireframe SVGs."""
import os
import shutil
import subprocess
from html import escape

from common import BUILD_DIR, OUT_DIR
from specs import operations as OP

DIAG = OUT_DIR / "diagrams"
WIRE = OUT_DIR / "wireframes"
DIAG.mkdir(exist_ok=True)
WIRE.mkdir(exist_ok=True)
FONT = "font-family='Inter, Helvetica, Arial, sans-serif'"

# ------------------------------------------------------------------ ER diagram (PNG + SVG)
chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
if shutil.which("npx") and os.path.exists(chrome):
    (BUILD_DIR / "puppeteer.json").write_text('{"executablePath":"%s","args":["--no-sandbox"]}' % chrome)
    env = dict(os.environ, PUPPETEER_SKIP_DOWNLOAD="1")
    for ext, extra in (("png", ["-s", "2"]), ("svg", [])):
        subprocess.run(["npx", "-y", "@mermaid-js/mermaid-cli@11", "-p", str(BUILD_DIR / "puppeteer.json"), "-i", str(DIAG / "er_diagram.mmd"),
                        "-o", str(DIAG / f"er_diagram.{ext}"), "-b", "white", "-w", "2400", *extra], check=True, env=env, capture_output=True)
else:
    print("mermaid-cli or Chrome not available: keeping existing er_diagram.png/svg")


# ------------------------------------------------------------------ Pipeline SVG
def box(x, y, w, h, title, lines, fill, stroke="#1F3A5F"):
    out = [f"<rect x='{x}' y='{y}' width='{w}' height='{h}' rx='10' fill='{fill}' stroke='{stroke}' stroke-width='1.5'/>",
           f"<text x='{x + w / 2}' y='{y + 24}' text-anchor='middle' font-size='15' font-weight='700' fill='#10233D' {FONT}>{escape(title)}</text>"]
    for i, ln in enumerate(lines):
        out.append(f"<text x='{x + w / 2}' y='{y + 46 + i * 17}' text-anchor='middle' font-size='12' fill='#33475B' {FONT}>{escape(ln)}</text>")
    return "\n".join(out)


def arrow(x1, y1, x2, y2, label=""):
    s = f"<line x1='{x1}' y1='{y1}' x2='{x2}' y2='{y2}' stroke='#1F3A5F' stroke-width='2' marker-end='url(#ah)'/>"
    if label:
        s += f"<text x='{(x1 + x2) / 2 + 6}' y='{(y1 + y2) / 2 - 6}' font-size='11' fill='#7A2E00' {FONT}>{escape(label)}</text>"
    return s


W = 1180
stages = [
    ("1 VELOOP Application", ["Web app (client events: views, opens, onboarding)", "Backend services: accounts, tasks, rewards,", "wallet, withdrawals, referrals"], "#E8F0FB"),
    ("2 Application Events", ["Server events via transactional outbox (money, status)", "Client events to one validated endpoint", "event_id + schema_version + data_environment"], "#E8F0FB"),
    ("3 Raw Data Storage", ["raw_events table + business tables (read replica)", "Stage 2 only if load justifies: object storage + warehouse", "quarantine table for rejected rows"], "#FFF4E0"),
    ("4 Validation", ["QC-01..QC-11: IDs, enums, timestamps (UTC),", "required fields, naming, dedup on event_id"], "#FDECEC"),
    ("5 Transformation", ["Scheduled SQL / dbt Core (free)", "Clean tables, normalisation, derived fields with as-of time"], "#EAF6EC"),
    ("6 Analytical Data Layer", ["Daily KPI tables on IST day, production only (QC-16)", "Reconciliation QC-13 must pass before refresh"], "#EAF6EC"),
    ("7 BI / Dashboard", ["Metabase OSS or Looker Studio", "7 dashboards (deliverable 14), stale-data banner"], "#F1ECFB"),
    ("8 Business Reporting", ["Founder, Product, Operations, Finance", "Definitions versioned in change log (Q)"], "#F1ECFB"),
]
bw, bh, gap = 520, 100, 34
x0 = 60
parts = [f"<svg xmlns='http://www.w3.org/2000/svg' width='{W}' height='{70 + len(stages) * (bh + gap)}' viewBox='0 0 {W} {70 + len(stages) * (bh + gap)}'>",
         "<defs><marker id='ah' markerWidth='10' markerHeight='8' refX='9' refY='4' orient='auto'><path d='M0,0 L10,4 L0,8 z' fill='#1F3A5F'/></marker></defs>",
         "<rect width='100%' height='100%' fill='white'/>",
         f"<text x='{W / 2}' y='34' text-anchor='middle' font-size='20' font-weight='700' fill='#10233D' {FONT}>VELOOP analytics pipeline (proposed, Stage 1 with Stage 2 upgrade path)</text>"]
for i, (t, lines, fill) in enumerate(stages):
    y = 60 + i * (bh + gap)
    parts.append(box(x0, y, bw, bh, t, lines, fill))
    if i < len(stages) - 1:
        parts.append(arrow(x0 + bw / 2, y + bh, x0 + bw / 2, y + bh + gap - 2))
side = [("Monitoring", ["Freshness, volume anomalies,", "test failures, quarantine counts", "-> team channel alert"], 3),
        ("Failure handling", ["Retry with same event_id", "Failed model keeps last good data", "Nightly 7-day recompute for late callbacks"], 4),
        ("Refresh", ["Daily 02:00 IST full refresh", "Hourly: withdrawal queue,", "pending rewards"], 6),
        ("Ownership", ["Engineering: steps 1-4", "Data/Analytics: steps 5-7", "Product: definitions; Founder: approval"], 1)]
for t, lines, i in side:
    y = 60 + i * (bh + gap)
    parts.append(box(x0 + bw + 120, y, 400, bh, t, lines, "#F7F7F7", "#8A8A8A"))
    parts.append(f"<line x1='{x0 + bw}' y1='{y + bh / 2}' x2='{x0 + bw + 118}' y2='{y + bh / 2}' stroke='#8A8A8A' stroke-dasharray='5,4'/>")
parts.append("</svg>")
(DIAG / "pipeline.svg").write_text("\n".join(parts))

# ------------------------------------------------------------------ Dashboard wireframes
GLYPH = {"Line": "line", "Stat": "tiles", "Stacked": "bars", "Paired": "bars", "Tiles": "tiles", "Funnel": "funnel", "Column": "bars",
         "Cohort": "heat", "100%": "bars", "Bar": "bars", "Ranked": "bars", "Sankey": "table", "Horizontal": "bars", "Small": "line",
         "Treemap": "heat", "Aged": "bars", "Line +": "line"}


def glyph(kind, x, y, w, h):
    g = []
    if kind == "line":
        pts = " ".join(f"{x + 10 + i * (w - 20) / 9},{y + h - 15 - ((i * 37) % 60) * (h - 40) / 60}" for i in range(10))
        g.append(f"<polyline points='{pts}' fill='none' stroke='#5B8DEF' stroke-width='2.5'/>")
    elif kind == "bars":
        for i in range(7):
            bh_ = (20 + (i * 29) % 55) * (h - 30) / 80
            g.append(f"<rect x='{x + 12 + i * (w - 24) / 7}' y='{y + h - 10 - bh_}' width='{(w - 24) / 7 - 6}' height='{bh_}' fill='#9DB8F2'/>")
    elif kind == "tiles":
        for i in range(3):
            g.append(f"<rect x='{x + 10 + i * (w - 20) / 3}' y='{y + 15}' width='{(w - 20) / 3 - 8}' height='{h - 30}' rx='6' fill='#EEF3FD' stroke='#9DB8F2'/>")
            g.append(f"<text x='{x + 10 + i * (w - 20) / 3 + ((w - 20) / 3 - 8) / 2}' y='{y + h / 2 + 6}' text-anchor='middle' font-size='16' font-weight='700' fill='#5B8DEF' {FONT}>###</text>")
    elif kind == "funnel":
        for i in range(4):
            fw = (w - 30) * (1 - i * 0.2)
            g.append(f"<rect x='{x + (w - fw) / 2}' y='{y + 12 + i * (h - 24) / 4}' width='{fw}' height='{(h - 24) / 4 - 5}' fill='#9DB8F2'/>")
    elif kind == "heat":
        for r in range(4):
            for c in range(8):
                op = 0.2 + ((r * 3 + c * 5) % 8) / 10
                g.append(f"<rect x='{x + 10 + c * (w - 20) / 8}' y='{y + 10 + r * (h - 20) / 4}' width='{(w - 20) / 8 - 3}' height='{(h - 20) / 4 - 3}' fill='#5B8DEF' fill-opacity='{op:.2f}'/>")
    else:
        for r in range(4):
            g.append(f"<rect x='{x + 10}' y='{y + 12 + r * (h - 24) / 4}' width='{w - 20}' height='{(h - 24) / 4 - 4}' fill='#EEF3FD' stroke='#C9D7F7'/>")
    return "\n".join(g)


for dname in dict.fromkeys(d["dashboard"] for d in OP.DASHBOARDS):
    vis = [d for d in OP.DASHBOARDS if d["dashboard"] == dname]
    cols, pw, ph = 2, 540, 230
    rows = (len(vis) + 1) // 2
    Wd, Hd = 40 + cols * (pw + 20), 130 + rows * (ph + 20)
    s = [f"<svg xmlns='http://www.w3.org/2000/svg' width='{Wd}' height='{Hd}' viewBox='0 0 {Wd} {Hd}'>", "<rect width='100%' height='100%' fill='#F6F8FB'/>",
         f"<text x='30' y='40' font-size='22' font-weight='700' fill='#10233D' {FONT}>Dashboard {escape(dname)}</text>",
         f"<text x='30' y='64' font-size='12' fill='#7A2E00' {FONT}>WIREFRAME. Layout only, no data. Production data only (data_environment = production). Shows 'data as of' time.</text>"]
    filters = sorted({f.strip() for d in vis for f in d["filters"].split(",") if f.strip() not in ("-", "", "date range")})
    s.append(f"<rect x='30' y='78' width='{Wd - 60}' height='30' rx='6' fill='white' stroke='#C9D7F7'/>")
    s.append(f"<text x='42' y='98' font-size='12' fill='#33475B' {FONT}>Filters: Date range | {escape(' | '.join(filters) or 'none')}   ·   Data as of: [timestamp]</text>")
    for i, d in enumerate(vis):
        x, y = 30 + (i % cols) * (pw + 20), 122 + (i // cols) * (ph + 20)
        kind = next((v for k, v in GLYPH.items() if d["visualization"].startswith(k)), "bars")
        s.append(f"<rect x='{x}' y='{y}' width='{pw}' height='{ph}' rx='10' fill='white' stroke='#C9D7F7'/>")
        s.append(f"<text x='{x + 14}' y='{y + 24}' font-size='14' font-weight='700' fill='#10233D' {FONT}>{escape(d['visual'])}</text>")
        s.append(f"<text x='{x + 14}' y='{y + 42}' font-size='11' fill='#5A6B7D' {FONT}>{escape(d['metric'])} · {escape(d['visualization'])} · refresh {escape(d['refresh'])}</text>")
        s.append(glyph(kind, x + 14, y + 52, pw - 28, ph - 92))
        s.append(f"<text x='{x + 14}' y='{y + ph - 14}' font-size='11' fill='#33475B' {FONT}>Q: {escape(d['business_question'][:80])}</text>")
    s.append("</svg>")
    (WIRE / f"dashboard_{dname.split()[0]}.svg").write_text("\n".join(s))
print("diagrams:", sorted(p.name for p in DIAG.iterdir()), "wireframes:", sorted(p.name for p in WIRE.iterdir()))
