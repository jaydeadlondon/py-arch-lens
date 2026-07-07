from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ImportEdge:
    source: str
    target: str
    imported_name: str
    line: int
    is_external: bool = False


@dataclass
class ModuleMetrics:
    lines: int = 0
    code_lines: int = 0
    import_count: int = 0
    class_count: int = 0
    function_count: int = 0
    method_count: int = 0
    async_function_count: int = 0
    branch_count: int = 0
    max_nesting: int = 0
    complexity_score: int = 0


@dataclass
class ModuleInfo:
    name: str
    path: Path
    package: str
    imports: list[ImportEdge] = field(default_factory=list)
    classes: list[str] = field(default_factory=list)
    functions: list[str] = field(default_factory=list)
    methods: dict[str, list[str]] = field(default_factory=dict)
    call_names: list[str] = field(default_factory=list)
    metrics: ModuleMetrics = field(default_factory=ModuleMetrics)
    syntax_error: str | None = None


@dataclass
class Cycle:
    nodes: list[str]


@dataclass
class AnalysisSummary:
    root: Path
    modules: dict[str, ModuleInfo]
    cycles: list[Cycle]
    orphan_modules: list[str]
    external_imports: dict[str, int]
    top_complex_modules: list[tuple[str, int]]
    graph_stats: dict[str, Any]
