from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
import json
from src.dependency_queries import graph_from_summary
from src.models import AnalysisSummary
from src.reports.check_report import validation_payload
from src.rules import ValidationResult


@dataclass
class SnapshotDiff:
    added_modules: list[str] = field(default_factory=list)
    removed_modules: list[str] = field(default_factory=list)
    added_edges: list[tuple[str, str]] = field(default_factory=list)
    removed_edges: list[tuple[str, str]] = field(default_factory=list)
    new_cycles: list[list[str]] = field(default_factory=list)
    resolved_cycles: list[list[str]] = field(default_factory=list)
    complexity_increases: list[tuple[str, int, int, int]] = field(default_factory=list)
    complexity_decreases: list[tuple[str, int, int, int]] = field(default_factory=list)
    new_external_imports: list[str] = field(default_factory=list)
    removed_external_imports: list[str] = field(default_factory=list)
    old_graph: dict[str, int] = field(default_factory=dict)
    new_graph: dict[str, int] = field(default_factory=dict)

    @property
    def drift_score(self) -> int:
        return (
            len(self.added_modules) * 3
            + len(self.removed_modules) * 3
            + len(self.added_edges) * 2
            + len(self.removed_edges) * 2
            + len(self.new_cycles) * 10
            + len(self.resolved_cycles) * 2
            + len(self.complexity_increases)
            + len(self.new_external_imports)
            + len(self.removed_external_imports)
        )

    @property
    def has_regression(self) -> bool:
        return bool(
            self.new_cycles
            or self.complexity_increases
            or self.added_edges
            or self.new_external_imports
        )


def create_snapshot(
    summary: AnalysisSummary, validation: ValidationResult | None = None
) -> dict[str, Any]:
    graph = graph_from_summary(summary)
    edges = sorted(
        (source, target)
        for source, targets in graph.edges.items()
        for target in targets
    )
    return {
        "schema": "pyarchlens.snapshot.v1",
        "created_at": datetime.now(UTC).isoformat(),
        "root": str(summary.root),
        "graph": summary.graph_stats,
        "modules": {
            name: {
                "path": str(info.path),
                "package": info.package,
                "lines": info.metrics.lines,
                "code_lines": info.metrics.code_lines,
                "imports": info.metrics.import_count,
                "classes": info.metrics.class_count,
                "functions": info.metrics.function_count,
                "methods": info.metrics.method_count,
                "branches": info.metrics.branch_count,
                "max_nesting": info.metrics.max_nesting,
                "complexity": info.metrics.complexity_score,
            }
            for name, info in sorted(summary.modules.items())
        },
        "edges": [{"source": source, "target": target} for source, target in edges],
        "cycles": [cycle.nodes for cycle in summary.cycles],
        "orphans": summary.orphan_modules,
        "external_imports": summary.external_imports,
        "validation": validation_payload(validation) if validation else None,
    }


