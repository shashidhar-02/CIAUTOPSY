## Summary

<!-- Briefly describe the purpose of this change and the problem it solves. -->

## Changes Proposed

- [ ] New diagnostic rule or rule improvement (rule ID: `...`)
- [ ] Ingestion, parsing, or redaction enhancement
- [ ] Baseline comparison or reporting update
- [ ] Performance, reliability, or benchmark update
- [ ] Documentation, governance, or test improvements

## Evidence & Verification

<!-- List the exact commands executed and their output to verify this change. -->
- `pytest -v` (Pass / Fail counts):
- `ruff check .` and `ruff format --check .`:
- `mypy src/ciautopsy`:
- Benchmark run (`python scripts/run_benchmark.py`):

## Security & Privacy Considerations

- [ ] Does this change handle untrusted input safely (bounds, path traversal)?
- [ ] Are logs/evidence redacted before serialization or display?
- [ ] Does this change avoid making unauthorized network calls or executing shell commands?

## Checklist

- [ ] Tests added or updated for all new logic (positive & negative cases)
- [ ] Documentation updated in `docs/` or `README.md`
- [ ] `CHANGELOG.md` updated if this is a user-facing change
