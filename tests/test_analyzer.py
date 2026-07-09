from pathlib import Path
from src.analyzer import ArchitectureAnalyzer


def test_analyzer_detects_cycle(tmp_path: Path):
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "a.py").write_text("from pkg import b\n", encoding="utf-8")
    (pkg / "b.py").write_text("from pkg import a\n", encoding="utf-8")
    summary = ArchitectureAnalyzer(tmp_path).analyze()
    assert len(summary.modules) == 2
    assert len(summary.cycles) == 1
