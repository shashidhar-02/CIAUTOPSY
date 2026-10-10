"""Terminal / Console reporter for CIAUTOPSY diagnostic findings."""

from __future__ import annotations

import io
import os
import sys

from ciautopsy.models import AnalysisReport, DiffReport, Severity

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text

    HAS_RICH = True
except ImportError:
    HAS_RICH = False

# Fallback ANSI constants
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"


def _supports_color() -> bool:
    """Checks if current terminal supports ANSI colors."""
    if os.environ.get("NO_COLOR"):
        return False
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


def format_console_report(report: AnalysisReport, use_color: bool | None = None) -> str:
    """Formats an AnalysisReport for terminal display."""
    color = _supports_color() if use_color is None else use_color

    if HAS_RICH and color:
        string_io = io.StringIO()
        console = Console(file=string_io, force_terminal=True, width=90)

        # Header
        console.print(
            Panel.fit(
                f"[bold cyan]CIAUTOPSY DIAGNOSTIC REPORT[/bold cyan]\n"
                f"[dim]Target: [bold]{report.log_path}[/bold] | Platform: {report.platform} | Lines: {report.total_lines:,}[/dim]",
                border_style="cyan",
            )
        )

        if not report.findings and not report.cascading_failures:
            console.print(
                "\n[green]✅ No diagnostic failure patterns detected.[/green] The log may have terminated normally or requires a custom rule.\n"
            )
            return string_io.getvalue()

        # Leading Root Cause
        if report.leading_root_cause:
            pr = report.leading_root_cause
            sev_style = (
                "bold red"
                if pr.severity == Severity.CRITICAL
                else "red"
                if pr.severity == Severity.HIGH
                else "yellow"
            )

            content_text = Text()
            content_text.append(f"[{pr.rule_id}] ", style="bold")
            content_text.append(f"{pr.title}\n", style=sev_style)
            content_text.append(
                f"Category: {pr.category.value} | Severity: {pr.severity.value} | Confidence: {int(pr.confidence * 100)}%\n",
                style="dim",
            )
            content_text.append(f"Rationale: {pr.confidence_explanation}\n\n", style="dim italic")
            content_text.append(f"{pr.description}\n\n")

            content_text.append("🔎 Log Evidence:\n", style="bold")
            for ev in pr.evidence[:3]:
                content_text.append(f"  Line {ev.line_number}: ", style="bold")
                content_text.append(f"{ev.matched_text}\n", style="red")
                if ev.context_lines:
                    for ctx_line, ctx_text in ev.context_lines:
                        prefix = "    ▶ " if ctx_line == ev.line_number else "      "
                        content_text.append(f"{prefix}{ctx_line:4d} | {ctx_text}\n", style="dim")

            content_text.append("\n💡 Actionable Fix:\n", style="bold green")
            for fix in pr.remediation.splitlines():
                content_text.append(f"  {fix}\n")

            console.print(
                Panel(
                    content_text,
                    title="🎯 Primary Root Cause Candidate",
                    border_style="red"
                    if pr.severity in (Severity.CRITICAL, Severity.HIGH)
                    else "yellow",
                )
            )

        # Other findings
        secondary = [f for f in report.findings if not f.is_primary_cause]
        if secondary:
            table = Table(title="⚠️ Other Detected Findings", border_style="yellow")
            table.add_column("Rule ID", style="bold")
            table.add_column("Finding", style="white")
            table.add_column("Category", style="dim")
            table.add_column("Severity", style="bold yellow")
            table.add_column("Line", justify="right")
            for f in secondary:
                f_line = f.evidence[0].line_number if f.evidence else 0
                table.add_row(f.rule_id, f.title, f.category.value, f.severity.value, str(f_line))
            console.print(table)

        # Cascading failures
        if report.cascading_failures:
            console.print(
                f"\n[dim]⛓️ Downstream Cascading Errors ({len(report.cascading_failures)} suppressed):[/dim]"
            )
            for cf in report.cascading_failures:
                first_line = cf.evidence[0].line_number if cf.evidence else 0
                console.print(f"  [dim]• Line {first_line}: {cf.title}[/dim]")

        # Baseline comparison
        if report.baseline_comparison:
            console.print(
                f"\n[bold blue]🔄 Baseline Comparison:[/bold blue] {report.baseline_comparison.summary}"
            )

        return string_io.getvalue()

    # Plain text / fallback formatting
    b = BOLD if color else ""
    r = RESET if color else ""
    d = DIM if color else ""
    red = RED if color else ""
    c = CYAN if color else ""

    lines: list[str] = [
        f"{b}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{r}",
        f"  🩺  {b}CIAUTOPSY DIAGNOSTIC REPORT{r}",
        f"  Target: {report.log_path}  |  Platform: {report.platform}  |  Lines: {report.total_lines:,}",
        f"{b}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{r}",
    ]

    if not report.findings and not report.cascading_failures:
        lines.append(
            f"\n{c}No diagnostic failure patterns detected.{r} "
            "The log may have terminated normally or requires a custom rule.\n"
        )
        return "\n".join(lines)

    if report.leading_root_cause:
        pr = report.leading_root_cause
        lines.append(f"\n🎯 {b}PRIMARY ROOT CAUSE CANDIDATE:{r}")
        lines.append(f"  {b}[{pr.rule_id}]{r} {red}{b}{pr.title}{r}")
        lines.append(
            f"  Category: {pr.category.value}  |  "
            f"Severity: {pr.severity.value}  |  "
            f"Confidence: {int(pr.confidence * 100)}%"
        )
        lines.append(f"  Rationale: {pr.confidence_explanation}")
        lines.append(f"\n  {d}{pr.description}{r}")

        lines.append(f"\n  {b}🔎 Log Evidence:{r}")
        for ev in pr.evidence[:3]:
            lines.append(f"    Line {b}{ev.line_number}{r}: {red}{ev.matched_text}{r}")
            if ev.context_lines:
                lines.append(f"    {d}Context snippet:{r}")
                for ctx_line, ctx_text in ev.context_lines:
                    prefix = f"      {red}▶{r} " if ctx_line == ev.line_number else "        "
                    lines.append(f"{prefix}{d}{ctx_line:4d} |{r} {ctx_text}")

        lines.append(f"\n  💡 {b}Actionable Fix:{r}")
        for fix_line in pr.remediation.splitlines():
            lines.append(f"     {fix_line}")

    secondary_findings = [f for f in report.findings if not f.is_primary_cause]
    if secondary_findings:
        lines.append(
            f"\n{b}─────────────────────────────────────────────────────────────────────{r}"
        )
        lines.append(f"⚠️  {b}OTHER DETECTED ISSUES ({len(secondary_findings)}):{r}")
        for idx, f in enumerate(secondary_findings, start=1):
            first_line = f.evidence[0].line_number if f.evidence else 0
            lines.append(f"  {idx}. [{f.rule_id}] {f.title} (Line {first_line})")

    if report.cascading_failures:
        lines.append(
            f"\n{b}─────────────────────────────────────────────────────────────────────{r}"
        )
        lines.append(
            f"⛓️  {d}DOWNSTREAM CASCADING FAILURES ({len(report.cascading_failures)} suppressed):{r}"
        )
        for c_fail in report.cascading_failures:
            first_line = c_fail.evidence[0].line_number if c_fail.evidence else 0
            lines.append(f"  • {d}{c_fail.title} (Line {first_line}){r}")

    if report.baseline_comparison:
        lines.append(
            f"\n{b}─────────────────────────────────────────────────────────────────────{r}"
        )
        lines.append(f"🔄  {b}BASELINE COMPARISON:{r} {report.baseline_comparison.summary}")

    lines.append(f"{b}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{r}\n")
    return "\n".join(lines)


