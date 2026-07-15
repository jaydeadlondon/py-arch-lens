from pathlib import Path
from src.analyzer import ArchitectureAnalyzer
from src.rules import rules_from_mapping
from src.validator import ArchitectureValidator


def test_forbidden_import_detection(tmp_path: Path):
    pkg = tmp_path / "app"
    tests = tmp_path / "tests"
    pkg.mkdir()
    tests.mkdir()
    (pkg / "main.py").write_text("from tests import helper\n", encoding="utf-8")
    (tests / "helper.py").write_text("x = 1\n", encoding="utf-8")
    summary = ArchitectureAnalyzer(tmp_path).analyze()
    rules = rules_from_mapping(
        {"forbidden_imports": [{"source": "app.*", "target": "tests.*"}]}
    )
    result = ArchitectureValidator(rules).validate(summary)
    assert result.has_errors
    assert result.violations[0].code == "forbidden_import"


def test_layer_violation_detection(tmp_path: Path):
    pkg = tmp_path / "app"
    pkg.mkdir()
    (pkg / "ui.py").write_text("from app import db\n", encoding="utf-8")
    (pkg / "db.py").write_text("x = 1\n", encoding="utf-8")
    summary = ArchitectureAnalyzer(tmp_path).analyze()
    rules = rules_from_mapping(
        {
            "layers": [
                {"name": "ui", "modules": ["app.ui"], "may_depend_on": []},
                {"name": "database", "modules": ["app.db"], "may_depend_on": []},
            ]
        }
    )
    result = ArchitectureValidator(rules).validate(summary)
    assert result.has_errors
    assert result.violations[0].code == "layer_violation"
