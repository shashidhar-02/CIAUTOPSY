"""Tests for individual diagnostic rules."""

import os

from ciautopsy.models import Category, Severity
from ciautopsy.parsers.demuxer import parse_log_file
from ciautopsy.rules import RuleRegistry
from ciautopsy.rules.dependencies import (
    NpmEresolveRule,
    PythonMissingModuleRule,
)
from ciautopsy.rules.infrastructure import OutOfMemoryRule, StepTimeoutRule

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def test_python_missing_module_rule():
    parsed = parse_log_file(os.path.join(FIXTURES_DIR, "python_missing_dep.log"))
    rule = PythonMissingModuleRule()
    finding = rule.evaluate(parsed)

    assert finding is not None
    assert finding.rule_id == "DEP-001"
    assert "pydantic_settings" in finding.title
    assert finding.category == Category.DEPENDENCY
    assert finding.severity == Severity.HIGH
    assert len(finding.evidence) == 1
    assert finding.evidence[0].metadata["module"] == "pydantic_settings"


def test_docker_oom_rule():
    parsed = parse_log_file(os.path.join(FIXTURES_DIR, "docker_oom.log"))
    rule = OutOfMemoryRule()
    finding = rule.evaluate(parsed)

    assert finding is not None
    assert finding.rule_id == "OOM-001"
    assert finding.severity == Severity.CRITICAL
    assert finding.category == Category.OUT_OF_MEMORY


def test_npm_eresolve_rule():
    parsed = parse_log_file(os.path.join(FIXTURES_DIR, "node_eresolve.log"))
    rule = NpmEresolveRule()
    finding = rule.evaluate(parsed)

    assert finding is not None
    assert finding.rule_id == "DEP-003"
    assert finding.category == Category.DEPENDENCY


def test_timeout_rule():
    parsed = parse_log_file(os.path.join(FIXTURES_DIR, "gha_timeout.log"))
    rule = StepTimeoutRule()
    finding = rule.evaluate(parsed)

    assert finding is not None
    assert finding.rule_id == "TIM-001"
    assert finding.category == Category.TIMEOUT


def test_rule_registry_contains_rules():
    rules = RuleRegistry.get_all_rules()
    assert len(rules) >= 8
    rule_ids = {r.rule_id for r in rules}
    assert "DEP-001" in rule_ids
    assert "OOM-001" in rule_ids
    assert "TIM-001" in rule_ids
    assert "CAS-001" in rule_ids
