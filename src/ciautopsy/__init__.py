"""CIAUTOPSY - Evidence-based root-cause analysis for failed CI/CD pipelines."""

__version__ = "0.1.0"
__author__ = "CIAUTOPSY Contributors"

from ciautopsy.comparison.comparator import compare_logs
from ciautopsy.engine.analyzer import (
    analyze_log,
    analyze_log_content,
    analyze_target,
)
from ciautopsy.models import AnalysisReport, DiffReport, Finding, Severity

__all__ = [
    "__version__",
    "analyze_target",
    "analyze_log",
    "analyze_log_content",
    "compare_logs",
    "AnalysisReport",
    "DiffReport",
    "Finding",
    "Severity",
]
