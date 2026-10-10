"""Unified input ingestion handling plain text logs and ZIP archives."""

from __future__ import annotations

import os
from typing import Any

from ciautopsy.config import DEFAULT_INGESTION_CONFIG, IngestionConfig
from ciautopsy.errors import InputValidationError
from ciautopsy.ingest.archive import ingest_zip_archive


def ingest_target(
    target_path: str,
    config: IngestionConfig = DEFAULT_INGESTION_CONFIG,
) -> tuple[str, str, dict[str, Any]]:
    """
    Ingests a target path (file or zip archive).
    Returns (safe_identifier, content, metadata).
    """
    if not os.path.exists(target_path):
        raise InputValidationError(f"Input file not found: {target_path}")

    lower_path = target_path.lower()
    if lower_path.endswith(".zip"):
        member_name, content = ingest_zip_archive(target_path, config=config)
        metadata = {
            "archive_path": target_path,
            "member_name": member_name,
            "is_archive": True,
            "size_bytes": os.path.getsize(target_path),
        }
        return f"{target_path}::{member_name}", content, metadata

    # Plain text file ingestion
    file_size = os.path.getsize(target_path)
    if file_size > config.max_file_bytes:
        raise InputValidationError(
            f"Log file exceeds size limit ({file_size:,} bytes > {config.max_file_bytes:,} bytes)"
        )

    with open(target_path, encoding="utf-8", errors="replace") as f:
        content = f.read()

    metadata = {
        "file_path": target_path,
        "is_archive": False,
        "size_bytes": file_size,
    }
    return target_path, content, metadata
