"""Base classes, registry, and execution contracts for CIAUTOPSY diagnostic rules."""

from __future__ import annotations

import abc
from typing import ClassVar

from ciautopsy.models import Category, Evidence, Finding, LogLine, ParsedLog, Severity


class DiagnosticRule(abc.ABC):
    """Abstract base class for all log diagnostic rules."""

    rule_id: ClassVar[str] = "GEN-000"
    rule_version: ClassVar[str] = "1.0.0"
    name: ClassVar[str] = "Generic Rule"
    category: ClassVar[Category] = Category.INFRASTRUCTURE
    severity: ClassVar[Severity] = Severity.MEDIUM
    confidence: ClassVar[float] = 0.90
    confidence_explanation: ClassVar[str] = "Direct pattern match with log context"
    quick_filter_keywords: ClassVar[tuple[str, ...]] = ()

    @abc.abstractmethod
    def evaluate(self, parsed_log: ParsedLog) -> Finding | None:
        """
        Analyzes the parsed log. Returns a Finding if triggered, or None.
        """
        pass

    def get_context(
        self,
        lines: list[LogLine],
        target_idx: int,
        before: int = 2,
        after: int = 2,
    ) -> list[tuple[int, str]]:
        """
        Extracts surrounding lines as context for evidence display.
        target_idx is 0-indexed in the lines list.
        """
        start = max(0, target_idx - before)
        end = min(len(lines), target_idx + after + 1)
        return [(lines[i].line_number, lines[i].clean_text) for i in range(start, end)]

    def create_finding(
        self,
        title: str,
        description: str,
        remediation: str,
        evidence: list[Evidence],
        severity: Severity | None = None,
        confidence: float | None = None,
        confidence_explanation: str | None = None,
        detection_rationale: str | None = None,
        is_primary: bool = False,
        related_symptoms: list[str] | None = None,
        limitations: str | None = None,
    ) -> Finding:
        """Helper to create a structured Finding instance."""
        return Finding(
            rule_id=self.rule_id,
            rule_version=self.rule_version,
            title=title,
            description=description,
            category=self.category,
            severity=severity or self.severity,
            remediation=remediation,
            evidence=evidence,
            confidence=confidence if confidence is not None else self.confidence,
            confidence_explanation=(
                confidence_explanation
                if confidence_explanation is not None
                else self.confidence_explanation
            ),
            detection_rationale=(
                detection_rationale
                if detection_rationale is not None
                else f"Matched signature '{self.rule_id}: {self.name}' in log lines"
            ),
            is_primary_cause=is_primary,
            related_symptoms=related_symptoms or [],
            limitations=limitations,
        )


class RuleRegistry:
    """Central registry of all active diagnostic rules."""

    _rules: ClassVar[list[type[DiagnosticRule]]] = []

    @classmethod
    def register(cls, rule_cls: type[DiagnosticRule]) -> type[DiagnosticRule]:
        """Registers a rule class if not already registered."""
        if rule_cls not in cls._rules:
            cls._rules.append(rule_cls)
        return rule_cls

    @classmethod
    def get_all_rules(cls) -> list[DiagnosticRule]:
        """Instantiates and returns all registered diagnostic rules."""
        return [rule_cls() for rule_cls in cls._rules]


def register_rule(cls: type[DiagnosticRule]) -> type[DiagnosticRule]:
    """Decorator to register a diagnostic rule in the RuleRegistry."""
    return RuleRegistry.register(cls)
