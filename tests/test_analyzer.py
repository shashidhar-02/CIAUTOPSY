"""Tests for core analyzer and root-cause ranking."""

import os

from ciautopsy.engine.analyzer import analyze_log
from ciautopsy.models import Category

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def test_analyzer_identifies_primary_root_cause_over_cascade():
    fixture_path = os.path.join(FIXTURES_DIR, "python_missing_dep.log")
    report = analyze_log(fixture_path)

    assert report.primary_root_cause is not None
    # Root cause must be the missing dependency DEP-001, NOT the cascading exit code CAS-001
    assert report.primary_root_cause.rule_id == "DEP-001"
    assert report.primary_root_cause.is_primary_cause is True
    assert report.primary_root_cause.category == Category.DEPENDENCY

    # Cascading failure should be suppressed into cascading_failures
    cascading_ids = [cf.rule_id for cf in report.cascading_failures]
    assert "CAS-001" in cascading_ids


def test_analyzer_report_serialization():
    fixture_path = os.path.join(FIXTURES_DIR, "docker_oom.log")
    report = analyze_log(fixture_path)

    report_dict = report.to_dict()
    assert report_dict["total_lines"] > 0
    assert report_dict["primary_root_cause"]["rule_id"] == "OOM-001"
    assert len(report_dict["findings"]) >= 1


def test_analyzer_max_lines():
    fixture_path = os.path.join(FIXTURES_DIR, "docker_oom.log")
    report = analyze_log(fixture_path, max_lines=5)
    assert report.total_lines == 5
