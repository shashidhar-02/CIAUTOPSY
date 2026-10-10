"""JSON reporter for machine-readable diagnostic outputs with schema validation."""

from __future__ import annotations

import json

from ciautopsy.models import AnalysisReport, DiffReport


def format_json_report(report: AnalysisReport | DiffReport, indent: int = 2) -> str:
    """Serializes an AnalysisReport or DiffReport to formatted, versioned JSON."""
    return json.dumps(report.to_dict(), indent=indent)
