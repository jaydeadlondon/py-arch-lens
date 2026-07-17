from pathlib import Path
import re
from src.dependency_queries import graph_from_summary
from src.models import AnalysisSummary


def write_mermaid_report(summary: AnalysisSummary, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_mermaid(summary), encoding="utf-8")
    return path


def render_mermaid(summary: AnalysisSummary) -> str:
    graph = graph_from_summary(summary)
    lines = ["flowchart LR"]
    aliases = {node: _alias(node) for node in sorted(graph.nodes)}
    for node in sorted(graph.nodes):
        lines.append(f'    {aliases[node]}["{node}"]')
    for source in sorted(graph.edges):
        for target in sorted(graph.edges[source]):
            lines.append(f"    {aliases[source]} --> {aliases[target]}")
    return "\n".join(lines) + "\n"


def _alias(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_]", "_", value)
    return f"m_{cleaned}"
