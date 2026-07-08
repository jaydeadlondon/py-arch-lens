from pathlib import Path
from jinja2 import Template
from src.models import AnalysisSummary

_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>PyArchLens Report</title>
<style>
body{font-family:Inter,Arial,sans-serif;margin:0;background:#0f172a;color:#e2e8f0}
header{padding:32px;background:#111827;border-bottom:1px solid #334155}
main{padding:24px;display:grid;gap:24px}
section{background:#111827;border:1px solid #334155;border-radius:16px;padding:20px;box-shadow:0 20px 40px rgba(0,0,0,.25)}
h1,h2{margin:0 0 16px}table{width:100%;border-collapse:collapse}th,td{padding:10px;border-bottom:1px solid #334155;text-align:left}th{color:#93c5fd}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:16px}.card{background:#1e293b;border-radius:14px;padding:18px}.number{font-size:32px;font-weight:800;color:#38bdf8}.bad{color:#fb7185}.good{color:#34d399}.tag{display:inline-block;padding:4px 8px;border-radius:999px;background:#334155;margin:2px}
</style>
</head>
<body>
<header><h1>PyArchLens Report</h1><div>{{ summary.root }}</div></header>
<main>
<section class="cards">
<div class="card"><div>Modules</div><div class="number">{{ summary.modules|length }}</div></div>
<div class="card"><div>Edges</div><div class="number">{{ summary.graph_stats.edges }}</div></div>
<div class="card"><div>Cycles</div><div class="number {{ 'bad' if summary.cycles else 'good' }}">{{ summary.cycles|length }}</div></div>
<div class="card"><div>Orphans</div><div class="number">{{ summary.orphan_modules|length }}</div></div>
</section>
<section><h2>Top complex modules</h2><table><tr><th>Module</th><th>Score</th></tr>{% for name, score in summary.top_complex_modules %}<tr><td>{{ name }}</td><td>{{ score }}</td></tr>{% endfor %}</table></section>
<section><h2>Cycles</h2>{% if summary.cycles %}<table><tr><th>#</th><th>Modules</th></tr>{% for cycle in summary.cycles %}<tr><td>{{ loop.index }}</td><td>{{ cycle.nodes|join(' → ') }}</td></tr>{% endfor %}</table>{% else %}<p class="good">No cycles found.</p>{% endif %}</section>
<section><h2>Modules</h2><table><tr><th>Module</th><th>Lines</th><th>Imports</th><th>Classes</th><th>Functions</th><th>Complexity</th></tr>{% for name, info in modules %}<tr><td>{{ name }}</td><td>{{ info.metrics.lines }}</td><td>{{ info.metrics.import_count }}</td><td>{{ info.metrics.class_count }}</td><td>{{ info.metrics.function_count + info.metrics.method_count }}</td><td>{{ info.metrics.complexity_score }}</td></tr>{% endfor %}</table></section>
<section><h2>External imports</h2>{% for name, count in summary.external_imports.items() %}<span class="tag">{{ name }}: {{ count }}</span>{% else %}<p>No external imports.</p>{% endfor %}</section>
</main>
</body>
</html>
"""


def write_html_report(summary: AnalysisSummary, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    html = Template(_TEMPLATE).render(
        summary=summary, modules=sorted(summary.modules.items())
    )
    path.write_text(html, encoding="utf-8")
    return path
