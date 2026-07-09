from pathlib import Path
from src.scanner import module_name_from_path, package_name_from_module


def test_module_name_from_regular_file(tmp_path: Path):
    path = tmp_path / "pkg" / "feature.py"
    path.parent.mkdir()
    path.write_text("x = 1", encoding="utf-8")
    assert module_name_from_path(tmp_path, path) == "pkg.feature"


def test_module_name_from_init_file(tmp_path: Path):
    path = tmp_path / "pkg" / "__init__.py"
    path.parent.mkdir()
    path.write_text("x = 1", encoding="utf-8")
    assert module_name_from_path(tmp_path, path) == "pkg"


def test_package_name_from_module():
    assert package_name_from_module("pkg.feature.tool") == "pkg"
