# Security Policy

## Supported Versions

Only the latest active minor release receives security updates and vulnerability patches.

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1.0 | :x:                |

---

## Reporting a Vulnerability

We take the security of CIAUTOPSY seriously. If you believe you have found a security vulnerability in CIAUTOPSY, please report it responsibly:

1. **Do not create a public GitHub issue.**
2. Report the vulnerability privately via **GitHub Security Advisories** on the repository page (`Security` -> `Advisories` -> `Report a vulnerability`).
3. If GitHub Private Vulnerability Reporting is unavailable, open a confidential issue requesting secure communication channels without including sensitive proof-of-concept payloads in public text.

### What to Include

Please provide:
- A clear description of the vulnerability.
- Step-by-step reproduction instructions or a minimal test case.
- Impact assessment (e.g., path traversal, denial of service via regex, information disclosure).
- Any proposed remediation or patch.

We will acknowledge receipt within 48 business hours and provide status updates as we investigate and prepare a coordinated fix.

---

## Security Model & Threat Boundaries

CIAUTOPSY is designed as an offline, local-first CLI tool for analyzing untrusted CI/CD build logs.

### 1. Untrusted Input Handling
- **ZIP Ingestion Limits:** Input archives are parsed in memory with strict validation:
  - Path traversal defense (`..`, absolute paths, Windows drive letters, backslashes are rejected).
  - Maximum archive file size: 50 MB (configurable).
  - Maximum uncompressed member size: 100 MB (configurable).
  - Maximum member count: 200 files.
  - Pathological compression ratio defense (rejects compression ratio exceeding 100:1).
- **Stream Ingestion Limits:**
  - Maximum line length is capped (default: 8,192 chars) to prevent ReDoS (Regular Expression Denial of Service).
  - Maximum total line limits (default: 50,000 lines, configurable via `--max-lines`).

### 2. Secret Redaction Contract
- CIAUTOPSY applies best-effort heuristic redaction for common secrets (GitHub PATs, AWS Access Keys, Bearer tokens, Authorization headers, Basic auth credentials in URLs, Database URIs, and Private Key blocks) prior to rendering terminal output or exporting reports.
- **Limitation:** Pattern-based redaction cannot guarantee 100% removal of all custom, proprietary, or unconventional secrets. Users should always review generated reports before sharing them publicly.

### 3. Non-Execution Guarantee
- CIAUTOPSY parses build logs to diagnose failure causes.
- **CIAUTOPSY will NEVER execute shell commands, scripts, or network endpoints parsed from log contents.** Suggested remediation actions are printed as human-readable suggestions for the user to review and run manually.

### 4. Zero Telemetry & Air-Gapped Operation
- CIAUTOPSY performs zero background network transmission and collects zero telemetry.
- All log parsing, diffing, and report generation execute entirely locally on your machine.
