"""Security and redaction engine for masking secrets in log evidence and reports."""

from __future__ import annotations

import re
from re import Pattern

# Built-in secret patterns with corresponding redaction placeholders
BUILTIN_SECRET_PATTERNS: list[tuple[Pattern[str], str]] = [
    # GitHub Tokens
    (
        re.compile(
            r"(ghp_[A-Za-z0-9_]{36,}|gho_[A-Za-z0-9_]{36,}|ghs_[A-Za-z0-9_]{36,}|github_pat_[A-Za-z0-9_]{22,})"
        ),
        "[REDACTED_GITHUB_TOKEN]",
    ),
    # AWS Access Key ID
    (re.compile(r"\b(AKIA[0-9A-Z]{16})\b"), "[REDACTED_AWS_KEY]"),
    # Bearer Authorization headers
    (
        re.compile(r"(Bearer\s+)[a-zA-Z0-9_\-\.]{20,}", re.IGNORECASE),
        r"\1[REDACTED_BEARER_TOKEN]",
    ),
    # Basic auth embedded in URLs: https://user:pass@domain.com
    (
        re.compile(r"://([^/\s:@]+):([^/\s:@]+)@"),
        r"://[REDACTED_USER]:[REDACTED_PASS]@",
    ),
    # Database connection strings: postgres://user:pass@host:5432/db
    (
        re.compile(r"(?i)(postgres|postgresql|mysql|mongodb|redis)://([^/\s:@]+):([^/\s:@]+)@"),
        r"\1://[REDACTED_USER]:[REDACTED_PASS]@",
    ),
    # Slack Tokens
    (
        re.compile(r"\b(xox[baprs]-[0-9a-zA-Z\-]{24,})\b"),
        "[REDACTED_SLACK_TOKEN]",
    ),
    # Password / Token assignment: token=abcdef123456 or password: "secret"
    (
        re.compile(
            r"(?i)\b(password|passwd|secret|api[_-]?key|access[_-]?token)\s*([:=])\s*['\"]?([A-Za-z0-9_\-\.]{8,})['\"]?"
        ),
        r"\1\2[REDACTED_CREDENTIAL]",
    ),
    # Private Key blocks
    (
        re.compile(r"-----BEGIN [A-Z ]+PRIVATE KEY-----"),
        "[REDACTED_PRIVATE_KEY_START]",
    ),
]


def redact_secrets(text: str, custom_patterns: list[str] | None = None) -> str:
    """
    Masks known credentials, tokens, and authorization secrets in text.
    Preserves exact line breaks and structure.
    """
    if not text:
        return text

    sanitized = text

    # Apply built-in patterns
    for pattern, replacement in BUILTIN_SECRET_PATTERNS:
        sanitized = pattern.sub(replacement, sanitized)

    # Apply custom user-specified regex patterns if supplied
    if custom_patterns:
        for pat_str in custom_patterns:
            try:
                custom_pat = re.compile(pat_str)
                sanitized = custom_pat.sub("[REDACTED_CUSTOM]", sanitized)
            except re.error:
                # Malformed custom pattern; continue safely
                continue

    return sanitized
