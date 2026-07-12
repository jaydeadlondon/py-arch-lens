import json
from pathlib import Path
from src.models import AnalysisSummary
from src.reports.check_report import validation_payload
from src.rules import ValidationResult


def write_json_report(
    summary: AnalysisSummary, path: Path, validation: ValidationResult | None = None
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "root": str(summary.root),
        "graph": summary.graph_stats,
        "cycles": [cycle.nodes for cycle in summary.cycles],
        "orphans": summary.orphan_modules,
        "external_imports": summary.external_imports,
        "top_complex_modules": summary.top_complex_modules,
        "validation": validation_payload(validation) if validation else None,
        "modules": {
            name: {
                "path": str(info.path),
                "package": info.package,
                "imports": [edge.target for edge in info.imports],
                "classes": info.classes,
                "functions": info.functions,
                "methods": info.methods,
                "calls": info.call_names,
                "syntax_error": info.syntax_error,
                "metrics": info.metrics.__dict__,
            }
            for name, info in sorted(summary.modules.items())
        },
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