def format_console_diff(diff: DiffReport, use_color: bool | None = None) -> str:
    """Formats a DiffReport for terminal display."""
    color = _supports_color() if use_color is None else use_color

    b = BOLD if color else ""
    r = RESET if color else ""
    red = RED if color else ""
    g = GREEN if color else ""

    lines: list[str] = [
        f"{b}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{r}",
        f"  🔄  {b}CIAUTOPSY BUILD COMPARISON REPORT{r}",
        f"  Failed:   {diff.failed_path}",
        f"  Baseline: {diff.baseline_path}",
        f"{b}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{r}\n",
        f"📊 {b}Summary:{r} {diff.summary}\n",
    ]

    if diff.divergence_step:
        lines.append(f"🚩 {b}Divergence Point:{r} {diff.divergence_step}\n")

    if diff.differences:
        lines.append(f"{b}Spotlight Differences:{r}")
        for item in diff.differences:
            lines.append(f"  Line {item.failed_line} (Step: {item.step or 'Global'}):")
            lines.append(f"    {g}- Baseline (L{item.baseline_line}): {item.baseline_content}{r}")
            lines.append(f"    {red}+ Failed   (L{item.failed_line}): {item.failed_content}{r}")
            lines.append("")

    lines.append(f"{b}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{r}\n")
    return "\n".join(lines)
