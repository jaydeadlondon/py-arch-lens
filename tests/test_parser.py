from pathlib import Path
from src.parser import ModuleParser


def test_parser_collects_metrics(tmp_path: Path):
    path = tmp_path / "pkg" / "mod.py"
    path.parent.mkdir()
    path.write_text(
        """
import os
from pkg import other

class User:
    def name(self):
        if True:
            return os.getcwd()

def build():
    return User()
""".strip(),
        encoding="utf-8",
    )
    parser = ModuleParser(tmp_path, {"pkg.mod", "pkg.other"})
    info = parser.parse(path)
    assert info.name == "pkg.mod"
    assert info.metrics.import_count == 2
    assert info.metrics.class_count == 1
    assert info.metrics.function_count == 1
    assert info.metrics.method_count == 1
    assert info.metrics.branch_count == 1
    assert "User" in info.call_names
