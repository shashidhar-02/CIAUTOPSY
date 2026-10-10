"""Diagnostic rules for CI infrastructure, memory limits, timeouts, and disk constraints."""

from __future__ import annotations

import re
from re import Pattern
from typing import ClassVar

from ciautopsy.models import Category, Evidence, Finding, ParsedLog, Severity
from ciautopsy.rules.base import DiagnosticRule, register_rule


@register_rule
class OutOfMemoryRule(DiagnosticRule):
    """Detects process terminations caused by out-of-memory errors and exit code 137."""

    rule_id: ClassVar[str] = "OOM-001"
    rule_version: ClassVar[str] = "1.0.0"
    name: ClassVar[str] = "Out Of Memory (OOM / Exit 137)"
    category: ClassVar[Category] = Category.OUT_OF_MEMORY
    severity: ClassVar[Severity] = Severity.CRITICAL
    confidence: ClassVar[float] = 0.98
    confidence_explanation: ClassVar[str] = (
        "Explicit SIGKILL/exit 137 or heap memory exhaustion observed"
    )
    quick_filter_keywords: ClassVar[tuple[str, ...]] = (
        "137",
        "SIGKILL",
        "heap out of memory",
        "MemoryError",
        "oom-killer",
        "Killed",
    )

    PATTERNS: ClassVar[list[Pattern[str]]] = [
        re.compile(r"command terminated with exit code 137", re.IGNORECASE),
        re.compile(r"exit code: 137", re.IGNORECASE),
        re.compile(r"died with signal 9 \(SIGKILL\)", re.IGNORECASE),
        re.compile(r"JavaScript heap out of memory", re.IGNORECASE),
        re.compile(r"MemoryError", re.IGNORECASE),
        re.compile(r"oom-killer|out of memory: killed process", re.IGNORECASE),
        re.compile(r"Killed\s*$", re.MULTILINE),
    ]

    def evaluate(self, parsed_log: ParsedLog) -> Finding | None:
        evidence_list: list[Evidence] = []

        for idx, line in enumerate(parsed_log.lines):
            if any(kw in line.clean_text for kw in self.quick_filter_keywords):
                for pat in self.PATTERNS:
                    if pat.search(line.clean_text):
                        context = self.get_context(parsed_log.lines, idx, before=3, after=2)
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
            title="Process Terminated Due to Out-Of-Memory (OOM / SIGKILL 137)",
            description=(
                "The process exceeded memory allocation limits and was terminated by the OS "
                "OOM killer or container runtime (exit code 137)."
            ),
            remediation=(
                "1. If running Node.js: increase heap space with `NODE_OPTIONS=--max-old-space-size=4096`.\n"
                "2. If running Docker: increase container memory limit in CI runner configuration.\n"
                "3. If running test suites: reduce test parallelization concurrency (e.g. `pytest -n 2` instead of auto).\n"
                "4. Check for runaway loops or large in-memory dataset loads."
            ),
            evidence=evidence_list,
            severity=Severity.CRITICAL,
        )


