"""Comprehensive test coverage for all diagnostic rules."""

from ciautopsy.models import Category
from ciautopsy.parsers.demuxer import parse_log_content
from ciautopsy.rules.builds import (
    CascadingExitRule,
    CommandNotFoundRule,
    HeaderCompilationRule,
    SyntaxErrorRule,
)
from ciautopsy.rules.dependencies import NodeMissingModuleRule, PipConflictRule
from ciautopsy.rules.infrastructure import DiskSpaceRule, DockerPermissionRule
from ciautopsy.rules.network import NetworkConnectionRule
from ciautopsy.rules.secrets import AuthenticationFailureRule, MissingEnvVarRule
from ciautopsy.rules.testing import JestFailureRule


def test_command_not_found_rule():
    log = parse_log_content("bash: terraform: command not found\nexit 127")
    finding = CommandNotFoundRule().evaluate(log)
    assert finding is not None
    assert finding.rule_id == "CMD-001"
    assert finding.category == Category.INFRASTRUCTURE


def test_header_compilation_rule():
    log = parse_log_content("gcc main.c\nfatal error: Python.h: No such file or directory\n")
    finding = HeaderCompilationRule().evaluate(log)
    assert finding is not None
    assert finding.rule_id == "BLD-001"
    assert "Python.h" in finding.title


def test_syntax_error_rule():
    log = parse_log_content('  File "app.py", line 10\n    def foo(\nSyntaxError: invalid syntax')
    finding = SyntaxErrorRule().evaluate(log)
    assert finding is not None
    assert finding.rule_id == "SYN-001"


def test_cascading_exit_rule():
    log = parse_log_content("make: *** [all] Error 2\n")
    finding = CascadingExitRule().evaluate(log)
    assert finding is not None
    assert finding.rule_id == "CAS-001"
    assert finding.category == Category.CASCADING_FAILURE


def test_disk_space_rule():
    log = parse_log_content("write error: No space left on device\n")
    finding = DiskSpaceRule().evaluate(log)
    assert finding is not None
    assert finding.rule_id == "DSK-001"


def test_docker_permission_rule():
    log = parse_log_content(
        "Got permission denied while trying to connect to the Docker daemon socket\n"
    )
    finding = DockerPermissionRule().evaluate(log)
    assert finding is not None
    assert finding.rule_id == "DOK-001"


def test_auth_failure_rule():
    log = parse_log_content("fatal: Authentication failed for 'https://github.com/org/repo'\n")
    finding = AuthenticationFailureRule().evaluate(log)
    assert finding is not None
    assert finding.rule_id == "SEC-001"


def test_missing_env_var_rule():
    log = parse_log_content("KeyError: 'DATABASE_URL'\n")
    finding = MissingEnvVarRule().evaluate(log)
    assert finding is not None
    assert finding.rule_id == "SEC-002"
    assert "DATABASE_URL" in finding.title


def test_jest_failure_rule():
    log = parse_log_content("FAIL src/components/Button.test.tsx\nTests: 1 failed\n")
    finding = JestFailureRule().evaluate(log)
    assert finding is not None
    assert finding.rule_id == "TST-002"


def test_node_missing_module_rule():
    log = parse_log_content("Error: Cannot find module 'lodash'\n")
    finding = NodeMissingModuleRule().evaluate(log)
    assert finding is not None
    assert finding.rule_id == "DEP-004"
    assert "lodash" in finding.title


def test_pip_conflict_rule():
    log = parse_log_content("pip install foo\nResolutionImpossible: conflicting dependencies\n")
    finding = PipConflictRule().evaluate(log)
    assert finding is not None
    assert finding.rule_id == "DEP-002"


def test_network_connection_rule():
    log = parse_log_content("curl: (6) Could not resolve host: api.github.com\n")
    finding = NetworkConnectionRule().evaluate(log)
    assert finding is not None
    assert finding.rule_id == "NET-001"
    assert "Network Connection" in finding.title
