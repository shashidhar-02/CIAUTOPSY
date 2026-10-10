"""Tests for the command-line interface (CLI)."""

import json
import os
from pathlib import Path

from ciautopsy.cli import main

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def test_cli_version(capsys):
    exit_code = main(["version"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "ciautopsy 0.1.0" in captured.out


def test_cli_rules(capsys):
    exit_code = main(["rules"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "DEP-001" in captured.out
    assert "OOM-001" in captured.out


def test_cli_analyze_json(capsys):
    fixture = os.path.join(FIXTURES_DIR, "python_missing_dep.log")
    exit_code = main(["analyze", fixture, "--format", "json", "--no-color"])
    assert exit_code == 0  # Analysis completed successfully
    captured = capsys.readouterr()

    data = json.loads(captured.out)
    assert data["leading_root_cause"]["rule_id"] == "DEP-001"
    assert "pydantic_settings" in data["leading_root_cause"]["title"]


def test_cli_analyze_markdown(capsys):
    fixture = os.path.join(FIXTURES_DIR, "docker_oom.log")
    exit_code = main(["analyze", fixture, "--format", "markdown", "--no-color"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "# 🩺 CIAUTOPSY Diagnostic Report" in captured.out
    assert "OOM-001" in captured.out


def test_cli_analyze_output_file(tmp_path: Path):
    fixture = os.path.join(FIXTURES_DIR, "python_missing_dep.log")
    out_file = tmp_path / "subdir" / "test_report.md"
    exit_code = main(["analyze", fixture, "--format", "markdown", "-o", str(out_file)])
    assert exit_code == 0
    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    assert "DEP-001" in content


def test_cli_analyze_with_baseline(capsys):
    failed = os.path.join(FIXTURES_DIR, "baseline_failed_drift.log")
    baseline = os.path.join(FIXTURES_DIR, "baseline_success.log")
    exit_code = main(["analyze", failed, "--baseline", baseline, "--format", "json"])
    assert exit_code == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["baseline_comparison"] is not None
    assert "divergence_line" in data["baseline_comparison"]


def test_cli_missing_file():
    exit_code = main(["analyze", "non_existent_file.log"])
    assert exit_code == 2
