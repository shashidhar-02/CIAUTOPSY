"""Configuration defaults and limits for CIAUTOPSY."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class IngestionConfig:
    """Limits and guardrails for log and archive ingestion."""

    max_lines: int = 100_000
    max_line_length: int = 16_384  # 16 KB per line truncation guard
    max_file_bytes: int = 100 * 1024 * 1024  # 100 MB for plain text logs

    # ZIP archive security limits
    max_archive_bytes: int = 100 * 1024 * 1024  # 100 MB compressed
    max_uncompressed_bytes: int = 250 * 1024 * 1024  # 250 MB total uncompressed
    max_member_count: int = 500  # Max files inside ZIP
    max_single_file_bytes: int = 50 * 1024 * 1024  # 50 MB max per single member
    max_compression_ratio: float = 100.0  # Max uncompressed / compressed ratio


@dataclass(frozen=True, slots=True)
class SecurityConfig:
    """Security and redaction options."""

    redact_secrets: bool = True
    custom_secret_patterns: list[str] = field(default_factory=list)


DEFAULT_INGESTION_CONFIG = IngestionConfig()
DEFAULT_SECURITY_CONFIG = SecurityConfig()
