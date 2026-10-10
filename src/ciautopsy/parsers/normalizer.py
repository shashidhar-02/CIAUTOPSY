"""Log line normalizer, stripping ANSI codes and extracting timestamps."""

from __future__ import annotations

import re

from ciautopsy.security.redaction import redact_secrets

ANSI_ESCAPE_PATTERN = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

TIMESTAMP_PATTERNS = [
    re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z?)\s*"),
    re.compile(r"^\[(\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:\.\d+)?)\]\s*"),
    re.compile(r"^(\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2}:\d{2})\s*"),
]


def strip_ansi(text: str) -> str:
    """Removes ANSI color and control characters from log text."""
    return ANSI_ESCAPE_PATTERN.sub("", text)


def extract_timestamp(text: str) -> tuple[str | None, str]:
    """Extracts a leading timestamp if present, returning (timestamp, remaining_text)."""
    for pattern in TIMESTAMP_PATTERNS:
        match = pattern.match(text)
        if match:
            timestamp = match.group(1)
            remaining = text[match.end() :]
            return timestamp, remaining
    return None, text


def normalize_line(
    raw: str,
    sanitize: bool = True,
    max_line_length: int = 16_384,
) -> tuple[str, str | None]:
    """
    Normalizes a single log line:
    1. Truncates extreme pathological line lengths.
    2. Strips ANSI escape sequences and carriage returns.
    3. Extracts leading timestamp.
    4. Redacts secrets if sanitize is True.

    Returns (clean_text, timestamp).
    """
    truncated = raw[:max_line_length]
    clean = strip_ansi(truncated)
    clean = clean.replace("\r", "")
    timestamp, clean = extract_timestamp(clean)

    if sanitize:
        clean = redact_secrets(clean)

    return clean.strip(), timestamp
