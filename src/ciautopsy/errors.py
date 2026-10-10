"""Structured error hierarchy for CIAUTOPSY."""

from __future__ import annotations


class CiautopsyError(Exception):
    """Base exception for all CIAUTOPSY errors."""

    def __init__(self, message: str, exit_code: int = 3) -> None:
        super().__init__(message)
        self.message = message
        self.exit_code = exit_code


class InputValidationError(CiautopsyError):
    """Raised when an input file, path, or argument is invalid or missing."""

    def __init__(self, message: str) -> None:
        super().__init__(message, exit_code=2)


class ArchiveSecurityError(CiautopsyError):
    """Raised when an archive violates security constraints (path traversal, zip bomb)."""

    def __init__(self, message: str) -> None:
        super().__init__(message, exit_code=2)


class AnalysisProcessingError(CiautopsyError):
    """Raised when an unexpected error occurs during log analysis."""

    def __init__(self, message: str) -> None:
        super().__init__(message, exit_code=3)
