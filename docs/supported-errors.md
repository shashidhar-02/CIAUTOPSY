# Supported Error Categories & Diagnostic Rules

CIAUTOPSY v0.1.0 includes a modular rule catalog spanning 7 core categories. Each rule defines a stable ID, category, detection pattern, confidence calculation, and suggested remediation.

---

## Rule Catalog

| Rule ID | Name | Category | Severity | Typical Trigger Signature |
|---------|------|----------|----------|---------------------------|
| `DEP-001` | Missing Python Module | Dependencies | `HIGH` | `ModuleNotFoundError: No module named '...'` / `ImportError` |
| `DEP-002` | Pip Conflict | Dependencies | `HIGH` | `ResolutionImpossible: for ...` / `conflicting dependencies` |
| `DEP-003` | Npm Dependency Conflict | Dependencies | `HIGH` | `npm ERR! code ERESOLVE` / `Could not resolve dependency` |
| `DEP-004` | Node Module Not Found | Dependencies | `HIGH` | `Cannot find module '...'` / `code: 'MODULE_NOT_FOUND'` |
| `OOM-001` | Out of Memory / OOM | Infrastructure | `CRITICAL` | `Out of memory: Kill process` / `OOMKilled` / exit code 137 |
| `TIM-001` | Execution Timeout | Infrastructure | `CRITICAL` | `The job running on runner ... has exceeded the maximum execution time` |
| `DSK-001` | Disk Space Exhausted | Infrastructure | `CRITICAL` | `No space left on device` / `ENOSPC: no space left` |
| `DOK-001` | Docker Socket Permission | Infrastructure | `HIGH` | `Got permission denied while trying to connect to the Docker daemon socket` |
| `CMD-001` | Command Not Found | Build | `HIGH` | `command not found` / `is not recognized as an internal or external command` (exit 127) |
| `BLD-001` | Compilation Failure | Build | `HIGH` | `fatal error: ...: No such file or directory` / `error: linker ... failed` |
| `SYN-001` | Syntax Error | Build | `HIGH` | `SyntaxError: invalid syntax` / `IndentationError` |
| `CAS-001` | Cascading Process Exit | Build | `LOW` | `Process completed with exit code 1` / `exit status 1` |
| `TST-001` | Pytest Assertion Failure | Testing | `HIGH` | `FAILED tests/...` / `AssertionError` |
| `TST-002` | Jest Test Failure | Testing | `HIGH` | `FAIL src/...` / `Jest: "global" coverage threshold not met` |
| `SEC-001` | Unauthorized / Auth Failure | Secrets | `CRITICAL` | `HTTP 401 Unauthorized` / `HTTP 403 Forbidden` / `Authentication failed` |
| `SEC-002` | Missing Env / Secret | Secrets | `HIGH` | `KeyError: '...'` / `Missing required environment variable` |
| `NET-001` | Network Timeout / DNS | Network | `HIGH` | `Could not resolve host` / `Connection refused` / `ETIMEDOUT` |

---

## Cascading Exit Code Handling (`CAS-001`)

Many CI runners log lines like `Process completed with exit code 1` or `npm ERR! command failed`.
- In naive regex searchers, these lines are often erroneously picked as the root cause.
- In CIAUTOPSY, `CAS-001` carries low priority and is marked as a cascading symptom. When a primary error (e.g. `DEP-001` or `SYN-001`) is present, `CAS-001` is automatically suppressed as a root cause and grouped under the primary failure's evidence list.

---

## Viewing Rules via CLI

You can inspect the active catalog directly in your terminal:

```bash
ciautopsy rules
```
