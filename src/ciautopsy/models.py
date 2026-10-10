"""Domain data models for CIAUTOPSY log analysis, evidence linking, and reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

SCHEMA_VERSION = "0.1.0"


class Severity(str, Enum):
    """Diagnostic severity levels."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class Category(str, Enum):
    """Categorization for failure modes and pipeline bottlenecks."""

    DEPENDENCY = "Dependency Resolution"
    OUT_OF_MEMORY = "Resource / Memory (OOM)"
    TIMEOUT = "Execution Timeout"
    TEST_FAILURE = "Test Suite Failure"
    BUILD_SYNTAX = "Build / Compilation Syntax"
    PERMISSION_AUTH = "Authentication & Secrets"
    INFRASTRUCTURE = "CI Infrastructure & Environment"
    CASCADING_FAILURE = "Downstream Cascading Error"
    UNKNOWN_AMBIGUOUS = "Unknown / Ambiguous Failure"


@dataclass(slots=True)
class LogLine:
    """Represents a single normalized line from a CI/CD build log."""

    line_number: int
    raw_text: str
    clean_text: str
    timestamp: str | None = None
    step_name: str | None = None


@dataclass(slots=True)
class Evidence:
    """Concrete proof linking a diagnostic finding back to original log line(s)."""

    line_number: int
    matched_text: str
    context_lines: list[tuple[int, str]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert evidence to dictionary representation."""
        return {
            "line_number": self.line_number,
            "matched_text": self.matched_text,
            "context_lines": [
                {"line": line_num, "text": text} for line_num, text in self.context_lines
            ],
            "metadata": self.metadata,
        }


@dataclass(slots=True)
class Finding:
    """A detected diagnostic hypothesis backed by concrete log evidence."""

    rule_id: str
    title: str
    description: str
    category: Category
    severity: Severity
    remediation: str
    evidence: list[Evidence] = field(default_factory=list)
    confidence: float = 0.90
    confidence_explanation: str = "Signature match with contextual verification"
    detection_rationale: str = "Matched signature pattern in build logs"
    is_primary_cause: bool = False
    rule_version: str = "1.0.0"
    related_symptoms: list[str] = field(default_factory=list)
    limitations: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert finding to dictionary representation."""
        return {
            "rule_id": self.rule_id,
            "rule_version": self.rule_version,
            "title": self.title,
            "description": self.description,
            "category": self.category.value,
            "severity": self.severity.value,
            "remediation": self.remediation,
            "detection_rationale": self.detection_rationale,
            "confidence": round(self.confidence, 2),
            "confidence_explanation": self.confidence_explanation,
            "is_primary_cause": self.is_primary_cause,
            "evidence": [e.to_dict() for e in self.evidence],
            "related_symptoms": self.related_symptoms,
            "limitations": self.limitations,
        }


@dataclass(slots=True)
class ParsedLog:
    """Structured representation of an entire parsed CI/CD log."""

    filepath: str
    lines: list[LogLine]
    total_lines: int
    steps: list[str] = field(default_factory=list)
    platform: str = "Generic CI"


@dataclass(slots=True)
class DiffItem:
    """A distinct difference found between failed and baseline logs."""

    step: str | None
    failed_line: int
    baseline_line: int
    description: str
    failed_content: str
    baseline_content: str

    def to_dict(self) -> dict[str, Any]:
        """Convert diff item to dictionary representation."""
        return asdict(self)


@dataclass(slots=True)
class DiffReport:
    """Comparative diagnostic report between a failed log and baseline log."""

    failed_path: str
    baseline_path: str
    divergence_step: str | None
    divergence_line: int | None
    summary: str
    differences: list[DiffItem] = field(default_factory=list)
    new_findings: list[str] = field(default_factory=list)
    removed_findings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert diff report to dictionary representation."""
        return {
            "failed_path": self.failed_path,
            "baseline_path": self.baseline_path,
            "divergence_step": self.divergence_step,
            "divergence_line": self.divergence_line,
            "summary": self.summary,
            "differences": [d.to_dict() for d in self.differences],
            "new_findings": self.new_findings,
            "removed_findings": self.removed_findings,
        }


@dataclass(slots=True)
class AnalysisReport:
    """Complete diagnostic report produced by CIAUTOPSY."""

    log_path: str
    total_lines: int
    platform: str
    findings: list[Finding]
    leading_root_cause: Finding | None = None
    cascading_failures: list[Finding] = field(default_factory=list)
    alternative_hypotheses: list[str] = field(default_factory=list)
    missing_evidence: list[str] = field(default_factory=list)
    baseline_comparison: DiffReport | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    schema_version: str = SCHEMA_VERSION

    @property
    def primary_root_cause(self) -> Finding | None:
        """Alias for backward compatibility."""
        return self.leading_root_cause

    def to_dict(self) -> dict[str, Any]:
        """Convert analysis report to versioned dictionary representation."""
        return {
            "schema_version": self.schema_version,
            "log_path": self.log_path,
            "total_lines": self.total_lines,
            "platform": self.platform,
            "leading_root_cause": (
                self.leading_root_cause.to_dict() if self.leading_root_cause else None
            ),
            "primary_root_cause": (
                self.leading_root_cause.to_dict() if self.leading_root_cause else None
            ),
            "findings_count": len(self.findings),
            "findings": [f.to_dict() for f in self.findings],
            "cascading_failures": [f.to_dict() for f in self.cascading_failures],
            "alternative_hypotheses": self.alternative_hypotheses,
            "missing_evidence": self.missing_evidence,
            "baseline_comparison": (
                self.baseline_comparison.to_dict() if self.baseline_comparison else None
            ),
            "metadata": self.metadata,
        }
