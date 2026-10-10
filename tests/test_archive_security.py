"""Security and safety tests for ZIP archive ingestion."""

import io
import zipfile

import pytest

from ciautopsy.config import IngestionConfig
from ciautopsy.errors import ArchiveSecurityError, InputValidationError
from ciautopsy.ingest.archive import ingest_zip_archive, is_safe_member_name
from ciautopsy.parsers.demuxer import parse_log_target


def test_is_safe_member_name():
    assert is_safe_member_name("build.log") is True
    assert is_safe_member_name("logs/ci/test.log") is True

    # Traversal attempts
    assert is_safe_member_name("../secret.txt") is False
    assert is_safe_member_name("logs/../../secret.txt") is False
    assert is_safe_member_name("/etc/passwd") is False
    assert is_safe_member_name("\\Windows\\system32") is False
    assert is_safe_member_name("C:boot.ini") is False
    assert is_safe_member_name("C:\\boot.ini") is False
    assert is_safe_member_name("") is False


def test_ingest_valid_zip(tmp_path):
    zip_path = tmp_path / "valid_run.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr(
            "run/build.log",
            "2025-10-10T14:00:00Z ##[group]Run test\nPassed\n",
        )

    member_name, content = ingest_zip_archive(str(zip_path))
    assert member_name == "run/build.log"
    assert "Run test" in content

    # Test full parser on ZIP
    parsed = parse_log_target(str(zip_path))
    assert parsed.total_lines == 2
    assert "Run test" in parsed.steps


def test_reject_zip_path_traversal(tmp_path):
    zip_path = tmp_path / "evil.zip"

    # Create zip with directory traversal entry
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        zf.writestr("../../../evil.sh", "echo pwned")

    zip_path.write_bytes(zip_buffer.getvalue())

    with pytest.raises(ArchiveSecurityError, match="Unsafe path detected"):
        ingest_zip_archive(str(zip_path))


def test_reject_zip_member_count_limit(tmp_path):
    zip_path = tmp_path / "too_many_members.zip"
    config = IngestionConfig(max_member_count=5)

    with zipfile.ZipFile(zip_path, "w") as zf:
        for i in range(10):
            zf.writestr(f"file_{i}.log", f"Line {i}")

    with pytest.raises(ArchiveSecurityError, match="member count exceeds limit"):
        ingest_zip_archive(str(zip_path), config=config)


def test_reject_zip_size_limit(tmp_path):
    zip_path = tmp_path / "large.zip"
    config = IngestionConfig(max_archive_bytes=100)

    # Write 500 bytes to zip
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("test.log", "a" * 500)

    with pytest.raises(ArchiveSecurityError, match="exceeds maximum allowed size"):
        ingest_zip_archive(str(zip_path), config=config)


def test_reject_empty_or_no_log_zip(tmp_path):
    zip_path = tmp_path / "empty.zip"
    with zipfile.ZipFile(zip_path, "w"):
        pass

    with pytest.raises(InputValidationError, match="No readable log files"):
        ingest_zip_archive(str(zip_path))
