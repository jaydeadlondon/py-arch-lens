from pathlib import Path
import typer
from rich.console import Console
from src.analyzer import ArchitectureAnalyzer
from src.formatting import cycle_table, external_table, module_table, summary_panel
from src.reports.html_report import write_html_report
from src.reports.json_report import write_json_report

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
) -> None:
    summary = ArchitectureAnalyzer(path).analyze()
    json_path = write_json_report(summary, out / "pyarchlens_report.json")
    html_path = write_html_report(summary, out / "pyarchlens_report.html")
    console.print(f"JSON report: {json_path}")
    console.print(f"HTML report: {html_path}")


@app.command()
def tui(path: Path = typer.Argument(Path("."), exists=True, file_okay=False)) -> None:
    try:
        from tui import run_tui
    except Exception as exc:
        console.print(f"TUI is unavailable: {exc}")
        raise typer.Exit(1)
    run_tui(path)
