"""Demuxes raw and archive CI/CD logs into structured lines with step tracking."""

from __future__ import annotations

import re
from collections.abc import Iterator

from ciautopsy.config import DEFAULT_INGESTION_CONFIG, IngestionConfig
from ciautopsy.ingest.reader import ingest_target
from ciautopsy.models import LogLine, ParsedLog
from ciautopsy.parsers.normalizer import normalize_line

GHA_GROUP_PATTERN = re.compile(r"^##\[group\](.*)$")
GHA_SECTION_PATTERN = re.compile(r"^##\[section\](.*)$")
GITLAB_SECTION_START = re.compile(r"section_start:\d+:([a-zA-Z0-9_\-\.]+)")
GENERIC_STEP_PATTERN = re.compile(
    r"^(?:===|---|\*\*\*)\s*Step:\s*(.*?)\s*(?:===|---|\*\*\*)$", re.IGNORECASE
)


def stream_log_lines(
    line_iterator: Iterator[str],
    max_lines: int | None = 100_000,
    max_line_length: int = 16_384,
) -> tuple[list[LogLine], list[str], str]:
    """
    Streams raw lines and parses them into structured LogLine instances.
    Returns (parsed_lines, steps_seen, platform).
    """
    parsed_lines: list[LogLine] = []
    current_step: str | None = "Initialization"
    steps_seen: list[str] = []
    gha_hits = 0
    gitlab_hits = 0

    for idx, raw in enumerate(line_iterator, start=1):
        if max_lines and idx > max_lines:
            break

        clean, timestamp = normalize_line(raw, max_line_length=max_line_length)

        # Step detection: GitHub Actions
        gha_group_match = GHA_GROUP_PATTERN.match(clean)
        if gha_group_match:
            current_step = gha_group_match.group(1).strip()
            if current_step not in steps_seen:
                steps_seen.append(current_step)
            gha_hits += 1

        gha_section_match = GHA_SECTION_PATTERN.match(clean)
        if gha_section_match:
            current_step = gha_section_match.group(1).strip()
            if current_step not in steps_seen:
                steps_seen.append(current_step)
            gha_hits += 1

        # Step detection: GitLab CI
        gitlab_match = GITLAB_SECTION_START.search(clean)
        if gitlab_match:
            current_step = gitlab_match.group(1)
            if current_step not in steps_seen:
                steps_seen.append(current_step)
            gitlab_hits += 1

        # Step detection: Generic step header
        generic_match = GENERIC_STEP_PATTERN.match(clean)
        if generic_match:
            current_step = generic_match.group(1).strip()
            if current_step not in steps_seen:
                steps_seen.append(current_step)

        # Platform heuristics
        if "github.com/actions" in clean or "GITHUB_WORKSPACE" in clean or "Run actions/" in clean:
            gha_hits += 1

        parsed_lines.append(
            LogLine(
                line_number=idx,
                raw_text=raw,
                clean_text=clean,
                timestamp=timestamp,
                step_name=current_step,
            )
        )

    platform = "Generic CI"
    if gha_hits > 0:
        platform = "GitHub Actions"
    elif gitlab_hits > 0:
        platform = "GitLab CI"

    return parsed_lines, steps_seen, platform


def parse_log_target(
    target_path: str,
    config: IngestionConfig = DEFAULT_INGESTION_CONFIG,
) -> ParsedLog:
    """
    Ingests any target (plain log or zip) and produces a ParsedLog.
    """
    identifier, content, metadata = ingest_target(target_path, config=config)
    lines_iter = iter(content.splitlines())
    parsed_lines, steps, platform = stream_log_lines(
        lines_iter,
        max_lines=config.max_lines,
        max_line_length=config.max_line_length,
    )

    return ParsedLog(
        filepath=identifier,
        lines=parsed_lines,
        total_lines=len(parsed_lines),
        steps=steps,
        platform=platform,
    )


def parse_log_file(filepath: str, max_lines: int | None = 100_000) -> ParsedLog:
    """Convenience helper for file parsing."""
    config = IngestionConfig(max_lines=max_lines or 100_000)
    return parse_log_target(filepath, config=config)


def parse_log_content(
    content: str,
    filepath: str = "stream",
    max_lines: int | None = 100_000,
) -> ParsedLog:
    """Convenience helper for raw string parsing."""
    lines_iter = iter(content.splitlines())
    parsed_lines, steps, platform = stream_log_lines(lines_iter, max_lines=max_lines)

    return ParsedLog(
        filepath=filepath,
        lines=parsed_lines,
        total_lines=len(parsed_lines),
        steps=steps,
        platform=platform,
    )
