from collections import defaultdict, deque
from src.models import Cycle, ImportEdge


class DependencyGraph:
    def __init__(self):
        self.nodes: set[str] = set()
        self.edges: dict[str, set[str]] = defaultdict(set)
        self.reverse_edges: dict[str, set[str]] = defaultdict(set)

    def add_node(self, node: str) -> None:
        self.nodes.add(node)
        self.edges.setdefault(node, set())
        self.reverse_edges.setdefault(node, set())

    def add_edge(self, source: str, target: str) -> None:
        self.add_node(source)
        self.add_node(target)
        self.edges[source].add(target)
        self.reverse_edges[target].add(source)

    @classmethod
    def from_imports(
        cls, module_names: set[str], imports: list[ImportEdge]
    ) -> "DependencyGraph":
        graph = cls()
        for name in module_names:
            graph.add_node(name)
        for edge in imports:
            target = closest_known_module(edge.target, module_names)
            if target and edge.source != target:
                graph.add_edge(edge.source, target)
        return graph

    def cycles(self) -> list[Cycle]:
        index = 0
        stack: list[str] = []
        indices: dict[str, int] = {}
        lowlinks: dict[str, int] = {}
        on_stack: set[str] = set()
        result: list[Cycle] = []

        def strongconnect(node: str) -> None:
            nonlocal index
            indices[node] = index
            lowlinks[node] = index
            index += 1
            stack.append(node)
            on_stack.add(node)
            for neighbor in self.edges.get(node, set()):
                if neighbor not in indices:
                    strongconnect(neighbor)
                    lowlinks[node] = min(lowlinks[node], lowlinks[neighbor])
                elif neighbor in on_stack:
                    lowlinks[node] = min(lowlinks[node], indices[neighbor])
            if lowlinks[node] == indices[node]:
                component: list[str] = []
                while True:
                    item = stack.pop()
                    on_stack.remove(item)
                    component.append(item)
                    if item == node:
                        break
                if len(component) > 1 or node in self.edges.get(node, set()):
                    result.append(Cycle(sorted(component)))

        for node in sorted(self.nodes):
            if node not in indices:
                strongconnect(node)
        return sorted(result, key=lambda cycle: (len(cycle.nodes), cycle.nodes))

    def orphan_modules(self) -> list[str]:
        return sorted(
            node
            for node in self.nodes
            if not self.edges[node] and not self.reverse_edges[node]
        )

    def topological_layers(self) -> list[list[str]]:
        indegree = {node: len(self.reverse_edges[node]) for node in self.nodes}
        queue = deque(sorted(node for node, degree in indegree.items() if degree == 0))
        layers: list[list[str]] = []
        visited: set[str] = set()
        while queue:
            layer = list(queue)
            queue.clear()
            layers.append(layer)
            for node in layer:
                visited.add(node)
                for neighbor in sorted(self.edges[node]):
                    indegree[neighbor] -= 1
                    if indegree[neighbor] == 0:
                        queue.append(neighbor)
        remaining = sorted(self.nodes - visited)
        if remaining:
            layers.append(remaining)
        return layers

    def stats(self) -> dict[str, int]:
        edge_count = sum(len(targets) for targets in self.edges.values())
        return {
            "nodes": len(self.nodes),
            "edges": edge_count,
            "orphans": len(self.orphan_modules()),
            "cycles": len(self.cycles()),
        }


def closest_known_module(target: str, known_modules: set[str]) -> str | None:
    if target in known_modules:
        return target
    parts = target.split(".")
    while parts:
        candidate = ".".join(parts)
        if candidate in known_modules:
            return candidate
        parts.pop()
    return None
