"""Ingest package for CIAUTOPSY."""

from ciautopsy.ingest.archive import ingest_zip_archive, is_safe_member_name
from ciautopsy.ingest.reader import ingest_target

__all__ = ["ingest_target", "ingest_zip_archive", "is_safe_member_name"]
