"""Build the static documentation site (site/) for Vercel or Netlify from deliverables/*.md."""
import json
import re
import shutil

import markdown

from common import BUILD_DIR, OUT_DIR, ROOT, SIM_DIR

SITE = ROOT / "site"
if SITE.exists():
    shutil.rmtree(SITE)
(SITE / "files").mkdir(parents=True)
for sub in ["diagrams", "wireframes"]:
    shutil.copytree(OUT_DIR / sub, SITE / sub)
for x in OUT_DIR.glob("*.xlsx"):
    shutil.copy(x, SITE / "files" / x.name)
shutil.copytree(SIM_DIR, SITE / "files" / "simulated")
N = json.loads((BUILD_DIR / "counts.json").read_text())

docs = sorted(OUT_DIR.glob("*.md"))
titles = {d.stem: d.read_text().splitlines()[0].lstrip("# ").strip() for d in docs}

CSS = """
:root{--bg:#f6f8fb;--panel:#fff;--ink:#10233d;--muted:#5a6b7d;--line:#dbe3ee;--accent:#1f3a5f;--accent2:#5b8def;--warn:#7a2e00;--warnbg:#fff4e0}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#0f141b;--panel:#161d27;--ink:#e6edf5;--muted:#9aa9ba;--line:#2a3544;--accent:#9db8f2;--accent2:#7ea4f5;--warn:#ffcf99;--warnbg:#2b2214}}
:root[data-theme="dark"]{--bg:#0f141b;--panel:#161d27;--ink:#e6edf5;--muted:#9aa9ba;--line:#2a3544;--accent:#9db8f2;--accent2:#7ea4f5;--warn:#ffcf99;--warnbg:#2b2214}
*{box-sizing:border-box}html,body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.6 Inter,system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
a{color:var(--accent2)}.wrap{display:grid;grid-template-columns:280px minmax(0,1fr);min-height:100vh}
nav{background:var(--panel);border-right:1px solid var(--line);padding:20px 14px;position:sticky;top:0;height:100vh;overflow:auto}
nav .brand{font-weight:800;font-size:16px;margin:0 6px 14px}nav a{display:block;padding:6px 8px;border-radius:6px;color:var(--ink);text-decoration:none;font-size:13.5px}
nav a:hover,nav a.on{background:var(--bg);color:var(--accent2)}main{padding:32px 40px;max-width:1200px;min-width:0}
h1{font-size:28px;line-height:1.25;margin-top:0}h2{margin-top:36px;border-bottom:1px solid var(--line);padding-bottom:6px}h3{margin-top:26px}
table{border-collapse:collapse;width:100%;font-size:13px;margin:14px 0;display:block;overflow-x:auto}
th,td{border:1px solid var(--line);padding:6px 9px;text-align:left;vertical-align:top}th{background:var(--accent);color:#fff;position:sticky;top:0}
:root[data-theme="dark"] th{color:#0f141b}tr:nth-child(even) td{background:color-mix(in srgb,var(--panel) 92%,var(--accent2))}
blockquote{margin:16px 0;padding:12px 16px;background:var(--warnbg);border-left:4px solid var(--warn);color:var(--warn);border-radius:6px}
code{background:color-mix(in srgb,var(--panel) 80%,var(--accent2));padding:1px 5px;border-radius:4px;font-size:12.5px}
pre{background:var(--panel);border:1px solid var(--line);padding:14px;border-radius:8px;overflow:auto}pre code{background:none;padding:0}
img{max-width:100%;height:auto;background:#fff;border:1px solid var(--line);border-radius:8px}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:12px;margin:18px 0}
.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:14px;text-decoration:none;color:var(--ink)}
.card b{display:block;margin-bottom:4px}.card span{color:var(--muted);font-size:13px}
.stats{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px;margin:18px 0}
.stat{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:12px}.stat b{font-size:24px;display:block;color:var(--accent2)}
.stat span{font-size:12.5px;color:var(--muted)}.toggle{margin:12px 6px 0;font-size:12px;background:none;border:1px solid var(--line);color:var(--ink);border-radius:6px;padding:4px 8px;cursor:pointer}
@media print{nav{display:none}.wrap{display:block}main{max-width:none;padding:0}th{position:static}table{display:table;font-size:10.5px}h2{break-after:avoid}}
@media (max-width:860px){.wrap{grid-template-columns:1fr}nav{position:static;height:auto;max-height:200px;border-right:0;border-bottom:1px solid var(--line)}main{padding:20px 16px}}
"""


