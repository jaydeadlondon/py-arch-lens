from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ScanConfig:
    root: Path
    include_external: bool = True
    excluded_dirs: set[str] = field(default_factory=lambda: {
        ".git",
        ".hg",
        ".svn",
        ".venv",
        "venv",
        "env",
        "__pycache__",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        "node_modules",
        "dist",
        "build",
        "coverage"
    })
    excluded_files: set[str] = field(default_factory=set)

    @property
    def normalized_root(self) -> Path:
        return self.root.expanduser().resolve()
