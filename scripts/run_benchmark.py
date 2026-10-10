"""Benchmark evaluation runner measuring diagnostic accuracy, recall, and resource performance."""

from __future__ import annotations

import json
import sys
import time
import tracemalloc
from pathlib import Path

from ciautopsy.engine.analyzer import analyze_log

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BENCHMARK_DIR = Path(__file__).resolve().parent.parent / "tests" / "benchmark"
GROUND_TRUTH_PATH = BENCHMARK_DIR / "ground_truth.json"
CORPUS_DIR = BENCHMARK_DIR / "corpus"


def run_benchmark() -> dict[str, float | int | str]:
    """Runs the synthetic benchmark suite and measures honest empirical performance."""
    if not GROUND_TRUTH_PATH.exists():
        sys.stderr.write(f"Ground truth not found: {GROUND_TRUTH_PATH}\n")
        sys.exit(1)

    with open(GROUND_TRUTH_PATH, encoding="utf-8") as f:
        cases = json.load(f)

    total_cases = len(cases)
    positive_cases = 0
    negative_cases = 0
    unknown_cases = 0

    top1_correct = 0
    top3_correct = 0
    exact_line_correct = 0
    false_positives = 0
    unknown_handled_correctly = 0

    tracemalloc.start()
    start_time = time.perf_counter()

    print("================================================================================")
    print("  [CIAUTOPSY] SYNTHETIC DIAGNOSTIC BENCHMARK")
    print("================================================================================")
    print(f"Loaded {total_cases} test cases from {GROUND_TRUTH_PATH.name}\n")

    for case in cases:
        case_id = case["id"]
        filename = case["filename"]
        expected_rule = case["expected_rule"]
        expected_line = case["expected_line"]
        category = case["category"]
        log_path = str(CORPUS_DIR / filename)

        report = analyze_log(log_path)
        leading = report.leading_root_cause
        all_candidate_ids = [f.rule_id for f in report.findings]

        if category == "NegativeControl":
            negative_cases += 1
            if leading is None:
                print(
                    f"  [PASS] {case_id} ({filename}): Correctly classified negative control (no findings)"
                )
            else:
                false_positives += 1
                print(f"  [FAIL] {case_id} ({filename}): False positive! Flagged {leading.rule_id}")
            continue

        if category == "UnknownFailure":
            unknown_cases += 1
            if leading is None:
                unknown_handled_correctly += 1
                print(
                    f"  [PASS] {case_id} ({filename}): Correctly identified unknown/unmodeled failure"
                )
            else:
                print(
                    f"  [WARN] {case_id} ({filename}): Overfitted unknown failure with {leading.rule_id}"
                )
            continue

        # Positive diagnostic case
        positive_cases += 1
        is_top1 = leading is not None and leading.rule_id == expected_rule
        is_top3 = expected_rule in all_candidate_ids[:3]

        actual_line = leading.evidence[0].line_number if leading and leading.evidence else None
        is_line_match = actual_line == expected_line

        if is_top1:
            top1_correct += 1
        if is_top3:
            top3_correct += 1
        if is_line_match:
            exact_line_correct += 1

        status = "PASS" if is_top1 and is_line_match else "PARTIAL" if is_top1 else "FAIL"
        actual_rule_str = leading.rule_id if leading else "None"
        print(
            f"  [{status:<7}] {case_id} ({filename:<32}): "
            f"Expected {expected_rule} (L{expected_line}), Got {actual_rule_str} (L{actual_line})"
        )

    duration_ms = (time.perf_counter() - start_time) * 1000
    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    top1_accuracy = (top1_correct / positive_cases) * 100 if positive_cases else 0.0
    top3_recall = (top3_correct / positive_cases) * 100 if positive_cases else 0.0
    line_accuracy = (exact_line_correct / positive_cases) * 100 if positive_cases else 0.0
    fp_rate = (false_positives / negative_cases) * 100 if negative_cases else 0.0
    unknown_accuracy = (unknown_handled_correctly / unknown_cases) * 100 if unknown_cases else 0.0

    results = {
        "total_cases": total_cases,
        "positive_cases": positive_cases,
        "top1_accuracy_pct": round(top1_accuracy, 1),
        "top3_recall_pct": round(top3_recall, 1),
        "evidence_line_accuracy_pct": round(line_accuracy, 1),
        "false_positive_rate_pct": round(fp_rate, 1),
        "unknown_handling_accuracy_pct": round(unknown_accuracy, 1),
        "total_runtime_ms": round(duration_ms, 2),
        "avg_latency_per_log_ms": round(duration_ms / total_cases, 2),
        "peak_memory_kb": round(peak_mem / 1024, 1),
    }

    print("\n--------------------------------------------------------------------------------")
    print("  MEASURED BENCHMARK RESULTS")
    print("--------------------------------------------------------------------------------")
    print(
        f"  Top-1 Root Cause Accuracy:        {results['top1_accuracy_pct']}% ({top1_correct}/{positive_cases})"
    )
    print(
        f"  Top-3 Candidate Cause Recall:     {results['top3_recall_pct']}% ({top3_correct}/{positive_cases})"
    )
    print(
        f"  Exact Evidence Line Accuracy:     {results['evidence_line_accuracy_pct']}% ({exact_line_correct}/{positive_cases})"
    )
    print(
        f"  Negative Control FP Rate:         {results['false_positive_rate_pct']}% ({false_positives}/{negative_cases})"
    )
    print(
        f"  Unknown Case Handling Accuracy:   {results['unknown_handling_accuracy_pct']}% ({unknown_handled_correctly}/{unknown_cases})"
    )
    print(f"  Total Suite Runtime:              {results['total_runtime_ms']} ms")
    print(f"  Average Latency Per Log:          {results['avg_latency_per_log_ms']} ms")
    print(f"  Peak Memory Consumption:          {results['peak_memory_kb']} KB")
    print("================================================================================\n")

    output_results_path = BENCHMARK_DIR / "benchmark_results.json"
    with open(output_results_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    return results


if __name__ == "__main__":
    run_benchmark()
