"""Compares a failed CI build log against a successful baseline log to detect drift."""

from __future__ import annotations

import difflib

from ciautopsy.config import DEFAULT_INGESTION_CONFIG, IngestionConfig
from ciautopsy.models import DiffItem, DiffReport
from ciautopsy.parsers.demuxer import parse_log_target


def compare_logs(
    failed_path: str,
    baseline_path: str,
    max_diffs: int = 15,
    config: IngestionConfig = DEFAULT_INGESTION_CONFIG,
) -> DiffReport:
    """
    Compares failed log vs baseline log, identifying the step divergence point
    and significant line differences efficiently.
    """
    failed_log = parse_log_target(failed_path, config=config)
    baseline_log = parse_log_target(baseline_path, config=config)

    # 1. Compare step flows
    divergence_step: str | None = None
    min_steps = min(len(failed_log.steps), len(baseline_log.steps))

    for i in range(min_steps):
        if failed_log.steps[i] != baseline_log.steps[i]:
            divergence_step = (
                f"Diverged at step '{failed_log.steps[i]}' (Baseline had '{baseline_log.steps[i]}')"
            )
            break

    if not divergence_step and len(failed_log.steps) < len(baseline_log.steps):
        last_failed_step = failed_log.steps[-1] if failed_log.steps else "start"
        divergence_step = (
            f"Failed run terminated early at '{last_failed_step}'. "
            f"Baseline continued to '{baseline_log.steps[len(failed_log.steps)]}'"
        )

    # 2. Text comparison using difflib
    clean_failed = [line.clean_text for line in failed_log.lines]
    clean_baseline = [line.clean_text for line in baseline_log.lines]

    matcher = difflib.SequenceMatcher(None, clean_baseline, clean_failed)
    differences: list[DiffItem] = []
    first_divergence_line: int | None = None

    for tag, i1, _i2, j1, j2 in matcher.get_opcodes():
        if tag in ("replace", "insert"):
            if first_divergence_line is None and j1 < len(failed_log.lines):
                first_divergence_line = failed_log.lines[j1].line_number

            for failed_idx in range(j1, min(j2, j1 + 3)):
                if len(differences) >= max_diffs:
                    break
                f_line = failed_log.lines[failed_idx]
                b_text = clean_baseline[i1] if i1 < len(clean_baseline) else "(none)"
                b_line_num = (
                    baseline_log.lines[i1].line_number if i1 < len(baseline_log.lines) else 0
                )

                differences.append(
                    DiffItem(
                        step=f_line.step_name,
                        failed_line=f_line.line_number,
                        baseline_line=b_line_num,
                        description=f"Log divergence ({tag}) in step: {f_line.step_name or 'Global'}",
                        failed_content=f_line.clean_text,
                        baseline_content=b_text,
                    )
                )

        if len(differences) >= max_diffs:
            break

    summary = (
        f"Compared failed run ({failed_log.total_lines:,} lines) against baseline "
        f"({baseline_log.total_lines:,} lines). "
    )
    if divergence_step:
        summary += f"{divergence_step}. "
    if first_divergence_line:
        summary += f"First divergence detected around failed log line {first_divergence_line}."

    return DiffReport(
        failed_path=failed_path,
        baseline_path=baseline_path,
        divergence_step=divergence_step,
        divergence_line=first_divergence_line,
        summary=summary,
        differences=differences,
    )
