"""Diagnostic rules for DNS, network connection failures, and HTTP errors."""

from __future__ import annotations

import re
from re import Pattern
from typing import ClassVar

from ciautopsy.models import Category, Evidence, Finding, ParsedLog, Severity
from ciautopsy.rules.base import DiagnosticRule, register_rule


@register_rule
class NetworkConnectionRule(DiagnosticRule):
    """Detects network connection refused, DNS resolution failures, and remote host timeouts."""

    rule_id: ClassVar[str] = "NET-001"
    rule_version: ClassVar[str] = "1.0.0"
    name: ClassVar[str] = "Network Connection / DNS Resolution Error"
    category: ClassVar[Category] = Category.INFRASTRUCTURE
    severity: ClassVar[Severity] = Severity.HIGH
    confidence: ClassVar[float] = 0.94
    confidence_explanation: ClassVar[str] = (
        "Socket/DNS error connecting to external service or registry"
    )
    quick_filter_keywords: ClassVar[tuple[str, ...]] = (
        "Could not resolve host",
        "Connection refused",
        "ECONNREFUSED",
        "getaddrinfo",
        "ETIMEDOUT",
    )

    PATTERNS: ClassVar[list[Pattern[str]]] = [
        re.compile(r"Could not resolve host:\s+([a-zA-Z0-9_\-\.]+)", re.IGNORECASE),
        re.compile(r"connect: connection refused|ECONNREFUSED", re.IGNORECASE),
        re.compile(r"getaddrinfo ENOTFOUND|getaddrinfo failed", re.IGNORECASE),
        re.compile(r"Failed to connect to .* port \d+: Connection refused", re.IGNORECASE),
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
            title="Network Connection / DNS Resolution Failure",
            description=(
                "A network request failed due to unresolved hostnames or a refused socket connection."
            ),
            remediation=(
                "1. Verify that third-party services or package registries are reachable.\n"
                "2. Check if a local service container (e.g. Postgres, Redis, local server) was started and healthy before the step ran.\n"
                "3. Ensure the CI runner environment has DNS access and is not blocked by proxy or firewall rules."
            ),
            evidence=evidence_list,
        )
