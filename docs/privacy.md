# Privacy & Secret Redaction

CIAUTOPSY enforces a **local-first, privacy-by-default** contract.

---

## 1. Local Processing Guarantee

- **Zero Cloud Transmission:** CIAUTOPSY does not send logs, code snippets, or error messages to any external API, cloud service, or telemetry collector.
- **Air-Gapped Ready:** The core engine requires no internet connectivity and operates in air-gapped corporate and defense networks.

---

## 2. Automated Secret Redaction (`ciautopsy.security.redaction`)

Logs frequently capture sensitive tokens when builds fail during deployment, docker login, or dependency fetching. CIAUTOPSY applies automated heuristic pattern matching to mask sensitive credentials before they are printed to the terminal or saved to reports.

### Redacted Patterns

- **GitHub Personal Access Tokens:** `ghp_[A-Za-z0-9_]{36,}`
- **AWS Access Key IDs:** `AKIA[0-9A-Z]{16}`
- **Bearer & Authorization Tokens:** `Authorization:\s*Bearer\s+[A-Za-z0-9_\-\.]+`
- **Password Assignments:** `(?i)(?:password|secret|passwd|token)\s*=\s*['"]?[^\s'"]+`
- **Embedded Basic Auth in URLs:** `https?://[a-zA-Z0-9_\-\.]+:[^@\s]+@`
- **Database Connection URIs:** `(?:postgres|mysql|mongodb)://[^:]+:[^@]+@`
- **Private Key Blocks:** `-----BEGIN [A-Z\s]+ PRIVATE KEY-----` through `-----END [A-Z\s]+ PRIVATE KEY-----`

---

## 3. Redaction Caveat & Responsibility Notice

> [!WARNING]
> While CIAUTOPSY applies best-effort automated pattern matching, heuristic regex filtering cannot guarantee that every proprietary, non-standard, or unusual secret token will be caught.
>
> **Always inspect generated Markdown and JSON reports before attaching them to public GitHub issues or sharing them externally.**
