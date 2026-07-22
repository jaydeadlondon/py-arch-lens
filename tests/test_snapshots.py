from pathlib import Path
from src.analyzer import ArchitectureAnalyzer
from src.snapshots import (
    compare_snapshots,
    create_snapshot,
    diff_payload,
    load_snapshot,
    write_diff_report,
    write_snapshot,
)


def test_snapshot_creation_and_loading(tmp_path: Path):
    pkg = tmp_path / "app"
    pkg.mkdir()
    (pkg / "a.py").write_text("from app import b\n", encoding="utf-8")
    (pkg / "b.py").write_text("x = 1\n", encoding="utf-8")
    summary = ArchitectureAnalyzer(tmp_path).analyze()
    snapshot = create_snapshot(summary)
    assert snapshot["schema"] == "pyarchlens.snapshot.v1"
    assert "app.a" in snapshot["modules"]
    path = write_snapshot(summary, tmp_path / "snapshot.json")
    loaded = load_snapshot(path)
    assert loaded["modules"] == snapshot["modules"]


def test_snapshot_comparison(tmp_path: Path):
    old = {
        "schema": "pyarchlens.snapshot.v1",
        "graph": {"nodes": 1, "edges": 0},
        "modules": {"app.a": {"complexity": 10}},
        "edges": [],
        "cycles": [],
        "external_imports": {},
    }
    new = {
        "schema": "pyarchlens.snapshot.v1",
        "graph": {"nodes": 2, "edges": 1},
        "modules": {"app.a": {"complexity": 12}, "app.b": {"complexity": 1}},
        "edges": [{"source": "app.a", "target": "app.b"}],
        "cycles": [],
        "external_imports": {"rich": 1},
    }
    diff = compare_snapshots(old, new)
    payload = diff_payload(diff)
    assert diff.added_modules == ["app.b"]
    assert diff.added_edges == [("app.a", "app.b")]
    assert payload["drift_score"] > 0
    out = write_diff_report(diff, tmp_path / "diff.json")
    assert out.exists()
