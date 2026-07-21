from rich.table import Table
from src.snapshots import SnapshotDiff


def diff_table(diff: SnapshotDiff) -> Table:
    table = Table(title="Architecture drift")
    table.add_column("Metric", style="cyan")
    table.add_column("Count", justify="right", style="magenta")
    table.add_row("Drift score", str(diff.drift_score))
    table.add_row("Added modules", str(len(diff.added_modules)))
    table.add_row("Removed modules", str(len(diff.removed_modules)))
    table.add_row("Added edges", str(len(diff.added_edges)))
    table.add_row("Removed edges", str(len(diff.removed_edges)))
    table.add_row("New cycles", str(len(diff.new_cycles)))
    table.add_row("Resolved cycles", str(len(diff.resolved_cycles)))
    table.add_row("Complexity increases", str(len(diff.complexity_increases)))
    table.add_row("Complexity decreases", str(len(diff.complexity_decreases)))
    table.add_row("New external imports", str(len(diff.new_external_imports)))
    table.add_row("Removed external imports", str(len(diff.removed_external_imports)))
    return table


def complexity_delta_table(diff: SnapshotDiff) -> Table:
    table = Table(title="Complexity changes")
    table.add_column("Module", style="cyan")
    table.add_column("Old", justify="right")
    table.add_column("New", justify="right")
    table.add_column("Delta", justify="right", style="magenta")
    rows = diff.complexity_increases[:10] + diff.complexity_decreases[:10]
    if not rows:
        table.add_row("-", "-", "-", "No complexity changes")
    for name, old, new, delta in rows:
        table.add_row(name, str(old), str(new), str(delta))
    return table
