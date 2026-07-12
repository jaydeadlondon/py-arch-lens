import json
from pathlib import Path
from src.rules import ValidationResult


def write_check_report(result: ValidationResult, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = validation_payload(result)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def validation_payload(result: ValidationResult) -> dict:
    return {
        "ok": not result.has_errors,
        "errors": result.error_count,
        "warnings": result.warning_count,
        "violations": [
            {
                "code": item.code,
                "severity": item.severity,
                "source": item.source,
                "target": item.target,
                "line": item.line,
                "message": item.message,
                "rule": item.rule,
                "reason": item.reason,
            }
            for item in result.violations
        ],
    }
