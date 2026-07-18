from pathlib import Path
from src.analyzer import ArchitectureAnalyzer
from src.reports.mermaid_report import render_mermaid, write_mermaid_report


def test_mermaid_rendering(tmp_path: Path):
    pkg = tmp_path / "app"
    pkg.mkdir()
    (pkg / "a.py").write_text("from app import b\n", encoding="utf-8")
    (pkg / "b.py").write_text("x = 1\n", encoding="utf-8")
    summary = ArchitectureAnalyzer(tmp_path).analyze()
    text = render_mermaid(summary)
    assert "flowchart LR" in text
    assert "app.a" in text
    assert "-->" in text


def test_mermaid_writer(tmp_path: Path):
    pkg = tmp_path / "app"
    pkg.mkdir()
    (pkg / "a.py").write_text("from app import b\n", encoding="utf-8")
    (pkg / "b.py").write_text("x = 1\n", encoding="utf-8")
    summary = ArchitectureAnalyzer(tmp_path).analyze()
    out = write_mermaid_report(summary, tmp_path / "graph.mmd")
    assert out.exists()
    assert out.read_text(encoding="utf-8").startswith("flowchart LR")
