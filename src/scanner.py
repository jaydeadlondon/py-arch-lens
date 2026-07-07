from pathlib import Path
from config import ScanConfig


class ProjectScanner:
    def __init__(self, config: ScanConfig):
        self.config = config

    def scan(self) -> list[Path]:
        root = self.config.normalized_root
        files: list[Path] = []
        for path in root.rglob("*.py"):
            if self._is_allowed(path):
                files.append(path)
        return sorted(files)

    def _is_allowed(self, path: Path) -> bool:
        root = self.config.normalized_root
        relative = path.relative_to(root)
        if path.name in self.config.excluded_files:
            return False
        return not any(part in self.config.excluded_dirs for part in relative.parts)


def module_name_from_path(root: Path, path: Path) -> str:
    relative = path.resolve().relative_to(root.resolve())
    parts = list(relative.with_suffix("").parts)
    if parts[-1] == "__init__":
        parts = parts[:-1]
    if parts and parts[0] == "src":
        parts = parts[1:]
    return ".".join(parts) if parts else path.stem


def package_name_from_module(module_name: str) -> str:
    parts = module_name.split(".")
    return parts[0] if parts else module_name
