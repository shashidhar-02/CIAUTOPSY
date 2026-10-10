"""Tests for all reporting formats (Console, Markdown, JSON)."""

from ciautopsy.models import (
    AnalysisReport,
    Category,
    DiffItem,
    DiffReport,
    Evidence,
    Finding,
    Severity,
)
from ciautopsy.reports.console import format_console_diff, format_console_report
from ciautopsy.reports.json_reporter import format_json_report
from ciautopsy.reports.markdown import format_markdown_diff, format_markdown_report


def test_console_report_empty():
    report = AnalysisReport(
        log_path="clean.log",
        total_lines=10,
        platform="GitHub Actions",
        findings=[],
        cascading_failures=[],
    )
    output = format_console_report(report, use_color=False)
    assert "No diagnostic failure patterns detected" in output


def test_console_report_with_findings():
    ev = Evidence(
        line_number=5,
        matched_text="Error: foo",
        context_lines=[(4, "before"), (5, "Error: foo"), (6, "after")],
    )
    f1 = Finding(
        rule_id="TST-001",
        title="Primary Test Failure",
        description="A test failed",
        category=Category.TEST_FAILURE,
        severity=Severity.HIGH,
        remediation="Fix the test",
        evidence=[ev],
        is_primary_cause=True,
    )
    f2 = Finding(
        rule_id="DEP-001",
        title="Secondary Dep Warning",
        description="Dep problem",
        category=Category.DEPENDENCY,
        severity=Severity.MEDIUM,
        remediation="Install dep",
        evidence=[ev],
    )
    cascade = Finding(
        rule_id="CAS-001",
        title="Exit code 1",
        description="Cascading exit",
        category=Category.CASCADING_FAILURE,
        severity=Severity.LOW,
        remediation="Fix primary",
        evidence=[ev],
    )
    report = AnalysisReport(
        log_path="test.log",
        total_lines=20,
        platform="GitHub Actions",
        findings=[f1, f2],
        leading_root_cause=f1,
        cascading_failures=[cascade],
    )

    output = format_console_report(report, use_color=False)
    assert "PRIMARY ROOT CAUSE CANDIDATE" in output
    assert "OTHER DETECTED ISSUES" in output
    assert "DOWNSTREAM CASCADING FAILURES" in output


def test_console_report_rich_colored():
    ev = Evidence(
        line_number=5,
        matched_text="Error: foo",
        context_lines=[(4, "before"), (5, "Error: foo"), (6, "after")],
    )
    f1 = Finding(
        rule_id="TST-001",
        title="Primary Test Failure",
        description="A test failed",
        category=Category.TEST_FAILURE,
        severity=Severity.HIGH,
        remediation="Fix the test",
        evidence=[ev],
        is_primary_cause=True,
    )
    f2 = Finding(
        rule_id="DEP-001",
        title="Secondary Dep Warning",
        description="Dep problem",
        category=Category.DEPENDENCY,
        severity=Severity.MEDIUM,
        remediation="Install dep",
        evidence=[ev],
    )
    report = AnalysisReport(
        log_path="test.log",
        total_lines=20,
        platform="GitHub Actions",
        findings=[f1, f2],
        leading_root_cause=f1,
    )
    output = format_console_report(report, use_color=True)
    assert "CIAUTOPSY DIAGNOSTIC REPORT" in output
    assert "TST-001" in output


def test_console_diff():
    diff = DiffReport(
        failed_path="failed.log",
        baseline_path="passed.log",
        divergence_step="Diverged at test",
        divergence_line=12,
        summary="Compared runs",
        differences=[
            DiffItem(
                step="test",
                failed_line=12,
                baseline_line=12,
                description="line diff",
                failed_content="fail",
                baseline_content="pass",
            )
        ],
    )
    output = format_console_diff(diff, use_color=False)
    assert "CIAUTOPSY BUILD COMPARISON REPORT" in output
    assert "Divergence Point:" in output


def test_markdown_report():
    report = AnalysisReport(
        log_path="clean.log",
        total_lines=10,
        platform="GitHub Actions",
        findings=[],
        cascading_failures=[],
    )
    output = format_markdown_report(report)
    assert "No diagnostic failure patterns detected" in output


def test_markdown_diff():
    diff = DiffReport(
        failed_path="failed.log",
        baseline_path="passed.log",
        divergence_step="Diverged at step 2",
        divergence_line=5,
        summary="Summary test",
        differences=[
            DiffItem(
                step="build",
                failed_line=5,
                baseline_line=5,
                description="diff",
                failed_content="Error | pipe",
                baseline_content="Success",
            )
        ],
    )
    md = format_markdown_diff(diff)
    assert "# 🔄 CIAUTOPSY Build Comparison Report" in md
    assert "Divergence Point" in md
    assert "Error \\| pipe" in md


def test_json_report():
    report = AnalysisReport(
        log_path="run.log",
        total_lines=5,
        platform="Generic CI",
        findings=[],
    )
    json_out = format_json_report(report)
    assert '"total_lines": 5' in json_out