def page(title, body, active):
    links = "".join(f"<a class='{'on' if s == active else ''}' href='{s}.html'>{t}</a>" for s, t in titles.items())
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} | VELOOP Analytics Task 01</title><style>{CSS}</style></head><body><div class="wrap"><nav>
<div class="brand"><a href="index.html" style="padding:0;color:inherit">VELOOP Analytics Blueprint</a></div>
<a class="{'on' if active == 'index' else ''}" href="index.html">Overview</a>{links}<a href="downloads.html" class="{'on' if active == 'downloads' else ''}">Downloads</a>
<button class="toggle" onclick="var r=document.documentElement;r.dataset.theme=(r.dataset.theme==='dark'?'light':'dark');try{{localStorage.setItem('t',r.dataset.theme)}}catch(e){{}}">Toggle theme</button>
</nav><main>{body}</main></div>
<script>try{{var t=localStorage.getItem('t');if(t)document.documentElement.dataset.theme=t}}catch(e){{}}</script>
<script type="module">if(document.querySelector('.mermaid')){{const m=await import('https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs');m.default.initialize({{startOnLoad:true,theme:'neutral'}});m.default.run();}}</script>
</body></html>"""


def convert(md_text):
    md_text = re.sub(r"```mermaid\n(.*?)```", lambda m: f"<pre class=\"mermaid\">{m.group(1)}</pre>", md_text, flags=re.S)
    html = markdown.markdown(md_text, extensions=["tables", "fenced_code", "sane_lists"])
    html = re.sub(r'href="(\d\d_[A-Za-z_&]+)\.md"', r'href="\1.html"', html)
    html = re.sub(r'href="(\d\d_[A-Za-z_&]+\.xlsx)"', r'href="files/\1"', html)
    html = html.replace('href="diagrams/er_diagram.mmd"', 'href="diagrams/er_diagram.mmd" download')
    return html


for d in docs:
    (SITE / f"{d.stem}.html").write_text(page(titles[d.stem], convert(d.read_text()), d.stem))

cards = "".join(f"<a class='card' href='{s}.html'><b>{t.split('·')[0].strip()}</b><span>{t.split('·', 1)[-1].strip()}</span></a>" for s, t in titles.items())
stats = [(N["n_events"], "proposed events"), (N["n_kpis"], "KPI definitions (no targets)"), (N["n_fields"], "data dictionary fields"),
         (N["n_entities"], "entities in logical model"), (N["n_dq"], "data quality issues logged"), (N["n_assump"], "unknowns recorded"),
         (N["n_rules"], "quality control rules"), (N["n_backlog"], "backlog items")]
index = f"""<h1>VELOOP Rewards · Data Analyst Task 01</h1>
<p>Product analytics, data readiness and data management blueprint, prepared on 2026-10-01. This site presents all 21 required deliverables. Every spreadsheet can be downloaded.</p>
<blockquote><b>Integrity notice.</b> All data used here is <b>simulated</b>: either supplied by VELOOP for this task or generated by the analyst and labelled
"SIMULATED DATA — CREATED FOR ANALYTICAL TESTING". Nothing on this site is an actual VELOOP statistic. Every event, field, table and KPI is a <b>proposal</b> that engineering has not yet verified.</blockquote>
<div class="stats">{"".join(f"<div class='stat'><b>{v}</b><span>{l}</span></div>" for v, l in stats)}</div>
<h2>Start here</h2><p><a href="01_Executive_Summary.html">Executive Summary</a> (2-4 pages) and <a href="21_Final_Consolidated_Report.html">Final Consolidated Report</a>.</p>
<h2>All deliverables</h2><div class="cards">{cards}</div>
<h2>Reproducibility</h2><p>Every number is generated by Python scripts from the datasets, and a validator runs cross-consistency checks across all deliverables. Source code: see the GitHub repository README.</p>"""
(SITE / "index.html").write_text(page("Overview", index, "index"))
import subprocess
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
for stem in ["01_Executive_Summary", "21_Final_Consolidated_Report"]:
    try:
        subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={OUT_DIR / (stem + '.pdf')}",
                        (SITE / f"{stem}.html").as_uri()], check=True, capture_output=True, timeout=120)
    except Exception as e:  # PDF is a convenience copy; the HTML/MD versions are the source
        print("PDF skipped:", stem, e)
for p in OUT_DIR.glob("*.pdf"):
    shutil.copy(p, SITE / "files" / p.name)
files = sorted((SITE / "files").rglob("*.*"))
dl = "<h1>Downloads</h1><h2>Spreadsheets</h2><ul>" + "".join(f"<li><a href='files/{f.name}' download>{f.name}</a></li>" for f in files if f.suffix == ".xlsx") + "</ul>"
dl += "<h2>Simulated companion datasets</h2><blockquote>Fictional data created for analytical testing. Not VELOOP data.</blockquote><ul>" + "".join(
    f"<li><a href='files/simulated/{f.name}' download>{f.name}</a> ({f.stat().st_size // 1024} KB)</li>" for f in files if f.parent.name == "simulated") + "</ul>"
dl += "<h2>Diagrams</h2><ul><li><a href='diagrams/er_diagram.png'>ER diagram (PNG)</a> · <a href='diagrams/er_diagram.svg'>SVG</a> · <a href='diagrams/er_diagram.mmd' download>Mermaid source</a></li><li><a href='diagrams/pipeline.svg'>Pipeline architecture</a></li>" + "".join(
    f"<li><a href='wireframes/{w.name}'>{w.stem.replace('_', ' ').title()} wireframe</a></li>" for w in sorted((SITE / "wireframes").glob("*.svg"))) + "</ul>"
pdfs = sorted(OUT_DIR.glob("*.pdf"))
if pdfs:
    dl += "<h2>PDF</h2><ul>" + "".join(f"<li><a href='files/{p.name}' download>{p.name}</a></li>" for p in pdfs) + "</ul>"
(SITE / "downloads.html").write_text(page("Downloads", dl, "downloads"))
print("site pages:", len(list(SITE.glob("*.html"))))
