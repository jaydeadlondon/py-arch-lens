from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from src.models import AnalysisSummary


def summary_panel(summary: AnalysisSummary) -> Panel:
    stats = summary.graph_stats
    text = Text()
    text.append(f"Root: {summary.root}\n", style="bold")
    text.append(f"Modules: {len(summary.modules)}\n")
    text.append(f"Edges: {stats.get('edges', 0)}\n")
    text.append(f"Cycles: {len(summary.cycles)}\n")
    text.append(f"Orphans: {len(summary.orphan_modules)}\n")
    text.append(f"External imports: {len(summary.external_imports)}")
    return Panel(text, title="PyArchLens", border_style="cyan")


def module_table(summary: AnalysisSummary) -> Table:
    table = Table(title="Modules")
    table.add_column("Module", style="cyan", no_wrap=True)
    table.add_column("Lines", justify="right")
    table.add_column("Imports", justify="right")
    table.add_column("Classes", justify="right")
    table.add_column("Functions", justify="right")
    table.add_column("Complexity", justify="right", style="magenta")
    for name, info in sorted(summary.modules.items()):
        table.add_row(
            name,
            str(info.metrics.lines),
            str(info.metrics.import_count),
            str(info.metrics.class_count),
            str(info.metrics.function_count + info.metrics.method_count),
            str(info.metrics.complexity_score),
        )
    return table


def cycle_table(summary: AnalysisSummary) -> Table:
    table = Table(title="Dependency cycles")
    table.add_column("#", justify="right")
    table.add_column("Modules", style="yellow")
    if not summary.cycles:
        table.add_row("-", "No cycles found")
    for index, cycle in enumerate(summary.cycles, start=1):
        table.add_row(str(index), " -> ".join(cycle.nodes))
    return table


def external_table(summary: AnalysisSummary) -> Table:
    table = Table(title="External imports")
    table.add_column("Package", style="green")
    table.add_column("Count", justify="right")
    if not summary.external_imports:
        table.add_row("-", "0")
    for name, count in summary.external_imports.items():
        table.add_row(name, str(count))
    return table
