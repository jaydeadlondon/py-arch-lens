from src.graph import closest_known_module
from src.models import AnalysisSummary
from src.rules import (
    ArchitectureRules,
    RuleViolation,
    ValidationResult,
    matches_pattern,
)


class ArchitectureValidator:
    def __init__(self, rules: ArchitectureRules):
        self.rules = rules

    def validate(self, summary: AnalysisSummary) -> ValidationResult:
        result = ValidationResult()
        known_modules = set(summary.modules)
        for module in summary.modules.values():
            for edge in module.imports:
                target = closest_known_module(edge.target, known_modules) or edge.target
                if self._is_ignored(edge.source, target):
                    continue
                forbidden = self._validate_forbidden_import(
                    edge.source, target, edge.line
                )
                if forbidden:
                    result.violations.append(forbidden)
                layer = self._validate_layer(
                    edge.source, target, known_modules, edge.line
                )
                if layer:
                    result.violations.append(layer)
        result.violations.sort(
            key=lambda item: (
                item.severity,
                item.code,
                item.source,
                item.target,
                item.line or 0,
            )
        )
        return result

    def _validate_forbidden_import(
        self, source: str, target: str, line: int | None
    ) -> RuleViolation | None:
        for rule in self.rules.forbidden_imports:
            if matches_pattern(source, rule.source) and matches_pattern(
                target, rule.target
            ):
                return RuleViolation(
                    code="forbidden_import",
                    severity=rule.severity,
                    source=source,
                    target=target,
                    line=line,
                    rule=f"{rule.source} -> {rule.target}",
                    reason=rule.reason,
                    message=f"{source} imports {target}, but this import is forbidden",
                )
        return None

    def _validate_layer(
        self, source: str, target: str, known_modules: set[str], line: int | None
    ) -> RuleViolation | None:
        if target not in known_modules:
            return None
        source_layer = self._layer_for_module(source)
        target_layer = self._layer_for_module(target)
        if not source_layer or not target_layer:
            return None
        if source_layer.name == target_layer.name:
            return None
        if target_layer.name in source_layer.may_depend_on:
            return None
        return RuleViolation(
            code="layer_violation",
            severity="error",
            source=source,
            target=target,
            line=line,
            rule=f"layer {source_layer.name} may depend on {source_layer.may_depend_on}",
            reason=f"Layer {source_layer.name} is not allowed to depend on layer {target_layer.name}",
            message=f"{source} imports {target}, crossing from {source_layer.name} to forbidden layer {target_layer.name}",
        )

    def _layer_for_module(self, module: str):
        for layer in self.rules.layers:
            if any(matches_pattern(module, pattern) for pattern in layer.modules):
                return layer
        return None

    def _is_ignored(self, source: str, target: str) -> bool:
        return any(
            matches_pattern(source, item.source)
            and matches_pattern(target, item.target)
            for item in self.rules.ignore
        )
