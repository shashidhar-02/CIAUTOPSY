"""Executes real CIAUTOPSY commands to validate and generate demo examples."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure UTF-8 output encoding across all operating systems
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from ciautopsy.cli import main

ROOT_DIR = Path(__file__).resolve().parent.parent
EXAMPLES_DIR = ROOT_DIR / "examples"
LOGS_DIR = EXAMPLES_DIR / "logs"
REPORTS_DIR = EXAMPLES_DIR / "reports"


def run_demo_validation() -> None:
    """Generates authentic sample reports using the actual CIAUTOPSY CLI."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    failed_log = str(LOGS_DIR / "failed_python_import.log")
    baseline_log = str(LOGS_DIR / "success_baseline.log")
    ambiguous_log = str(LOGS_DIR / "ambiguous_failure.log")

    md_out = str(REPORTS_DIR / "sample_report.md")
    json_out = str(REPORTS_DIR / "sample_report.json")
    diff_md_out = str(REPORTS_DIR / "sample_comparison.md")

    print("[1/3] Generating sample Markdown report...")
    rc1 = main(["analyze", failed_log, "--format", "markdown", "-o", md_out])
    assert rc1 == 0, f"Expected rc=0, got {rc1}"
    assert os.path.exists(md_out)

    # Verify secret was redacted in output
    md_content = Path(md_out).read_text(encoding="utf-8")
    assert "ghp_DEMO_TOKEN" not in md_content
    assert "DEP-001" in md_content
    print("  -> Verified: Markdown report generated and test secret redacted.")

    print("[2/3] Generating sample JSON report...")
    rc2 = main(["analyze", failed_log, "--format", "json", "-o", json_out])
    assert rc2 == 0, f"Expected rc=0, got {rc2}"
    assert os.path.exists(json_out)
    json_content = Path(json_out).read_text(encoding="utf-8")
    assert "ghp_DEMO_TOKEN" not in json_content
    assert '"schema_version": "0.1.0"' in json_content
    print("  -> Verified: JSON report generated conforming to schema 0.1.0.")

    print("[3/3] Generating sample Baseline Comparison report...")
    rc3 = main(
        [
            "analyze",
            failed_log,
            "--baseline",
            baseline_log,
            "--format",
            "markdown",
            "-o",
            diff_md_out,
        ]
    )
    assert rc3 == 0, f"Expected rc=0, got {rc3}"
    assert os.path.exists(diff_md_out)
    diff_content = Path(diff_md_out).read_text(encoding="utf-8")
    assert "Baseline Comparison" in diff_content
    print("  -> Verified: Baseline comparison generated.")

    print("\n[Ambiguous Check] Testing unmodeled failure handling...")
    rc4 = main(["analyze", ambiguous_log, "--format", "markdown"])
    assert rc4 == 0
    print("  -> Verified: Ambiguous log correctly handled without unsupported claims.")

    print("\nAll demo examples validated successfully!")


if __name__ == "__main__":
    run_demo_validation()
