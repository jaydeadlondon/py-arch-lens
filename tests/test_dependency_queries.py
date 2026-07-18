from pathlib import Path
from src.analyzer import ArchitectureAnalyzer
from src.dependency_queries import (
    dependency_lines,
    filter_modules,
    find_dependency_path,
    module_detail,
)


def test_find_dependency_path(tmp_path: Path):
    pkg = tmp_path / "app"
    pkg.mkdir()
    (pkg / "a.py").write_text("from app import b\n", encoding="utf-8")
    (pkg / "b.py").write_text("from app import c\n", encoding="utf-8")
    (pkg / "c.py").write_text("x = 1\n", encoding="utf-8")
    summary = ArchitectureAnalyzer(tmp_path).analyze()
    result = find_dependency_path(summary, "app.a", "app.c")
    assert result.found
    assert result.nodes == ["app.a", "app.b", "app.c"]


def test_module_detail_and_filter(tmp_path: Path):
    pkg = tmp_path / "app"
    pkg.mkdir()
    (pkg / "a.py").write_text(
        "import os\nfrom app import b\nclass A:\n    pass\n", encoding="utf-8"
    )
    (pkg / "b.py").write_text("x = 1\n", encoding="utf-8")
    summary = ArchitectureAnalyzer(tmp_path).analyze()
    detail = module_detail(summary, "app.a")
    assert detail is not None
    assert detail.internal_imports == ["app.b"]
    assert detail.external_imports == ["os"]
    assert filter_modules(summary, "a")
    assert any("app.a -> app.b" in line for line in dependency_lines(summary))
