# CIAUTOPSY Security Architecture

CIAUTOPSY is engineered with a strict **secure-by-default** posture designed to safely analyze potentially hostile or compromised CI/CD build logs.

---

## 1. Threat Model & Ingestion Sandbox

When analyzing build logs from public pull requests or complex CI environments, input files may contain:
- Unchecked ZIP archives submitted as run artifacts.
- Pathological line lengths crafted to trigger catastrophic regex backtracking (ReDoS).
- Embedded shell injection commands formatted to resemble build output.
- Accidental secrets emitted by failing steps.

---

## 2. ZIP Archive Defenses (`ciautopsy.ingest.archive`)

When processing ZIP archives (such as downloaded GitHub Actions run archives), CIAUTOPSY enforces:

1. **Path Traversal Protection:**
   - Members containing directory traversal sequences (`..`), leading slashes (`/` or `\`), or Windows drive letters (`C:`) are immediately rejected with an `ArchiveSecurityError`.
2. **Zip-Bomb & Memory Exhaustion Defenses:**
   - **Member Count Limit:** Maximum 200 files in an archive (configurable).
   - **Compressed Size Limit:** Maximum 50 MB archive file size.
   - **Uncompressed Member Size Limit:** Maximum 100 MB per uncompressed entry.
   - **Compression Ratio Cap:** Rejects any member with a compression ratio exceeding 100:1 to prevent decompression bombs.
3. **No Unsafe Disk Extraction:**
   - Archives are read via in-memory streaming without writing untrusted file paths to host storage.

---

## 3. Regular Expression Denial of Service (ReDoS) Defenses

- All incoming lines are truncated to a maximum of 8,192 characters (`normalizer.py`) before regex evaluation.
- Diagnostic rules use linear-time, anchored expressions and fast substring pre-filters (`can_match(line)`) before invoking compiled regular expressions.

---

## 4. Non-Execution Guarantee

- CIAUTOPSY will **NEVER execute shell commands, scripts, or network endpoints parsed from log contents.**
- Suggested commands in reports are strictly human-readable recommendations formatted for developer review.

---

## 5. Offline Operation

- CIAUTOPSY operates completely offline.
- No network requests, API keys, or background telemetry are used during log analysis or reporting.
