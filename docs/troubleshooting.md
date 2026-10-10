# Troubleshooting & FAQ

---

## 1. Exit Codes

CIAUTOPSY adheres to an explicit exit code contract:

| Exit Code | Meaning | What to Check |
|-----------|---------|---------------|
| `0` | Success | Analysis finished normally. (Note: Even if the analyzed log failed, CIAUTOPSY exits 0 because analysis succeeded.) |
| `2` | Bad Arguments / Input Error | Check file path existence, file permissions, or archive bounds. |
| `3` | Internal Processing Error | An unexpected parsing or analysis exception occurred. |

---

## 2. Common Issues

### "Target log file not found" (Exit Code 2)
Ensure the relative or absolute path is correct:
```bash
ciautopsy analyze ./build.log
```

### "Input file exceeds maximum allowed size" or "Archive member count exceeded"
If your archive contains hundreds of log files or exceeds 50 MB:
- Use plain text log files instead of full archives, or
- Unpack only the failed step's log file before passing to `ciautopsy`.

### "No diagnostic failure patterns detected"
If CIAUTOPSY reports no failure cause:
1. Verify the log is actually from a failed run (check exit codes at the end).
2. The failure might be an unmodeled error category. Check [docs/contributing-rules.md](contributing-rules.md) to add a diagnostic rule.
3. Check if the error occurred beyond the ingestion limit (default: 50,000 lines). Increase with `--max-lines 100000`.

### Unicode / Terminal Output Warnings on Windows
On Windows systems using legacy code pages (`cp1252`), emojis or box-drawing characters may fail to render in older cmd.exe prompts. CIAUTOPSY automatically uses UTF-8 console streams and falls back to plain ASCII text if rich console rendering is unsupported.
