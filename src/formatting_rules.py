from rich.table import Table
from src.rules import ValidationResult


def validation_table(result: ValidationResult) -> Table:
    table = Table(title="Architecture rule violations")
    table.add_column("Severity", style="red")
    table.add_column("Code", style="yellow")
    table.add_column("Source", style="cyan")
    table.add_column("Target", style="magenta")
    table.add_column("Line", justify="right")
    table.add_column("Message")
    if not result.violations:
        table.add_row("ok", "-", "-", "-", "-", "No rule violations found")
    for item in result.violations:
        table.add_row(
            item.severity,
            item.code,
            item.source,
            item.target,
            str(item.line or "-"),
            item.message,
        )
    return table
