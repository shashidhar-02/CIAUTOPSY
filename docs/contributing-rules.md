# Contributing Diagnostic Rules

We encourage community contributions of diagnostic rules to expand CIAUTOPSY's failure catalog across languages, runtimes, and build tools.

---

## 1. Anatomy of a Rule

Every diagnostic rule extends `BaseRule` (in `src/ciautopsy/rules/base.py`) and defines:

```python
from __future__ import annotations
import re
from typing import Optional, List
from ciautopsy.rules.base import BaseRule
from ciautopsy.models import Finding, Evidence, Severity, Confidence


class MyToolFailureRule(BaseRule):
    rule_id = "TOOL-001"
    name = "MyTool Compilation Failure"
    category = "Build"
    severity = Severity.HIGH
    keywords = ["mytool", "compile error"]  # Fast substring pre-filter

    _PATTERN = re.compile(r"mytool:\s+fatal\s+error:\s+(.+)", re.IGNORECASE)

    def evaluate(
        self, line: str, line_number: int, step_name: Optional[str] = None
    ) -> Optional[Finding]:
        match = self._PATTERN.search(line)
        if not match:
            return None

        detail = match.group(1).strip()
        evidence = Evidence(
            line_number=line_number,
            text=line.strip(),
            step_name=step_name,
        )
        return Finding(
            rule_id=self.rule_id,
            rule_name=self.name,
            category=self.category,
            severity=self.severity,
            title=f"MyTool error: {detail}",
            description="MyTool encountered an unrecoverable compilation error.",
            confidence=Confidence.HIGH,
            confidence_factors=["Exact fatal error regex matched"],
            evidence=[evidence],
            suggested_actions=["Review the compiler error output"],
            is_cascade=False,
        )
```

---

## 2. Rule Design Guidelines

1. **Fast Keyword Pre-Filter:** Always supply `keywords = [...]`. Lines that do not contain any of the listed substrings bypass regex compilation completely, keeping throughput near 100,000 lines/sec.
2. **Anchor & Bound Expressions:** Avoid catastrophic backtracking. Use non-capturing groups `(?:...)` and avoid nested unconstrained quantifiers `(.*)*`.
3. **Cascading Symptom Flagging:** If the rule matches generic secondary exits (e.g. `exit status 1` or `npm ERR!`), mark `is_cascade=True` and set `severity=Severity.LOW` so the engine prioritizes the real root cause.
4. **Register the Rule:** Register your new rule class in `src/ciautopsy/rules/__init__.py`.

---

## 3. Required Tests

Every new rule must have:
- Unit test in `tests/test_more_rules.py` verifying that typical failure lines trigger the rule.
- Negative test ensuring benign lines containing similar words do not falsely trigger.
- Verification that original 1-indexed line numbers are preserved.
