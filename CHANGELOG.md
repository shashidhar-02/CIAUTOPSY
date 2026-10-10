# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-10-10

### Added
- **Core CLI (`ciautopsy`)**:
  - `ciautopsy analyze <target>`: Ingest and diagnose failed CI/CD log files (`.log`, `.txt`) or ZIP archives (`.zip`).
  - `--baseline <log>`: Differential build analysis to spotlight newly introduced errors versus the preceding successful run.
  - `--format [console|markdown|json]`: Multi-format report export.
  - `--output <path>`: Write reports to file destination.
  - `--max-lines <n>`: Configurable line ingestion bounds.
  - `ciautopsy rules`: Catalog viewer listing all active diagnostic rules and categories.
  - `ciautopsy version`: Displays version metadata and JSON schema compatibility.
- **Diagnostic Engine & Rules Catalog**:
  - `DEP-001`: Python `ModuleNotFoundError` / `ImportError`.
  - `DEP-002`: Python `pip` dependency resolution conflict.
  - `DEP-003`: Node.js npm `ERESOLVE` dependency tree clash.
  - `DEP-004`: Node.js `MODULE_NOT_FOUND`.
  - `OOM-001`: Linux OOM killer & Docker container exit code 137.
  - `TIM-001`: GitHub Actions & CI runner execution timeouts.
  - `DSK-001`: Storage failure (`No space left on device`).
  - `DOK-001`: Docker daemon socket permission errors.
  - `CMD-001`: Missing executable / command not found (exit code 127).
  - `BLD-001`: C/C++ compilation & missing header file failures.
  - `SYN-001`: Source code syntax and indentation errors.
  - `CAS-001`: Downstream cascading exit status detection (suppresses secondary exit noise).
  - `TST-001`: Pytest test suite assertions and regressions.
  - `TST-002`: Jest test suite failures.
  - `SEC-001`: Unauthorized / authentication failure (HTTP 401/403).
  - `SEC-002`: Missing environment variables and configuration secrets.
  - `NET-001`: Network timeout, DNS resolution failure, and connection resets.
- **Cascading Failure Suppression**:
  - Distinguishes primary root-cause triggers from secondary exit failures (`exit code 1`).
  - Groups related symptoms while preserving complete source line evidence.
- **Security & Ingestion Safeguards**:
  - Safe ZIP ingestion with path traversal (`..`, absolute paths) defenses.
  - Zip-bomb protections: member count limits, uncompressed size limits, and 100:1 compression ratio limits.
  - Best-effort secret redaction (GitHub PATs, AWS access keys, Bearer tokens, URLs with credentials, DB URIs, Private Keys).
  - Stream line truncation guards to prevent ReDoS.
  - Zero cloud network calls; zero external LLM dependencies.
- **Reporting**:
  - 10-section standardized Markdown autopsy report.
  - Schema-versioned JSON report (`schema_version: "0.1.0"`).
  - Rich ANSI/Unicode colorized terminal presentation with fallback.
- **Synthetic Benchmark**:
  - Reproducible benchmark corpus (`scripts/run_benchmark.py`) with empirical metrics.
- **Test Suite**:
  - 48 automated unit, integration, CLI, and archive security tests with 93% code coverage.
