from pathlib import Path
from src.analyzer import ArchitectureAnalyzer
from src.dependency_queries import dependency_lines, filter_modules, module_detail


def run_tui(path: Path) -> None:
    try:
        from textual.app import App, ComposeResult
        from textual.containers import Container
        from textual.widgets import (
            DataTable,
            Footer,
            Header,
            Input,
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
        Input { margin: 1; }
        DataTable { height: 1fr; }
        #stats { height: auto; border: solid #38bdf8; }
        #module_detail { height: auto; border: solid #64748b; }
        #graph_view { height: 1fr; border: solid #64748b; }
        TabPane { padding: 1; }
        """
        BINDINGS = [("q", "quit", "Quit"), ("r", "refresh", "Refresh")]

        def __init__(self, root: Path):
            super().__init__()
            self.root = root
            self.summary = ArchitectureAnalyzer(root).analyze()
            self.query = ""

        def compose(self) -> ComposeResult:
            yield Header()
            yield Container(Static(self._stats_text(), id="stats"))
            with TabbedContent():
                with TabPane("Modules"):
                    yield Input(placeholder="Filter modules", id="module_filter")
                    yield DataTable(id="modules")
                    yield Static("Select a module to see details", id="module_detail")
                with TabPane("Graph"):
                    yield Static(
                        "\n".join(dependency_lines(self.summary)), id="graph_view"
                    )
                with TabPane("Cycles"):
                    yield DataTable(id="cycles")
                with TabPane("External"):
                    yield DataTable(id="external")
            yield Footer()

        def on_mount(self) -> None:
            self._fill_tables()

        def on_input_changed(self, event: Input.Changed) -> None:
            if event.input.id == "module_filter":
                self.query = event.value
                self._fill_modules()

        def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
            if event.data_table.id == "modules":
                row = event.data_table.get_row(event.row_key)
                if row:
                    self._show_module_detail(str(row[0]))

        def action_refresh(self) -> None:
            self.summary = ArchitectureAnalyzer(self.root).analyze()
            stats = self.query_one("#stats", Static)
            stats.update(self._stats_text())
            graph = self.query_one("#graph_view", Static)
            graph.update("\n".join(dependency_lines(self.summary)))
            self._fill_tables()

        def _stats_text(self) -> str:
            stats = self.summary.graph_stats
            return f"Root: {self.summary.root}\nModules: {len(self.summary.modules)}  Edges: {stats.get('edges', 0)}  Cycles: {len(self.summary.cycles)}  Orphans: {len(self.summary.orphan_modules)}"

        def _fill_tables(self) -> None:
            self._fill_modules()
            self._fill_cycles()
            self._fill_external()

        def _fill_modules(self) -> None:
            modules = self.query_one("#modules", DataTable)
            modules.clear(columns=True)
            modules.add_columns("Module", "Lines", "Imports", "In", "Out", "Complexity")
            for info in filter_modules(self.summary, self.query):
                detail = module_detail(self.summary, info.name)
                incoming = str(detail.incoming_count) if detail else "0"
                outgoing = str(detail.outgoing_count) if detail else "0"
                modules.add_row(
                    info.name,
                    str(info.metrics.lines),
                    str(info.metrics.import_count),
                    incoming,
                    outgoing,
                    str(info.metrics.complexity_score),
                )

        def _fill_cycles(self) -> None:
            cycles = self.query_one("#cycles", DataTable)
            cycles.clear(columns=True)
            cycles.add_columns("#", "Modules")
            if self.summary.cycles:
                for index, cycle in enumerate(self.summary.cycles, start=1):
                    cycles.add_row(str(index), " -> ".join(cycle.nodes))
            else:
                cycles.add_row("-", "No cycles found")

        def _fill_external(self) -> None:
            external = self.query_one("#external", DataTable)
            external.clear(columns=True)
            external.add_columns("Package", "Count")
            if self.summary.external_imports:
                for name, count in self.summary.external_imports.items():
                    external.add_row(name, str(count))
            else:
                external.add_row("-", "0")

        def _show_module_detail(self, name: str) -> None:
            target = self.query_one("#module_detail", Static)
            detail = module_detail(self.summary, name)
            if not detail:
                target.update(f"Module not found: {name}")
                return
            text = [
                f"Module: {detail.module.name}",
                f"Path: {detail.module.path}",
                f"Lines: {detail.module.metrics.lines}",
                f"Complexity: {detail.module.metrics.complexity_score}",
                f"Incoming: {detail.incoming_count}",
                f"Outgoing: {detail.outgoing_count}",
                f"Classes: {', '.join(detail.module.classes) or '-'}",
                f"Functions: {', '.join(detail.module.functions) or '-'}",
                f"Internal imports: {', '.join(detail.internal_imports) or '-'}",
                f"Imported by: {', '.join(detail.imported_by) or '-'}",
                f"External imports: {', '.join(detail.external_imports) or '-'}",
            ]
            target.update("\n".join(text))

    PyArchLensApp(path).run()


def _fallback_tui(path: Path) -> None:
    from rich.console import Console
    from src.formatting import cycle_table, external_table, module_table, summary_panel

    console = Console()
    summary = ArchitectureAnalyzer(path).analyze()
    console.print(summary_panel(summary))
    console.print(module_table(summary))
    console.print(cycle_table(summary))
    console.print(external_table(summary))
