# JSON Report Schema (`v0.1.0`)

When CIAUTOPSY runs with `--format json`, it generates structured, machine-readable JSON suitable for ingestion by automated dashboards, triage bots, or internal monitoring tools.

---

## 1. Top-Level Schema (`AnalysisReport`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "CIAUTOPSY Analysis Report",
  "schema_version": "0.1.0",
  "type": "object",
  "required": [
    "schema_version",
    "target_file",
    "lines_analyzed",
    "findings",
    "cascading_findings"
  ],
  "properties": {
    "schema_version": { "type": "string", "const": "0.1.0" },
    "target_file": { "type": "string" },
    "platform": { "type": "string" },
    "total_lines": { "type": "integer" },
    "lines_analyzed": { "type": "integer" },
    "leading_cause": { "$ref": "#/$defs/Finding" },
    "findings": {
      "type": "array",
      "items": { "$ref": "#/$defs/Finding" }
    },
    "cascading_findings": {
      "type": "array",
      "items": { "$ref": "#/$defs/Finding" }
    },
    "diff_with_baseline": { "$ref": "#/$defs/DiffReport" },
    "missing_evidence": {
      "type": "array",
      "items": { "type": "string" }
    },
    "limitations": {
      "type": "array",
      "items": { "type": "string" }
    }
  }
}
```

---

## 2. Definitions

### `Finding` Object

Represents a diagnosed failure hypothesis:

```json
{
  "rule_id": "DEP-001",
  "rule_name": "Missing Python Module",
  "category": "Dependencies",
  "severity": "HIGH",
  "title": "Missing Python dependency: jwt",
  "description": "Python failed to import module 'jwt' (ModuleNotFoundError).",
  "confidence": "HIGH",
  "confidence_factors": [
    "Exact ModuleNotFoundError signature matched",
    "Missing package explicitly named in traceback",
    "Correlated with step 'Run tests'"
  ],
  "evidence": [
    {
      "line_number": 9,
      "text": "ModuleNotFoundError: No module named 'jwt'",
      "step_name": "Run tests",
      "is_redacted": false
    }
  ],
  "suggested_actions": [
    "Check your pyproject.toml, setup.py, or requirements.txt for 'jwt'",
    "Add 'jwt' or 'PyJWT' to your dependency manifest"
  ],
  "is_cascade": false
}
```

### `DiffReport` Object

Represents baseline comparison results when `--baseline` is specified:

```json
{
  "baseline_file": "success_run.log",
  "new_findings": [ ... ],
  "resolved_findings": [ ... ],
  "step_drifts": [
    {
      "step_name": "Run tests",
      "baseline_status": "passed",
      "failed_status": "failed",
      "explanation": "Step succeeded in baseline but encountered 2 error lines in target log"
    }
  ],
  "summary": "1 new root causes detected compared to baseline."
}
```
