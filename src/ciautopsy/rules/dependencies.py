"""Diagnostic rules for dependency resolution, package manager errors, and missing imports."""

from __future__ import annotations

import re
from re import Pattern
from typing import ClassVar

from ciautopsy.models import Category, Evidence, Finding, ParsedLog, Severity
from ciautopsy.rules.base import DiagnosticRule, register_rule


@register_rule
class PythonMissingModuleRule(DiagnosticRule):
    """Detects missing Python modules in tracebacks."""

    rule_id: ClassVar[str] = "DEP-001"
    rule_version: ClassVar[str] = "1.0.0"
    name: ClassVar[str] = "Python Module Not Found"
    category: ClassVar[Category] = Category.DEPENDENCY
    severity: ClassVar[Severity] = Severity.HIGH
    confidence: ClassVar[float] = 0.95
    confidence_explanation: ClassVar[str] = "Explicit ModuleNotFoundError traceback observed"
    quick_filter_keywords: ClassVar[tuple[str, ...]] = ("ModuleNotFoundError:", "No module named")

    PATTERN: ClassVar[Pattern[str]] = re.compile(
        r"ModuleNotFoundError:\s+No module named\s+['\"]([^'\"]+)['\"]"
    )

    def evaluate(self, parsed_log: ParsedLog) -> Finding | None:
        evidence_list: list[Evidence] = []
        missing_module = None

        for idx, line in enumerate(parsed_log.lines):
            if any(kw in line.clean_text for kw in self.quick_filter_keywords):
                match = self.PATTERN.search(line.clean_text)
                if match:
                    missing_module = match.group(1)
                    context = self.get_context(parsed_log.lines, idx, before=3, after=1)
                    evidence_list.append(
                        Evidence(
                            line_number=line.line_number,
                            matched_text=line.clean_text,
                            context_lines=context,
                            metadata={"module": missing_module},
                        )
                    )

        if not evidence_list:
            return None

        return self.create_finding(
            title=f"Missing Python Dependency: '{missing_module}'",
            description=(
                f"The build failed because Python module '{missing_module}' is not installed or "
                "not included in your environment specification."
            ),
            remediation=(
                f"1. Add '{missing_module}' to your `requirements.txt`, `pyproject.toml`, or `setup.cfg`.\n"
                f"2. Ensure the step installing dependencies (`pip install`, `poetry install`, `uv sync`) "
                "runs before executing code.\n"
                "3. If using an isolated virtual environment, verify it is activated in this CI step."
            ),
            evidence=evidence_list,
        )


@register_rule
class PipConflictRule(DiagnosticRule):
    """Detects pip dependency resolution conflicts."""

    rule_id: ClassVar[str] = "DEP-002"
    rule_version: ClassVar[str] = "1.0.0"
    name: ClassVar[str] = "Pip Dependency Resolution Conflict"
    category: ClassVar[Category] = Category.DEPENDENCY
    severity: ClassVar[Severity] = Severity.HIGH
    confidence: ClassVar[float] = 0.92
    confidence_explanation: ClassVar[str] = (
        "Pip resolver reported ResolutionImpossible or conflicting pins"
    )
    quick_filter_keywords: ClassVar[tuple[str, ...]] = (
        "ResolutionImpossible",
        "conflicting dependencies",
        "has requirement",
    )

    CONFLICT_PATTERN: ClassVar[Pattern[str]] = re.compile(
        r"(ResolutionImpossible|conflicting dependencies|has requirement .* but you have)"
    )

    def evaluate(self, parsed_log: ParsedLog) -> Finding | None:
        evidence_list: list[Evidence] = []

        for idx, line in enumerate(parsed_log.lines):
            if any(kw in line.clean_text for kw in self.quick_filter_keywords):
                if self.CONFLICT_PATTERN.search(line.clean_text):
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

        return self.create_finding(
            title="Incompatible Python Package Constraints (ResolutionImpossible)",
            description=(
                "pip was unable to find a set of package versions that satisfies all requirements."
            ),
            remediation=(
                "1. Check the conflicting dependencies listed in the log lines.\n"
                "2. Loosen strict version pins (e.g. change `==` to `>=` or `~=`) where possible.\n"
                "3. Use `pip install --dry-run` or `uv pip compile` locally to reproduce and solve the conflict."
            ),
            evidence=evidence_list,
        )


