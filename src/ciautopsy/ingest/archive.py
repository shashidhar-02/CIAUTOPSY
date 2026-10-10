"""Safe ZIP archive ingestion with zip bomb and path traversal protection."""

from __future__ import annotations

import os
import zipfile

from ciautopsy.config import DEFAULT_INGESTION_CONFIG, IngestionConfig
from ciautopsy.errors import ArchiveSecurityError, InputValidationError


def is_safe_member_name(name: str) -> bool:
    """
    Validates that a ZIP member filename does not contain path traversal vectors.
    Rejects absolute paths, drive letters, and directory climbing ('..').
    """
    if not name or name.startswith("/") or name.startswith("\\"):
        return False

    # Check for Windows drive letters (e.g., C:)
    if len(name) >= 2 and name[1] == ":":
        return False

    # Normalize path and verify it stays within relative boundary
    normalized = os.path.normpath(name)
    if normalized.startswith("..") or os.path.isabs(normalized):
        return False

    # Split components and ensure no '..'
    parts = normalized.replace("\\", "/").split("/")
    if any(part == ".." for part in parts):
        return False

    return True


def ingest_zip_archive(
    zip_path: str,
    config: IngestionConfig = DEFAULT_INGESTION_CONFIG,
) -> tuple[str, str]:
    """
    Safely opens a ZIP archive, validates security boundaries,
    and returns (selected_member_name, decoded_content_text).
    """
    if not os.path.exists(zip_path):
        raise InputValidationError(f"Archive file not found: {zip_path}")

    # Check compressed file size
    compressed_size = os.path.getsize(zip_path)
    if compressed_size > config.max_archive_bytes:
        raise ArchiveSecurityError(
            f"Archive exceeds maximum allowed size ({compressed_size:,} bytes > {config.max_archive_bytes:,} bytes)"
        )

    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            members = zf.infolist()

            if len(members) > config.max_member_count:
                raise ArchiveSecurityError(
                    f"Archive member count exceeds limit ({len(members)} > {config.max_member_count})"
                )

            total_uncompressed = sum(m.file_size for m in members)
            if total_uncompressed > config.max_uncompressed_bytes:
                raise ArchiveSecurityError(
                    f"Total uncompressed size exceeds limit ({total_uncompressed:,} > {config.max_uncompressed_bytes:,} bytes)"
                )

            # Check compression ratio to prevent zip bombs
            if compressed_size > 0:
                ratio = total_uncompressed / compressed_size
                if ratio > config.max_compression_ratio:
                    raise ArchiveSecurityError(
                        f"Suspicious compression ratio detected ({ratio:.1f} > {config.max_compression_ratio})"
                    )

            # Filter valid candidate log members
            log_candidates: list[zipfile.ZipInfo] = []
            for member in members:
                # Check member name safety
                if not is_safe_member_name(member.filename):
                    raise ArchiveSecurityError(
                        f"Unsafe path detected in archive member: '{member.filename}'"
                    )

                if member.is_dir():
                    continue

                if member.file_size > config.max_single_file_bytes:
                    continue

                # Filter text/log extensions
                lower_name = member.filename.lower()
                if (
                    lower_name.endswith((".log", ".txt", ".out"))
                    or "log" in lower_name
                    or "/" not in lower_name
                ):
                    log_candidates.append(member)

            if not log_candidates:
                # If no specific .log files, consider all safe non-dir files
                log_candidates = [m for m in members if not m.is_dir()]

            if not log_candidates:
                raise InputValidationError("No readable log files found in archive")

            # Sort candidate by size descending or name to find the main CI log
            log_candidates.sort(key=lambda m: m.file_size, reverse=True)
            chosen_member = log_candidates[0]

            # Read selected member into memory safely without extracting to disk
            with zf.open(chosen_member) as f:
                content_bytes = f.read(config.max_single_file_bytes)
                content = content_bytes.decode("utf-8", errors="replace")

            return chosen_member.filename, content

    except zipfile.BadZipFile as e:
        raise InputValidationError(f"Invalid or corrupted ZIP archive: {e}") from e
