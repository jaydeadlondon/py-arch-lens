from collections import deque
from dataclasses import dataclass
from src.graph import DependencyGraph, closest_known_module
from src.models import AnalysisSummary, ModuleInfo


@dataclass
class ModuleDetail:
    module: ModuleInfo
    internal_imports: list[str]
    external_imports: list[str]
    imported_by: list[str]
    outgoing_count: int
    incoming_count: int


@dataclass
class DependencyPath:
    source: str
    target: str
    nodes: list[str]

    @property
    def found(self) -> bool:
        return bool(self.nodes)

    @property
    def text(self) -> str:
        return " -> ".join(self.nodes) if self.nodes else "No dependency path found"


def graph_from_summary(summary: AnalysisSummary) -> DependencyGraph:
    imports = [edge for module in summary.modules.values() for edge in module.imports]
    return DependencyGraph.from_imports(set(summary.modules), imports)


def module_detail(summary: AnalysisSummary, module_name: str) -> ModuleDetail | None:
    module = summary.modules.get(module_name)
    if not module:
        return None
    known_modules = set(summary.modules)
    graph = graph_from_summary(summary)
    internal: list[str] = []
    external: list[str] = []
    for edge in module.imports:
        target = closest_known_module(edge.target, known_modules)
        if target:
            internal.append(target)
        else:
            external.append(edge.target)
    return ModuleDetail(
        module=module,
        internal_imports=sorted(set(internal)),
        external_imports=sorted(set(external)),
        imported_by=sorted(graph.reverse_edges[module_name]),
        outgoing_count=len(graph.edges[module_name]),
        incoming_count=len(graph.reverse_edges[module_name]),
    )


def find_dependency_path(
    summary: AnalysisSummary, source: str, target: str
) -> DependencyPath:
    graph = graph_from_summary(summary)
    if source not in graph.nodes or target not in graph.nodes:
        return DependencyPath(source, target, [])
    queue = deque([(source, [source])])
    visited = {source}
    while queue:
        node, path = queue.popleft()
        if node == target:
            return DependencyPath(source, target, path)
        for neighbor in sorted(graph.edges[node]):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))
    return DependencyPath(source, target, [])


def filter_modules(summary: AnalysisSummary, query: str) -> list[ModuleInfo]:
    value = query.lower().strip()
    modules = sorted(summary.modules.values(), key=lambda item: item.name)
    if not value:
        return modules
    return [
        module
        for module in modules
        if value in module.name.lower() or value in str(module.path).lower()
    ]


def dependency_lines(summary: AnalysisSummary, limit: int = 200) -> list[str]:
    graph = graph_from_summary(summary)
    lines: list[str] = []
    for source in sorted(graph.nodes):
        targets = sorted(graph.edges[source])
        if targets:
            for target in targets:
                lines.append(f"{source} -> {target}")
        else:
            lines.append(f"{source}")
        if len(lines) >= limit:
            lines.append(f"... truncated after {limit} lines")
            break
    return lines