@register_rule
class NpmEresolveRule(DiagnosticRule):
    """Detects npm peer dependency conflicts (ERESOLVE)."""

    rule_id: ClassVar[str] = "DEP-003"
    rule_version: ClassVar[str] = "1.0.0"
    name: ClassVar[str] = "npm Dependency Tree Conflict (ERESOLVE)"
    category: ClassVar[Category] = Category.DEPENDENCY
    severity: ClassVar[Severity] = Severity.HIGH
    confidence: ClassVar[float] = 0.95
    confidence_explanation: ClassVar[str] = "npm package manager reported ERESOLVE code"
    quick_filter_keywords: ClassVar[tuple[str, ...]] = ("ERESOLVE", "Could not resolve dependency")

    PATTERN: ClassVar[Pattern[str]] = re.compile(
        r"npm ERR!\s+code\s+ERESOLVE|npm ERR!\s+Could not resolve dependency"
    )

    def evaluate(self, parsed_log: ParsedLog) -> Finding | None:
        evidence_list: list[Evidence] = []

        for idx, line in enumerate(parsed_log.lines):
            if any(kw in line.clean_text for kw in self.quick_filter_keywords):
                if self.PATTERN.search(line.clean_text):
                    context = self.get_context(parsed_log.lines, idx, before=1, after=4)
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
            title="Node/npm Dependency Tree Conflict (ERESOLVE)",
            description=(
                "npm could not build the dependency tree due to conflicting peer dependency versions."
            ),
            remediation=(
                "1. Update the conflicting peer dependencies in `package.json` to mutually compatible versions.\n"
                "2. If safe, run `npm install --legacy-peer-deps` as an interim workaround.\n"
                "3. Run `npm ls` locally to inspect the conflicting dependency tree."
            ),
            evidence=evidence_list,
        )


@register_rule
class NodeMissingModuleRule(DiagnosticRule):
    """Detects missing Node.js modules or packages."""

    rule_id: ClassVar[str] = "DEP-004"
    rule_version: ClassVar[str] = "1.0.0"
    name: ClassVar[str] = "Node Module Not Found"
    category: ClassVar[Category] = Category.DEPENDENCY
    severity: ClassVar[Severity] = Severity.HIGH
    confidence: ClassVar[float] = 0.94
    confidence_explanation: ClassVar[str] = (
        "Node runtime reported Cannot find module or ERR_MODULE_NOT_FOUND"
    )
    quick_filter_keywords: ClassVar[tuple[str, ...]] = (
        "Cannot find module",
        "ERR_MODULE_NOT_FOUND",
    )

    PATTERN: ClassVar[Pattern[str]] = re.compile(
        r"(?:Error:\s+)?Cannot find module\s+['\"]([^'\"]+)['\"]|ERR_MODULE_NOT_FOUND",
        re.IGNORECASE,
    )

    def evaluate(self, parsed_log: ParsedLog) -> Finding | None:
        evidence_list: list[Evidence] = []
        module_name = "unknown"

        for idx, line in enumerate(parsed_log.lines):
            if any(kw in line.clean_text for kw in self.quick_filter_keywords):
                match = self.PATTERN.search(line.clean_text)
                if match:
                    if match.groups() and match.group(1):
                        module_name = match.group(1)
                    context = self.get_context(parsed_log.lines, idx, before=2, after=2)
                    evidence_list.append(
                        Evidence(
                            line_number=line.line_number,
                            matched_text=line.clean_text,
                            context_lines=context,
                            metadata={"module": module_name},
                        )
                    )

        if not evidence_list:
            return None

        return self.create_finding(
            title=f"Missing Node.js Module: '{module_name}'",
            description=f"A Node.js runtime script failed because module '{module_name}' was not found.",
            remediation=(
                f"1. Add '{module_name}' to `package.json` dependencies.\n"
                "2. Ensure `npm ci` or `npm install` runs before your build or test step.\n"
                "3. Verify that `node_modules` is not mistakenly ignored or cleaned between CI jobs."
            ),
            evidence=evidence_list,
        )
