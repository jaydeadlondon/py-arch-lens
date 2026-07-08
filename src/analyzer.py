from collections import Counter
from pathlib import Path
from config import ScanConfig
from graph import DependencyGraph
from models import AnalysisSummary, ImportEdge, ModuleInfo
from parser import ModuleParser
from scanner import ProjectScanner, module_name_from_path


class ArchitectureAnalyzer:
    def __init__(self, root: Path):
        self.root = root.expanduser().resolve()

    def analyze(self) -> AnalysisSummary:
        config = ScanConfig(root=self.root)
        scanner = ProjectScanner(config)
        paths = scanner.scan()
        known_modules = {module_name_from_path(self.root, path) for path in paths}
        parser = ModuleParser(self.root, known_modules)
        modules: dict[str, ModuleInfo] = {}
        all_imports: list[ImportEdge] = []
        for path in paths:
            info = parser.parse(path)
            modules[info.name] = info
            all_imports.extend(info.imports)
        graph = DependencyGraph.from_imports(set(modules), all_imports)
        external_imports = Counter(edge.target.split(".")[0] for edge in all_imports if edge.is_external and edge.target)
        top_complex = sorted(
            ((name, module.metrics.complexity_score) for name, module in modules.items()),
            key=lambda item: item[1],
            reverse=True
        )[:10]
        return AnalysisSummary(
            root=self.root,
            modules=modules,
            cycles=graph.cycles(),
            orphan_modules=graph.orphan_modules(),
            external_imports=dict(external_imports.most_common()),
            top_complex_modules=top_complex,
            graph_stats=graph.stats()
        )
