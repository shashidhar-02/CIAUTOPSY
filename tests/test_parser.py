"""Tests for log parsing, normalization, secret redaction, and streaming."""

import os

from ciautopsy.parsers.demuxer import parse_log_content, parse_log_file, stream_log_lines
from ciautopsy.parsers.normalizer import (
    extract_timestamp,
    normalize_line,
    strip_ansi,
)
from ciautopsy.security.redaction import redact_secrets

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def test_strip_ansi():
    colored = "\x1b[31mError:\x1b[0m something went wrong \x1b[1mbold\x1b[0m"
    assert strip_ansi(colored) == "Error: something went wrong bold"


def test_redact_secrets():
    raw = (
        "Cloning https://user:secret123@github.com/org/repo using "
        "ghp_123456789012345678901234567890123456 and AKIAIOSFODNN7EXAMPLE "
        "with Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xyz"
    )
    redacted = redact_secrets(raw)
    assert "secret123" not in redacted
    assert "ghp_123456789012345678901234567890123456" not in redacted
    assert "AKIAIOSFODNN7EXAMPLE" not in redacted
    assert "[REDACTED_GITHUB_TOKEN]" in redacted
    assert "[REDACTED_AWS_KEY]" in redacted
    assert "[REDACTED_BEARER_TOKEN]" in redacted

    # Test custom patterns
    custom_raw = "INTERNAL_CORP_ID_99998888 failed"
    custom_redacted = redact_secrets(custom_raw, custom_patterns=[r"INTERNAL_CORP_ID_\d+"])
    assert "[REDACTED_CUSTOM]" in custom_redacted


def test_extract_timestamp_iso():
    text = "2025-10-10T14:00:01.1234567Z Running build step"
    ts, remaining = extract_timestamp(text)
    assert ts == "2025-10-10T14:00:01.1234567Z"
    assert remaining == "Running build step"


def test_normalize_line():
    raw = "2025-10-10T14:00:01Z \x1b[32mBuild succeeded\x1b[0m\r\n"
    clean, ts = normalize_line(raw)
    assert clean == "Build succeeded"
    assert ts == "2025-10-10T14:00:01Z"


def test_parse_log_file_gha():
    fixture_path = os.path.join(FIXTURES_DIR, "python_missing_dep.log")
    parsed = parse_log_file(fixture_path)

    assert parsed.platform == "GitHub Actions"
    assert parsed.total_lines > 10
    assert "Run pytest tests/" in parsed.steps
    assert parsed.lines[0].step_name == "Run actions/checkout@v4"


def test_parse_log_content():
    content = "##[group]Step 1\nHello World\n##[group]Step 2\nGoodbye\n"
    parsed = parse_log_content(content)
    assert parsed.steps == ["Step 1", "Step 2"]
    assert len(parsed.lines) == 4


def test_stream_log_lines_max_lines():
    lines = [f"Line {i}\n" for i in range(100)]
    parsed_lines, _, _ = stream_log_lines(iter(lines), max_lines=10)
    assert len(parsed_lines) == 10
