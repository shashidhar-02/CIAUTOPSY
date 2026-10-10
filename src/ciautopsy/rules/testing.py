"""Diagnostic rules for automated test runner failures."""

from __future__ import annotations

import re
from re import Pattern
from typing import ClassVar

from ciautopsy.models import Category, Evidence, Finding, ParsedLog, Severity
from ciautopsy.rules.base import DiagnosticRule, register_rule


@register_rule
class PytestFailureRule(DiagnosticRule):
    """Detects pytest test failures and assertion errors."""

    rule_id: ClassVar[str] = "TST-001"
    rule_version: ClassVar[str] = "1.0.0"
    name: ClassVar[str] = "Pytest Assertion / Test Suite Failure"
    category: ClassVar[Category] = Category.TEST_FAILURE
    severity: ClassVar[Severity] = Severity.HIGH
    confidence: ClassVar[float] = 0.95
    confidence_explanation: ClassVar[str] = "Pytest reported test failure or assertion error"
    quick_filter_keywords: ClassVar[tuple[str, ...]] = ("FAILED ", "= FAILURES =")

    PATTERN: ClassVar[Pattern[str]] = re.compile(
        r"FAILED\s+([a-zA-Z0-9_\-\./]+::[a-zA-Z0-9_]+)|=+ FAILURES =+"
    )

    def evaluate(self, parsed_log: ParsedLog) -> Finding | None:
        evidence_list: list[Evidence] = []
        failed_tests: list[str] = []

        for idx, line in enumerate(parsed_log.lines):
            if any(kw in line.clean_text for kw in self.quick_filter_keywords):
                match = self.PATTERN.search(line.clean_text)
                if match:
                    if match.group(1):
                        failed_tests.append(match.group(1))
                    context = self.get_context(parsed_log.lines, idx, before=2, after=3)
                    evidence_list.append(
                        Evidence(
                            line_number=line.line_number,
                            matched_text=line.clean_text,
                            context_lines=context,
                        )
                    )

        if not evidence_list:
            return None

        test_summary = (
            f"Failed test: {failed_tests[0]}"
            if len(failed_tests) == 1
            else f"{len(failed_tests)} test(s) failed in pytest"
            if failed_tests
            else "Pytest assertions failed"
        )

        return self.create_finding(
            title=f"Test Suite Failure: {test_summary}",
            description="One or more automated unit/integration tests failed in pytest.",
            remediation=(
                "1. Inspect the traceback and assertion diff above the failure mark.\n"
                "2. Run the specific failing test locally using `pytest <test_path>`.\n"
                "3. Verify if test data, mocks, or environment variables changed."
            ),
            evidence=evidence_list,
            related_symptoms=failed_tests,
        )


@register_rule
class JestFailureRule(DiagnosticRule):
    """Detects JavaScript / TypeScript test suite failures in Jest or Vitest."""

    rule_id: ClassVar[str] = "TST-002"
    rule_version: ClassVar[str] = "1.0.0"
    name: ClassVar[str] = "Jest / Vitest JavaScript Test Failure"
    category: ClassVar[Category] = Category.TEST_FAILURE
    severity: ClassVar[Severity] = Severity.HIGH
    confidence: ClassVar[float] = 0.95
    confidence_explanation: ClassVar[str] = "Jest/Vitest reported FAIL in test suite files"
    quick_filter_keywords: ClassVar[tuple[str, ...]] = ("FAIL ", "Tests: ")

    PATTERN: ClassVar[Pattern[str]] = re.compile(
        r"FAIL\s+([a-zA-Z0-9_\-\./]+\.(?:test|spec)\.[jt]sx?)"
    )

    def evaluate(self, parsed_log: ParsedLog) -> Finding | None:
        evidence_list: list[Evidence] = []
        failed_files: list[str] = []

        for idx, line in enumerate(parsed_log.lines):
            if any(kw in line.clean_text for kw in self.quick_filter_keywords):
                match = self.PATTERN.search(line.clean_text)
                if match:
                    failed_files.append(match.group(1))
                    context = self.get_context(parsed_log.lines, idx, before=2, after=3)
                    evidence_list.append(
                        Evidence(
                            line_number=line.line_number,
                            matched_text=line.clean_text,
                            context_lines=context,
                            metadata={"test_file": match.group(1)},
                        )
                    )

        if not evidence_list:
            return None

        return self.create_finding(
            title=f"Jest / Vitest Test Failure ({len(failed_files)} file(s))",
            description="Automated JavaScript / TypeScript test suite reported failures.",
            remediation=(
                "1. Run the failing test locally with `npm test -- <test-file>`.\n"
                "2. Inspect snapshot discrepancies or unexpected return values in the test report."
            ),
            evidence=evidence_list,
            related_symptoms=failed_files,
        )