def write_snapshot(
    summary: AnalysisSummary, path: Path, validation: ValidationResult | None = None
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = create_snapshot(summary, validation)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return path


def load_snapshot(path: Path) -> dict[str, Any]:
    return normalize_snapshot(json.loads(path.read_text(encoding="utf-8")))


def normalize_snapshot(payload: dict[str, Any]) -> dict[str, Any]:
    if "schema" in payload and "edges" in payload:
        return payload
    modules = payload.get("modules", {})
    edges: set[tuple[str, str]] = set()
    known = set(modules)
    for source, info in modules.items():
        for target in info.get("imports", []):
            match = _closest(target, known)
            if match and match != source:
                edges.add((source, match))
    return {
        "schema": "pyarchlens.snapshot.v1",
        "created_at": payload.get("created_at", ""),
        "root": payload.get("root", ""),
        "graph": payload.get("graph", {}),
        "modules": {
            name: {
                "path": info.get("path", ""),
                "package": info.get("package", ""),
                "lines": info.get("metrics", {}).get("lines", 0),
                "code_lines": info.get("metrics", {}).get("code_lines", 0),
                "imports": info.get("metrics", {}).get("import_count", 0),
                "classes": info.get("metrics", {}).get("class_count", 0),
                "functions": info.get("metrics", {}).get("function_count", 0),
                "methods": info.get("metrics", {}).get("method_count", 0),
                "branches": info.get("metrics", {}).get("branch_count", 0),
                "max_nesting": info.get("metrics", {}).get("max_nesting", 0),
                "complexity": info.get("metrics", {}).get("complexity_score", 0),
            }
            for name, info in modules.items()
        },
        "edges": [
            {"source": source, "target": target} for source, target in sorted(edges)
        ],
        "cycles": payload.get("cycles", []),
        "orphans": payload.get("orphans", []),
        "external_imports": payload.get("external_imports", {}),
        "validation": payload.get("validation"),
    }


def compare_snapshots(old: dict[str, Any], new: dict[str, Any]) -> SnapshotDiff:
    old_modules = set(old.get("modules", {}))
    new_modules = set(new.get("modules", {}))
    old_edges = {(item["source"], item["target"]) for item in old.get("edges", [])}
    new_edges = {(item["source"], item["target"]) for item in new.get("edges", [])}
    old_cycles = {tuple(item) for item in old.get("cycles", [])}
    new_cycles = {tuple(item) for item in new.get("cycles", [])}
    old_external = set(old.get("external_imports", {}))
    new_external = set(new.get("external_imports", {}))
    increases: list[tuple[str, int, int, int]] = []
    decreases: list[tuple[str, int, int, int]] = []
    for name in sorted(old_modules & new_modules):
        old_complexity = int(old["modules"][name].get("complexity", 0))
        new_complexity = int(new["modules"][name].get("complexity", 0))
        delta = new_complexity - old_complexity
        if delta > 0:
            increases.append((name, old_complexity, new_complexity, delta))
        elif delta < 0:
            decreases.append((name, old_complexity, new_complexity, delta))
    increases.sort(key=lambda item: item[3], reverse=True)
    decreases.sort(key=lambda item: item[3])
    return SnapshotDiff(
        added_modules=sorted(new_modules - old_modules),
        removed_modules=sorted(old_modules - new_modules),
        added_edges=sorted(new_edges - old_edges),
        removed_edges=sorted(old_edges - new_edges),
        new_cycles=[list(item) for item in sorted(new_cycles - old_cycles)],
        resolved_cycles=[list(item) for item in sorted(old_cycles - new_cycles)],
        complexity_increases=increases,
        complexity_decreases=decreases,
        new_external_imports=sorted(new_external - old_external),
        removed_external_imports=sorted(old_external - new_external),
        old_graph=old.get("graph", {}),
        new_graph=new.get("graph", {}),
    )


def diff_payload(diff: SnapshotDiff) -> dict[str, Any]:
    return {
        "drift_score": diff.drift_score,
        "has_regression": diff.has_regression,
        "graph": {"old": diff.old_graph, "new": diff.new_graph},
        "added_modules": diff.added_modules,
        "removed_modules": diff.removed_modules,
        "added_edges": [
            {"source": source, "target": target} for source, target in diff.added_edges
        ],
        "removed_edges": [
            {"source": source, "target": target}
            for source, target in diff.removed_edges
        ],
        "new_cycles": diff.new_cycles,
        "resolved_cycles": diff.resolved_cycles,
        "complexity_increases": [
            {"module": name, "old": old, "new": new, "delta": delta}
            for name, old, new, delta in diff.complexity_increases
        ],
        "complexity_decreases": [
            {"module": name, "old": old, "new": new, "delta": delta}
            for name, old, new, delta in diff.complexity_decreases
        ],
        "new_external_imports": diff.new_external_imports,
        "removed_external_imports": diff.removed_external_imports,
    }


def write_diff_report(diff: SnapshotDiff, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(diff_payload(diff), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def _closest(target: str, known: set[str]) -> str | None:
    if target in known:
        return target
    parts = target.split(".")
    while parts:
        candidate = ".".join(parts)
        if candidate in known:
            return candidate
        parts.pop()
    return None
