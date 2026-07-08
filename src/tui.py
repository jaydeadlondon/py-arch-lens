from pathlib import Path
from analyzer import ArchitectureAnalyzer


def run_tui(path: Path) -> None:
    try:
        from textual.app import App, ComposeResult
        from textual.containers import Container, Horizontal
        from textual.widgets import (
            DataTable,
            Footer,
            Header,
            Static,
            TabbedContent,
            TabPane,
        )
    except Exception:
        _fallback_tui(path)
        return

    class PyArchLensApp(App):
        CSS = """
        Screen { background: #0f172a; }
        Static { padding: 1; }
        DataTable { height: 1fr; }
        #stats { height: auto; border: solid #38bdf8; }
        TabPane { padding: 1; }
        """
        BINDINGS = [("q", "quit", "Quit"), ("r", "refresh", "Refresh")]

        def __init__(self, root: Path):
            super().__init__()
            self.root = root
            self.summary = ArchitectureAnalyzer(root).analyze()

        def compose(self) -> ComposeResult:
            yield Header()
            yield Container(Static(self._stats_text(), id="stats"))
            with TabbedContent():
                with TabPane("Modules"):
                    yield DataTable(id="modules")
                with TabPane("Cycles"):
                    yield DataTable(id="cycles")
                with TabPane("External"):
                    yield DataTable(id="external")
            yield Footer()

        def on_mount(self) -> None:
            self._fill_tables()

        def action_refresh(self) -> None:
            self.summary = ArchitectureAnalyzer(self.root).analyze()
            stats = self.query_one("#stats", Static)
            stats.update(self._stats_text())
            self._fill_tables()

        def _stats_text(self) -> str:
            stats = self.summary.graph_stats
            return f"Root: {self.summary.root}\nModules: {len(self.summary.modules)}  Edges: {stats.get('edges', 0)}  Cycles: {len(self.summary.cycles)}  Orphans: {len(self.summary.orphan_modules)}"

        def _fill_tables(self) -> None:
            modules = self.query_one("#modules", DataTable)
            modules.clear(columns=True)
            modules.add_columns(
                "Module", "Lines", "Imports", "Classes", "Functions", "Complexity"
            )
            for name, info in sorted(self.summary.modules.items()):
                modules.add_row(
                    name,
                    str(info.metrics.lines),
                    str(info.metrics.import_count),
                    str(info.metrics.class_count),
                    str(info.metrics.function_count + info.metrics.method_count),
                    str(info.metrics.complexity_score),
                )
            cycles = self.query_one("#cycles", DataTable)
            cycles.clear(columns=True)
            cycles.add_columns("#", "Modules")
            if self.summary.cycles:
                for index, cycle in enumerate(self.summary.cycles, start=1):
                    cycles.add_row(str(index), " -> ".join(cycle.nodes))
            else:
                cycles.add_row("-", "No cycles found")
            external = self.query_one("#external", DataTable)
            external.clear(columns=True)
            external.add_columns("Package", "Count")
            if self.summary.external_imports:
                for name, count in self.summary.external_imports.items():
                    external.add_row(name, str(count))
            else:
                external.add_row("-", "0")

    PyArchLensApp(path).run()


def _fallback_tui(path: Path) -> None:
    from rich.console import Console
    from formatting import cycle_table, external_table, module_table, summary_panel

    console = Console()
    summary = ArchitectureAnalyzer(path).analyze()
    console.print(summary_panel(summary))
    console.print(module_table(summary))
    console.print(cycle_table(summary))
    console.print(external_table(summary))