@register_rule
class StepTimeoutRule(DiagnosticRule):
    """Detects timeouts for individual steps or whole CI jobs."""

    rule_id: ClassVar[str] = "TIM-001"
    rule_version: ClassVar[str] = "1.0.0"
    name: ClassVar[str] = "CI Step / Job Execution Timeout"
    category: ClassVar[Category] = Category.TIMEOUT
    severity: ClassVar[Severity] = Severity.HIGH
    confidence: ClassVar[float] = 0.95
    confidence_explanation: ClassVar[str] = (
        "Cancellation or maximum execution duration limit reached"
    )
    quick_filter_keywords: ClassVar[tuple[str, ...]] = (
        "The operation was canceled",
        "maximum execution time",
        "timed out",
        "execution timed out",
    )

    PATTERNS: ClassVar[list[Pattern[str]]] = [
        re.compile(r"The operation was canceled\.", re.IGNORECASE),
        re.compile(r"job has reached the maximum execution time", re.IGNORECASE),
        re.compile(r"timed out after \d+ (?:minutes|seconds|hours)", re.IGNORECASE),
        re.compile(r"execution timed out", re.IGNORECASE),
        re.compile(r"command timed out after", re.IGNORECASE),
    ]

    def evaluate(self, parsed_log: ParsedLog) -> Finding | None:
        evidence_list: list[Evidence] = []

        for idx, line in enumerate(parsed_log.lines):
            if any(kw in line.clean_text for kw in self.quick_filter_keywords):
                for pat in self.PATTERNS:
                    if pat.search(line.clean_text):
                        context = self.get_context(parsed_log.lines, idx, before=3, after=2)
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
            title="CI Execution Timed Out",
            description=(
                "The build step or entire job exceeded the configured maximum duration limit "
                "and was cancelled by the CI runner."
            ),
            remediation=(
                "1. Inspect previous log lines for stalled network downloads, deadlocks, or waiting prompts.\n"
                "2. Ensure all interactive commands run with non-interactive flags (e.g. `npm -y`, `apt-get -y`).\n"
                "3. If the workload legitimately needs more time, increase `timeout-minutes` in your workflow definition."
            ),
            evidence=evidence_list,
        )


@register_rule
class DiskSpaceRule(DiagnosticRule):
    """Detects storage disk exhaustion on runners."""

    rule_id: ClassVar[str] = "DSK-001"
    rule_version: ClassVar[str] = "1.0.0"
    name: ClassVar[str] = "Runner Disk Space Exhausted (ENOSPC)"
    category: ClassVar[Category] = Category.INFRASTRUCTURE
    severity: ClassVar[Severity] = Severity.CRITICAL
    confidence: ClassVar[float] = 0.97
    confidence_explanation: ClassVar[str] = "OS reported ENOSPC or No space left on device"
    quick_filter_keywords: ClassVar[tuple[str, ...]] = ("No space left", "ENOSPC")

    PATTERN: ClassVar[Pattern[str]] = re.compile(
        r"No space left on device|ENOSPC|write error: No space left", re.IGNORECASE
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
            title="Runner Disk Space Exhausted (No Space Left On Device)",
            description="The runner VM or container ran out of available disk storage space.",
            remediation=(
                "1. Prune unused Docker images, caches, and build artifacts (`docker system prune -af`).\n"
                "2. On GitHub Actions runners, free disk space using cleanup actions like `easimon/maximize-build-space`.\n"
                "3. Clear package manager caches before building large assets."
            ),
            evidence=evidence_list,
        )


@register_rule
class DockerPermissionRule(DiagnosticRule):
    """Detects socket permission errors when accessing Docker daemon."""

    rule_id: ClassVar[str] = "DOK-001"
    rule_version: ClassVar[str] = "1.0.0"
    name: ClassVar[str] = "Docker Daemon Socket Permission Denied"
    category: ClassVar[Category] = Category.INFRASTRUCTURE
    severity: ClassVar[Severity] = Severity.HIGH
    confidence: ClassVar[float] = 0.96
    confidence_explanation: ClassVar[str] = "Docker socket permission denied in log output"
    quick_filter_keywords: ClassVar[tuple[str, ...]] = ("docker.sock", "Docker daemon")

    PATTERN: ClassVar[Pattern[str]] = re.compile(
        r"Got permission denied while trying to connect to the Docker daemon socket|dial unix /var/run/docker\.sock: connect: permission denied",
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
            title="Docker Daemon Socket Access Denied",
            description=(
                "The current CI user does not have permission to communicate with `/var/run/docker.sock`."
            ),
            remediation=(
                "1. Add the CI runner user to the `docker` user group (`sudo usermod -aG docker $USER`).\n"
                "2. If using container-in-container / Docker-in-Docker (dind), verify proper socket mounting.\n"
                "3. Ensure the runner service has appropriate root/sudo privileges."
            ),
            evidence=evidence_list,
        )
