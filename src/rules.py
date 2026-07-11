from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import fnmatch


@dataclass
class ForbiddenImportRule:
    source: str
    target: str
    reason: str = ""
    severity: str = "error"


@dataclass
class LayerRule:
    name: str
    modules: list[str]
    may_depend_on: list[str] = field(default_factory=list)


@dataclass
class IgnoreRule:
    source: str
    target: str


@dataclass
class ArchitectureRules:
    layers: list[LayerRule] = field(default_factory=list)
    forbidden_imports: list[ForbiddenImportRule] = field(default_factory=list)
    ignore: list[IgnoreRule] = field(default_factory=list)


@dataclass
class RuleViolation:
    code: str
    severity: str
    source: str
    target: str
    message: str
    rule: str
    line: int | None = None
    reason: str = ""


@dataclass
class ValidationResult:
    violations: list[RuleViolation] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(item.severity == "error" for item in self.violations)

    @property
    def error_count(self) -> int:
        return sum(1 for item in self.violations if item.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for item in self.violations if item.severity == "warning")


def load_rules(path: Path) -> ArchitectureRules:
    try:
        import yaml
    except Exception as exc:
        raise RuntimeError("PyYAML is required to load architecture rules") from exc
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return rules_from_mapping(payload)


def rules_from_mapping(payload: dict[str, Any]) -> ArchitectureRules:
    return ArchitectureRules(
        layers=[
            LayerRule(
                name=str(item.get("name", "")),
                modules=list(item.get("modules", [])),
                may_depend_on=list(item.get("may_depend_on", [])),
            )
            for item in payload.get("layers", [])
        ],
        forbidden_imports=[
            ForbiddenImportRule(
                source=str(item.get("source", "*")),
                target=str(item.get("target", "*")),
                reason=str(item.get("reason", "")),
                severity=str(item.get("severity", "error")),
            )
            for item in payload.get("forbidden_imports", [])
        ],
        ignore=[
            IgnoreRule(
                source=str(item.get("source", "")), target=str(item.get("target", ""))
            )
            for item in payload.get("ignore", [])
        ],
    )


def matches_pattern(value: str, pattern: str) -> bool:
    return fnmatch.fnmatchcase(value, pattern)
