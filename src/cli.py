from pathlib import Path
import typer
from rich.console import Console
from src.analyzer import ArchitectureAnalyzer
from src.formatting import cycle_table, external_table, module_table, summary_panel
from src.formatting_rules import validation_table
from src.reports.html_report import write_html_report
from src.reports.json_report import write_json_report
from src.reports.check_report import write_check_report
from src.rules import load_rules
from src.validator import ArchitectureValidator
from src.dependency_queries import find_dependency_path, module_detail
from src.reports.mermaid_report import write_mermaid_report
from src.formatting_snapshots import complexity_delta_table, diff_table
from src.snapshots import (
    compare_snapshots,
    load_snapshot,
    write_diff_report,
    write_snapshot,
)

app = typer.Typer(help="Analyze Python project architecture")
console = Console()


@app.command()
def analyze(
    path: Path = typer.Argument(Path("."), exists=True, file_okay=False)
) -> None:
    summary = ArchitectureAnalyzer(path).analyze()
    console.print(summary_panel(summary))
    console.print(module_table(summary))
    console.print(cycle_table(summary))
    console.print(external_table(summary))


@app.command()
def report(
    path: Path = typer.Argument(Path("."), exists=True, file_okay=False),
    out: Path = typer.Option(Path("reports")),
    config: Path | None = typer.Option(None, "--config", "-c"),
) -> None:
    summary = ArchitectureAnalyzer(path).analyze()
    validation = None
    if config:
        rules = load_rules(config)
        validation = ArchitectureValidator(rules).validate(summary)
    json_path = write_json_report(summary, out / "pyarchlens_report.json", validation)
    html_path = write_html_report(summary, out / "pyarchlens_report.html", validation)
    console.print(f"JSON report: {json_path}")
    console.print(f"HTML report: {html_path}")


@app.command()
def check(
    path: Path = typer.Argument(Path("."), exists=True, file_okay=False),
    config: Path = typer.Option(
        Path("pyarchlens.yml"), "--config", "-c", exists=True, file_okay=True
    ),
    out: Path | None = typer.Option(None, "--out"),
) -> None:
    summary = ArchitectureAnalyzer(path).analyze()
    rules = load_rules(config)
    result = ArchitectureValidator(rules).validate(summary)
    console.print(summary_panel(summary))
    console.print(validation_table(result))
    if out:
        report_path = write_check_report(result, out)
        console.print(f"Check report: {report_path}")
    if result.has_errors:
        raise typer.Exit(1)


@app.command()
def path(
    project: Path = typer.Argument(Path("."), exists=True, file_okay=False),
    source: str = typer.Argument(...),
    target: str = typer.Argument(...),
) -> None:
    summary = ArchitectureAnalyzer(project).analyze()
    result = find_dependency_path(summary, source, target)
    if result.found:
        console.print(result.text)
    else:
        console.print(f"No dependency path from {source} to {target}")
        raise typer.Exit(1)


@app.command()
def module(
    project: Path = typer.Argument(Path("."), exists=True, file_okay=False),
    name: str = typer.Argument(...),
) -> None:
    summary = ArchitectureAnalyzer(project).analyze()
    detail = module_detail(summary, name)
    if not detail:
        console.print(f"Module not found: {name}")
        raise typer.Exit(1)
    console.print(f"Module: {detail.module.name}")
    console.print(f"Path: {detail.module.path}")
    console.print(f"Lines: {detail.module.metrics.lines}")
    console.print(f"Complexity: {detail.module.metrics.complexity_score}")
    console.print(f"Incoming: {detail.incoming_count}")
    console.print(f"Outgoing: {detail.outgoing_count}")
    console.print(f"Classes: {', '.join(detail.module.classes) or '-'}")
    console.print(f"Functions: {', '.join(detail.module.functions) or '-'}")
    console.print(f"Internal imports: {', '.join(detail.internal_imports) or '-'}")
    console.print(f"Imported by: {', '.join(detail.imported_by) or '-'}")
    console.print(f"External imports: {', '.join(detail.external_imports) or '-'}")


@app.command()
def mermaid(
    project: Path = typer.Argument(Path("."), exists=True, file_okay=False),
    out: Path = typer.Option(Path("reports/dependencies.mmd")),
) -> None:
    summary = ArchitectureAnalyzer(project).analyze()
    path = write_mermaid_report(summary, out)
    console.print(f"Mermaid graph: {path}")


@app.command()
def snapshot(
    project: Path = typer.Argument(Path("."), exists=True, file_okay=False),
    out: Path = typer.Option(Path("snapshots/architecture.json")),
    config: Path | None = typer.Option(None, "--config", "-c"),
) -> None:
    summary = ArchitectureAnalyzer(project).analyze()
    validation = None
    if config:
        rules = load_rules(config)
        validation = ArchitectureValidator(rules).validate(summary)
    path = write_snapshot(summary, out, validation)
    console.print(f"Snapshot: {path}")


@app.command()
def compare(
    old: Path = typer.Argument(..., exists=True, dir_okay=False),
    new: Path = typer.Argument(..., exists=True, dir_okay=False),
    out: Path | None = typer.Option(None, "--out"),
    max_drift: int | None = typer.Option(None, "--max-drift"),
    fail_on_regression: bool = typer.Option(False, "--fail-on-regression"),
) -> None:
    old_snapshot = load_snapshot(old)
    new_snapshot = load_snapshot(new)
    diff = compare_snapshots(old_snapshot, new_snapshot)
    console.print(diff_table(diff))
    console.print(complexity_delta_table(diff))
    if out:
        path = write_diff_report(diff, out)
        console.print(f"Comparison report: {path}")
    if max_drift is not None and diff.drift_score > max_drift:
        raise typer.Exit(1)
    if fail_on_regression and diff.has_regression:
        raise typer.Exit(1)


@app.command()
def tui(path: Path = typer.Argument(Path("."), exists=True, file_okay=False)) -> None:
    try:
        from src.tui import run_tui
    except Exception as exc:
        console.print(f"TUI is unavailable: {exc}")
        raise typer.Exit(1)
    run_tui(path)
