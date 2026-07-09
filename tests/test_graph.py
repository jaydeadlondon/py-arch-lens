from src.graph import DependencyGraph, closest_known_module
from src.models import ImportEdge


def test_closest_known_module():
    assert (
        closest_known_module(
            "app.core.models.User", {"app", "app.core", "app.core.models"}
        )
        == "app.core.models"
    )


def test_cycle_detection():
    imports = [
        ImportEdge("a", "b", "b", 1),
        ImportEdge("b", "c", "c", 1),
        ImportEdge("c", "a", "a", 1),
    ]
    graph = DependencyGraph.from_imports({"a", "b", "c"}, imports)
    cycles = graph.cycles()
    assert len(cycles) == 1
    assert cycles[0].nodes == ["a", "b", "c"]


def test_orphans():
    graph = DependencyGraph()
    graph.add_node("a")
    graph.add_node("b")
    graph.add_edge("b", "c")
    assert graph.orphan_modules() == ["a"]
