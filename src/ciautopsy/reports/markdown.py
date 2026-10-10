"""Markdown reporter conforming to CIAUTOPSY specification."""

from __future__ import annotations

from ciautopsy.models import AnalysisReport, DiffReport


def format_markdown_report(report: AnalysisReport) -> str:
    """Renders a comprehensive, evidence-linked AnalysisReport in Markdown."""
    lines: list[str] = [
        "# 🩺 CIAUTOPSY Diagnostic Report",
        "",
        "## 1. Summary",
        "",
        f"- **Target Log:** `{report.log_path}`",
        f"- **Detected Platform:** {report.platform}",
        f"- **Total Lines Analyzed:** {report.total_lines:,}",
        f"- **Diagnostic Hypotheses Identified:** {len(report.findings)}",
        f"- **Cascading Failures Grouped:** {len(report.cascading_failures)}",
        f"- **Baseline Compared:** {'Yes' if report.baseline_comparison else 'No'}",
        f"- **Report Schema Version:** `{report.schema_version}`",
        "",
        "---",
        "",
    ]

    # 2 & 3. Leading Candidate Root Cause & Confidence
    lines.append("## 2. Leading Candidate Root Cause")
    lines.append("")

    if report.leading_root_cause:
        pr = report.leading_root_cause
        lines.extend(
            [
                f"### `[{pr.rule_id}]` {pr.title}",
                "",
                f"- **Category:** {pr.category.value}",
                f"- **Severity:** `{pr.severity.value}`",
                f"- **Confidence:** {int(pr.confidence * 100)}%",
                f"- **Confidence Rationale:** {pr.confidence_explanation}",
                f"- **Detection Rationale:** {pr.detection_rationale}",
                "",
                f"> {pr.description}",
                "",
            ]
        )

        # 4. Evidence
        lines.append("## 3. Evidence References")
        lines.append("")
        for ev in pr.evidence[:3]:
            lines.append(f"**Log Line `{ev.line_number}`:**")
            lines.append("```log")
            if ev.context_lines:
                for ctx_num, ctx_text in ev.context_lines:
                    mark = " > " if ctx_num == ev.line_number else "   "
                    lines.append(f"{mark}{ctx_num:4d} | {ctx_text}")
            else:
                lines.append(f" > {ev.line_number:4d} | {ev.matched_text}")
            lines.append("```")
            lines.append("")

        # 5. Related Symptoms
        lines.append("## 4. Related Symptoms & Cascades")
        lines.append("")
        if pr.related_symptoms:
            lines.append("**Associated Symptom Signatures:**")
            for sym in pr.related_symptoms:
                lines.append(f"- `{sym}`")
            lines.append("")

        if report.cascading_failures:
            lines.extend(
                [
                    "<details>",
                    "<summary>Click to view downstream cascading exits</summary>",
                    "",
                ]
            )
            for cf in report.cascading_failures:
                first_line = cf.evidence[0].line_number if cf.evidence else 0
                lines.append(f"- Line `{first_line}`: {cf.title}")
            lines.extend(["", "</details>", ""])

        # 6. Baseline comparison (if provided)
        lines.append("## 5. Baseline Comparison")
        lines.append("")
        if report.baseline_comparison:
            lines.append(f"> {report.baseline_comparison.summary}")
            if report.baseline_comparison.divergence_step:
                lines.append(f"\n**Divergence Step:** {report.baseline_comparison.divergence_step}")
            lines.append("")
        else:
            lines.append(
                "*No successful baseline log was provided for comparison. "
                "Use `--baseline <file>` to detect environment or version drift.*"
            )
            lines.append("")

        # 7. Suggested Next Steps
        lines.append("## 6. Suggested Next Steps")
        lines.append("")
        lines.append(pr.remediation)
        lines.append("")

    else:
        lines.append("✅ **No diagnostic failure patterns detected.**")
        lines.append(
            "The log either succeeded, terminated abnormally without standard error signatures, "
            "or requires a custom diagnostic rule."
        )
        lines.append("")

    # 8. Alternative Hypotheses
    lines.append("## 7. Alternative Hypotheses")
    lines.append("")
    if report.alternative_hypotheses:
        for alt in report.alternative_hypotheses:
            lines.append(f"- {alt}")
    else:
        lines.append("No competing alternative root-cause hypotheses were detected.")
    lines.append("")

    # 9. Missing Evidence
    lines.append("## 8. Missing Evidence")
    lines.append("")
    if report.missing_evidence:
        for miss in report.missing_evidence:
            lines.append(f"- ⚠️ {miss}")
    else:
        lines.append("No obvious evidence gaps detected in the parsed build log.")
    lines.append("")

    # 10. Limitations & Privacy Notice
    lines.append("## 9. Limitations & Privacy Notice")
    lines.append("")
    lines.append(
        "- **Privacy & Redaction:** All evidence was processed locally. "
        "Best-effort secret redaction was applied, but heuristic filtering cannot guarantee that every token or secret was removed. "
        "Review report contents before sharing externally."
    )
    lines.append(
        "- **Diagnostic Scope:** Findings represent automated hypotheses backed by log evidence, not formal mathematical proofs."
    )
    lines.append(
        "- **Non-Execution:** CIAUTOPSY suggests remediation commands but never executes shell commands extracted from logs."
    )
    lines.append("")
    lines.append("*Generated locally by [CIAUTOPSY](https://github.com/shashidhar-02/CIAUTOPSY)*")

    return "\n".join(lines)


def format_markdown_diff(diff: DiffReport) -> str:
    """Renders a DiffReport into GitHub-flavored Markdown."""
    lines: list[str] = [
        "# 🔄 CIAUTOPSY Build Comparison Report",
        "",
        f"- **Failed Run:** `{diff.failed_path}`",
        f"- **Baseline Run:** `{diff.baseline_path}`",
        "",
        f"**Summary:** {diff.summary}",
        "",
    ]

    if diff.divergence_step:
        lines.extend(
            [
                "### 🚩 Divergence Point",
                f"> {diff.divergence_step}",
                "",
            ]
        )

    if diff.differences:
        lines.extend(
            [
                "### 🔍 Key Differences",
                "",
                "| Failed Line | Step | Baseline Content | Failed Content |",
                "| :--- | :--- | :--- | :--- |",
            ]
        )
        for item in diff.differences:
            b_text = item.baseline_content.replace("|", "\\|")
            f_text = item.failed_content.replace("|", "\\|")
            lines.append(
                f"| `{item.failed_line}` | {item.step or 'Global'} | `{b_text}` | `{f_text}` |"
            )
        lines.append("")

    lines.append("\n*Generated locally by [CIAUTOPSY](https://github.com/shashidhar-02/CIAUTOPSY)*")
    return "\n".join(lines)
