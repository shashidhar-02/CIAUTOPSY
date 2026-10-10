# Synthetic Benchmark Methodology & Metrics

To ensure diagnostic accuracy and avoid regression, CIAUTOPSY is tested continuously against a curated synthetic benchmark corpus.

---

## 1. Corpus Design (`tests/benchmark/corpus/`)

The benchmark suite consists of 11 realistic test logs covering distinct scenarios:

1. **Positive Failure Cases (9 cases):**
   - Python missing dependency (`DEP-001`)
   - Docker container OOM killed (`OOM-001`)
   - npm `ERESOLVE` dependency conflict (`DEP-003`)
   - GitHub Actions workflow execution timeout (`TIM-001`)
   - Disk space exhausted (`DSK-001`)
   - Authentication failure / 401 Unauthorized (`SEC-001`)
   - Missing required environment variable (`SEC-002`)
   - Pytest assertion failure (`TST-001`)
   - DNS resolution failure / network timeout (`NET-001`)
2. **Negative Control (1 case):**
   - Clean, successful CI log with informational notices and warnings. Verifies that the tool produces **0 false positives** on healthy builds.
3. **Ambiguous / Unmodeled Case (1 case):**
   - Truncated or unmodeled failure. Verifies that the tool safely reports **unknown** rather than inventing a false diagnosis.

---

## 2. Benchmark Metrics & Formulas

- **Top-1 Root Cause Accuracy:** Percentage of failure logs where the primary diagnosed cause matches ground truth.
  $$\text{Top-1 Accuracy} = \frac{\text{Correct Top-1 Diagnoses}}{\text{Total Positive Cases}} \times 100\%$$
- **Top-3 Candidate Recall:** Percentage of failure logs where the true cause appears in the top 3 candidate hypotheses.
- **Exact Evidence Line Accuracy:** Percentage of cases where the identified primary evidence cites the exact 1-indexed ground-truth line.
- **Negative Control False-Positive Rate:** Percentage of clean successful logs mistakenly diagnosed with an error.
- **Unknown Handling Accuracy:** Correct identification of unmodeled/truncated logs without false positive claims.
- **Latency & Peak Memory:** Execution runtime per log and peak memory allocation measured via `tracemalloc`.

---

## 3. Running the Benchmark

You can reproduce the benchmark results at any time:

```bash
python scripts/run_benchmark.py
```

### Measured Benchmark Output (v0.1.0)
- **Top-1 Root Cause Accuracy:** 100.0% (9/9)
- **Top-3 Candidate Cause Recall:** 100.0% (9/9)
- **Exact Evidence Line Accuracy:** 100.0% (9/9)
- **Negative Control FP Rate:** 0.0% (0/1)
- **Unknown Case Handling Accuracy:** 100.0% (1/1)
- **Average Latency:** ~0.48 ms per log
- **Peak Memory:** ~136.6 KB
