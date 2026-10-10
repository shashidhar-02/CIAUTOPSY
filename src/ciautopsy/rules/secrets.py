"""Diagnostic rules for authentication, missing secrets, and environment tokens."""

from __future__ import annotations

import re
from re import Pattern
from typing import ClassVar

from ciautopsy.models import Category, Evidence, Finding, ParsedLog, Severity
from ciautopsy.rules.base import DiagnosticRule, register_rule


@register_rule
class AuthenticationFailureRule(DiagnosticRule):
    """Detects authentication, token expiration, and registry permission failures."""

    rule_id: ClassVar[str] = "SEC-001"
    rule_version: ClassVar[str] = "1.0.0"
    name: ClassVar[str] = "Authentication / Git Credential Failure"
    category: ClassVar[Category] = Category.PERMISSION_AUTH
    severity: ClassVar[Severity] = Severity.HIGH
    confidence: ClassVar[float] = 0.96
    confidence_explanation: ClassVar[str] = (
        "HTTP 401/403 or authentication failure reported by Git/package registry"
    )
    quick_filter_keywords: ClassVar[tuple[str, ...]] = (
        "Authentication failed",
        "401",
        "Invalid or expired token",
        "E401",
        "Permission to",
    )

    PATTERNS: ClassVar[list[Pattern[str]]] = [
        re.compile(r"fatal: Authentication failed for", re.IGNORECASE),
        re.compile(r"HTTP 401 (?:Unauthorized|Forbidden)", re.IGNORECASE),
        re.compile(r"Invalid or expired token", re.IGNORECASE),
        re.compile(r"npm ERR! code E401", re.IGNORECASE),
        re.compile(r"Permission to .* denied to", re.IGNORECASE),
    ]

    def evaluate(self, parsed_log: ParsedLog) -> Finding | None:
        evidence_list: list[Evidence] = []

        for idx, line in enumerate(parsed_log.lines):
            if any(kw in line.clean_text for kw in self.quick_filter_keywords):
                for pat in self.PATTERNS:
                    if pat.search(line.clean_text):
                        context = self.get_context(parsed_log.lines, idx, before=2, after=2)
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
            title="Authentication / Registry Credential Failure",
            description=(
                "Access was rejected due to missing, expired, or invalid credentials/tokens."
            ),
            remediation=(
                "1. Verify that repository secrets (e.g. `GITHUB_TOKEN`, `NPM_TOKEN`, `DOCKER_PASSWORD`) are configured.\n"
                "2. Check if a personal access token (PAT) has expired or lacks necessary scopes.\n"
                "3. Ensure the workflow has granted the needed `permissions:` (e.g. `contents: write`, `packages: write`)."
            ),
            evidence=evidence_list,
        )


@register_rule
class MissingEnvVarRule(DiagnosticRule):
    """Detects missing required environment variables."""

    rule_id: ClassVar[str] = "SEC-002"
    rule_version: ClassVar[str] = "1.0.0"
    name: ClassVar[str] = "Missing Required Environment Variable"
    category: ClassVar[Category] = Category.PERMISSION_AUTH
    severity: ClassVar[Severity] = Severity.HIGH
    confidence: ClassVar[float] = 0.91
    confidence_explanation: ClassVar[str] = (
        "KeyError or explicit environment variable missing message"
    )
    quick_filter_keywords: ClassVar[tuple[str, ...]] = (
        "KeyError:",
        "Required environment variable",
    )

    PATTERNS: ClassVar[list[Pattern[str]]] = [
        re.compile(r"KeyError:\s+['\"]([A-Z0-9_]+)['\"]", re.IGNORECASE),
        re.compile(
            r"Required environment variable\s+['\"]?([A-Z0-9_]+)['\"]?\s+is not set",
            re.IGNORECASE,
        ),
    ]

    def evaluate(self, parsed_log: ParsedLog) -> Finding | None:
        evidence_list: list[Evidence] = []
        missing_var = "ENV_VAR"

        for idx, line in enumerate(parsed_log.lines):
            if any(kw in line.clean_text for kw in self.quick_filter_keywords):
                for pat in self.PATTERNS:
                    match = pat.search(line.clean_text)
                    if match:
                        if match.groups() and match.group(1):
                            missing_var = match.group(1)
                        context = self.get_context(parsed_log.lines, idx, before=2, after=2)
                        evidence_list.append(
                            Evidence(
                                line_number=line.line_number,
                                matched_text=line.clean_text,
                                context_lines=context,
                                metadata={"env_var": missing_var},
                            )
                        )
                        break

        if not evidence_list:
            return None

        return self.create_finding(
            title=f"Missing Environment Variable: '{missing_var}'",
            description=(
                f"The application or script raised an error because environment variable '{missing_var}' was not provided."
            ),
            remediation=(
                f"1. Add '{missing_var}' to the CI workflow's `env:` block or repository secret settings.\n"
                "2. Check if the variable name has a typo or is missing default fallback logic in code."
            ),
            evidence=evidence_list,
        )
