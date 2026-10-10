"""Diagnostic rules for build compilation, syntax errors, and missing commands."""

from __future__ import annotations

import re
from re import Pattern
from typing import ClassVar

from ciautopsy.models import Category, Evidence, Finding, ParsedLog, Severity
from ciautopsy.rules.base import DiagnosticRule, register_rule


@register_rule
class CommandNotFoundRule(DiagnosticRule):
    """Detects missing executables or commands not found on PATH."""

    rule_id: ClassVar[str] = "CMD-001"
    rule_version: ClassVar[str] = "1.0.0"
    name: ClassVar[str] = "Command Not Found (Exit 127)"
    category: ClassVar[Category] = Category.INFRASTRUCTURE
    severity: ClassVar[Severity] = Severity.HIGH
    confidence: ClassVar[float] = 0.95
    confidence_explanation: ClassVar[str] = "Shell reported command not found / exit code 127"
    quick_filter_keywords: ClassVar[tuple[str, ...]] = (
        "command not found",
        ": not found",
        "is not recognized",
    )

    PATTERN: ClassVar[Pattern[str]] = re.compile(
        r"(?:command not found|: not found|is not recognized as an internal or external command)",
        re.IGNORECASE,
    )

    def evaluate(self, parsed_log: ParsedLog) -> Finding | None:
        evidence_list: list[Evidence] = []

        for idx, line in enumerate(parsed_log.lines):
            if any(kw in line.clean_text for kw in self.quick_filter_keywords):
                if self.PATTERN.search(line.clean_text):
                    context = self.get_context(parsed_log.lines, idx, before=2, after=2)
                    evidence_list.append(
                        Evidence(
                            line_number=line.line_number,
                            matched_text=line.clean_text,
                            context_lines=context,
                        )
                    )

        if not evidence_list:
            return None

        return self.create_finding(
            title="Required Command or Binary Not Found on PATH",
            description=(
                "A script attempted to invoke a command or binary that is not installed "
                "or not present in the system PATH environment variable."
            ),
            remediation=(
                "1. Add an installation step before this command (e.g. `sudo apt-get install <tool>` or `brew install`).\n"
                "2. Check if a setup action is required (e.g. `actions/setup-node`, `actions/setup-python`, `actions/setup-go`).\n"
                "3. Verify that your PATH includes the directory containing the executable."
            ),
            evidence=evidence_list,
        )


@register_rule
class HeaderCompilationRule(DiagnosticRule):
    """Detects missing C/C++ native header files during extension builds."""

    rule_id: ClassVar[str] = "BLD-001"
    rule_version: ClassVar[str] = "1.0.0"
    name: ClassVar[str] = "Missing C/C++ Header / Compiler Error"
    category: ClassVar[Category] = Category.BUILD_SYNTAX
    severity: ClassVar[Severity] = Severity.HIGH
    confidence: ClassVar[float] = 0.94
    confidence_explanation: ClassVar[str] = "Native compiler error missing header"
    quick_filter_keywords: ClassVar[tuple[str, ...]] = ("fatal error:", "No such file or directory")

    PATTERN: ClassVar[Pattern[str]] = re.compile(
        r"fatal error:\s+([^:]+):\s+No such file or directory", re.IGNORECASE
    )

    def evaluate(self, parsed_log: ParsedLog) -> Finding | None:
        evidence_list: list[Evidence] = []
        header = "unknown"

        for idx, line in enumerate(parsed_log.lines):
            if any(kw in line.clean_text for kw in self.quick_filter_keywords):
                match = self.PATTERN.search(line.clean_text)
                if match:
                    header = match.group(1).strip()
                    context = self.get_context(parsed_log.lines, idx, before=2, after=2)
                    evidence_list.append(
                        Evidence(
                            line_number=line.line_number,
                            matched_text=line.clean_text,
                            context_lines=context,
                            metadata={"header": header},
                        )
                    )

        if not evidence_list:
            return None

        return self.create_finding(
            title=f"Native Compilation Failed: Missing Header '{header}'",
            description=(
                f"A native C/C++ extension failed to compile because header '{header}' was not found."
            ),
            remediation=(
                "1. Install corresponding system development libraries (e.g. `python3-dev`, `libssl-dev`, `build-essential`).\n"
                "2. For Python builds requiring `Python.h`, install the development package for your Python version."
            ),
            evidence=evidence_list,
        )


