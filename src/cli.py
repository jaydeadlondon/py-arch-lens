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
def tui(path: Path = typer.Argument(Path("."), exists=True, file_okay=False)) -> None:
    try:
        from src.tui import run_tui
    except Exception as exc:
        console.print(f"TUI is unavailable: {exc}")
        raise typer.Exit(1)
    run_tui(path)
