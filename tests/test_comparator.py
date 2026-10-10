"""Tests for differential comparison engine."""

import os

from ciautopsy.comparison.comparator import compare_logs

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def test_compare_logs_detects_drift():
    failed_path = os.path.join(FIXTURES_DIR, "baseline_failed_drift.log")
    baseline_path = os.path.join(FIXTURES_DIR, "baseline_success.log")

    diff_report = compare_logs(failed_path=failed_path, baseline_path=baseline_path)

    assert diff_report.failed_path == failed_path
    assert diff_report.baseline_path == baseline_path
    assert len(diff_report.differences) > 0
    assert diff_report.divergence_line is not None

    serialized = diff_report.to_dict()
    assert "divergence_line" in serialized
    assert len(serialized["differences"]) > 0
