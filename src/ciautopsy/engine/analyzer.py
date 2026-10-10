"""Core analysis engine orchestrating log parsing, rule evaluation, and root-cause ranking."""

from __future__ import annotations

from ciautopsy.comparison.comparator import compare_logs
from ciautopsy.config import DEFAULT_INGESTION_CONFIG, IngestionConfig
from ciautopsy.models import (
    AnalysisReport,
    Category,
    DiffReport,
    Finding,
    ParsedLog,
    Severity,
)
from ciautopsy.parsers.demuxer import parse_log_content, parse_log_target
from ciautopsy.rules import RuleRegistry

SEVERITY_WEIGHTS: dict[Severity, int] = {
    Severity.CRITICAL: 100,
    Severity.HIGH: 80,
    Severity.MEDIUM: 50,
    Severity.LOW: 20,
    Severity.INFO: 10,
}


def analyze_target(
    target_path: str,
    baseline_path: str | None = None,
    config: IngestionConfig = DEFAULT_INGESTION_CONFIG,
) -> AnalysisReport:
    """Analyzes a CI log or ZIP target, optionally comparing against a baseline."""
    parsed = parse_log_target(target_path, config=config)
    baseline_report: DiffReport | None = None
    if baseline_path:
        baseline_report = compare_logs(
            failed_path=target_path,
            baseline_path=baseline_path,
            config=config,
        )

    return analyze_parsed_log(parsed, baseline_comparison=baseline_report)


def analyze_log(
    log_path: str,
    max_lines: int | None = 100_000,
    baseline_path: str | None = None,
) -> AnalysisReport:
    """Convenience entrypoint for analyzing a log file path."""
    config = IngestionConfig(max_lines=max_lines or 100_000)
    return analyze_target(log_path, baseline_path=baseline_path, config=config)


def analyze_log_content(
    content: str,
    filepath: str = "stream",
    max_lines: int | None = 100_000,
) -> AnalysisReport:
    """Analyzes raw string log content and produces an AnalysisReport."""
    parsed = parse_log_content(content, filepath=filepath, max_lines=max_lines)
    return analyze_parsed_log(parsed)


def analyze_parsed_log(
    parsed: ParsedLog,
    baseline_comparison: DiffReport | None = None,
) -> AnalysisReport:
    """Evaluates rules against a ParsedLog and ranks root cause vs cascading errors."""
    rules = RuleRegistry.get_all_rules()
    raw_findings: list[Finding] = []

    for rule in rules:
        try:
            finding = rule.evaluate(parsed)
            if finding and finding.evidence:
                raw_findings.append(finding)
        except Exception:
            # Defensive guard: a faulty rule must never abort diagnostic triage
            continue

    primary_candidates: list[Finding] = []
    cascading_list: list[Finding] = []

    for f in raw_findings:
        if f.category == Category.CASCADING_FAILURE:
            cascading_list.append(f)
        else:
            primary_candidates.append(f)

    # Root Cause Ranking Algorithm:
    # 1. Earliest appearance in log (first real error before subsequent cascade)
    # 2. Higher severity
    # 3. Higher confidence
    def sort_key(f: Finding) -> tuple[int, int, float]:
        first_line = min((e.line_number for e in f.evidence), default=999_999)
        severity_score = SEVERITY_WEIGHTS.get(f.severity, 0)
        return (first_line, -severity_score, -f.confidence)

    primary_candidates.sort(key=sort_key)

    leading_root_cause: Finding | None = None
    alternative_hypotheses: list[str] = []

    if primary_candidates:
        leading_root_cause = primary_candidates[0]
        leading_root_cause.is_primary_cause = True

        for alt in primary_candidates[1:]:
            first_line = alt.evidence[0].line_number if alt.evidence else 0
            alternative_hypotheses.append(
                f"[{alt.rule_id}] {alt.title} (detected at line {first_line}, severity {alt.severity.value})"
            )
    elif cascading_list:
        leading_root_cause = cascading_list[0]
        leading_root_cause.is_primary_cause = True

    # Identify missing evidence notes
    missing_evidence: list[str] = []
    if parsed.total_lines < 5:
        missing_evidence.append(
            "Log contains fewer than 5 lines; build context is truncated or minimal"
        )
    if not leading_root_cause and not cascading_list:
        missing_evidence.append(
            "No known failure signatures matched. Root cause may be an unmodeled error or non-standard exit"
        )

    return AnalysisReport(
        log_path=parsed.filepath,
        total_lines=parsed.total_lines,
        platform=parsed.platform,
        findings=primary_candidates,
        leading_root_cause=leading_root_cause,
        cascading_failures=cascading_list,
        alternative_hypotheses=alternative_hypotheses,
        missing_evidence=missing_evidence,
        baseline_comparison=baseline_comparison,
        metadata={
            "rules_evaluated": len(rules),
            "steps_detected": parsed.steps,
        },
    )