@register_rule
class SyntaxErrorRule(DiagnosticRule):
    """Detects code syntax and parsing errors."""

    rule_id: ClassVar[str] = "SYN-001"
    rule_version: ClassVar[str] = "1.0.0"
    name: ClassVar[str] = "Syntax / Parsing Error"
    category: ClassVar[Category] = Category.BUILD_SYNTAX
    severity: ClassVar[Severity] = Severity.HIGH
    confidence: ClassVar[float] = 0.93
    confidence_explanation: ClassVar[str] = (
        "SyntaxError or unexpected token raised by compiler/interpreter"
    )
    quick_filter_keywords: ClassVar[tuple[str, ...]] = (
        "SyntaxError:",
        "parse error",
        "Unexpected token",
    )

    PATTERN: ClassVar[Pattern[str]] = re.compile(
        r"(SyntaxError:\s+invalid syntax|SyntaxError:\s+Unexpected token|parse error)",
        re.IGNORECASE,
    )

    def evaluate(self, parsed_log: ParsedLog) -> Finding | None:
        evidence_list: list[Evidence] = []

        for idx, line in enumerate(parsed_log.lines):
            if any(kw in line.clean_text for kw in self.quick_filter_keywords):
                if self.PATTERN.search(line.clean_text):
                    context = self.get_context(parsed_log.lines, idx, before=3, after=2)
                    evidence_list.append(
                        Evidence(
                            line_number=line.line_number,
                            matched_text=line.clean_text,
                            context_lines=context,
                        )
                    )

        if not evidence_list:
            return None

        return self.create_finding(
            title="Syntax / Parsing Error Detected",
            description="The compiler or interpreter encountered invalid code syntax.",
            remediation=(
                "1. Check the line and column indicated in the traceback.\n"
                "2. Verify whether the code relies on newer language features than the CI runner's runtime version."
            ),
            evidence=evidence_list,
        )


@register_rule
class CascadingExitRule(DiagnosticRule):
    """Identifies downstream process exits that result from an earlier failure."""

    rule_id: ClassVar[str] = "CAS-001"
    rule_version: ClassVar[str] = "1.0.0"
    name: ClassVar[str] = "Downstream Process Exit Code"
    category: ClassVar[Category] = Category.CASCADING_FAILURE
    severity: ClassVar[Severity] = Severity.LOW
    confidence: ClassVar[float] = 0.70
    confidence_explanation: ClassVar[str] = (
        "Generic non-zero exit code following a build step failure"
    )
    quick_filter_keywords: ClassVar[tuple[str, ...]] = (
        "Process completed with exit code",
        "make: *** [",
        "failed with exit code",
    )

    PATTERNS: ClassVar[list[Pattern[str]]] = [
        re.compile(r"Process completed with exit code (\d+)", re.IGNORECASE),
        re.compile(r"make: \*\*\* \[.*\] Error (\d+)", re.IGNORECASE),
        re.compile(r"command failed with exit code (\d+)", re.IGNORECASE),
    ]

    def evaluate(self, parsed_log: ParsedLog) -> Finding | None:
        evidence_list: list[Evidence] = []

        for idx, line in enumerate(parsed_log.lines):
            if any(kw in line.clean_text for kw in self.quick_filter_keywords):
                for pat in self.PATTERNS:
                    if pat.search(line.clean_text):
                        context = self.get_context(parsed_log.lines, idx, before=1, after=1)
                        evidence_list.append(
                            Evidence(
                                line_number=line.line_number,
                                matched_text=line.clean_text,
                                context_lines=context,
                            )
                        )
                        break

        if not evidence_list:
            return None

        return self.create_finding(
            title="Non-Zero Exit Code (Cascading Exit)",
            description=(
                "A build step exited with a non-zero exit code as a consequence of an earlier error."
            ),
            remediation="Review earlier error findings to resolve the primary failure trigger.",
            evidence=evidence_list,
            severity=Severity.LOW,
        )
