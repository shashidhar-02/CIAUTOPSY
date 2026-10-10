# Contributing to CIAUTOPSY 🩺

Thank you for your interest in contributing to **CIAUTOPSY**! Our mission is to make investigating failed CI/CD pipelines instant, evidence-backed, and private.

---

## 🧭 Code of Conduct

We are committed to providing a welcoming, inclusive, and harassment-free environment for everyone. Please treat all contributors with respect and kindness.

---

## 🛠️ Development Setup

CIAUTOPSY requires **Python 3.10+**.

### 1. Clone the repository
```bash
git clone https://github.com/shashidhar-02/CIAUTOPSY.git
cd CIAUTOPSY
```

### 2. Set up a virtual environment
```bash
# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate

# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install in editable mode with development dependencies
```bash
pip install --upgrade pip
pip install -e ".[dev]"
```

---

## 🧩 Adding a Diagnostic Rule

One of the best ways to contribute is by adding new diagnostic rules for CI/CD failures. A rule should:
1. **Target a concrete failure mode** (e.g., Python `ModuleNotFoundError`, Docker `OOMKilled`, npm `ERESOLVE`, Go build errors, GitHub Actions step timeouts).
2. **Extract verifiable evidence** (exact line numbers and relevant context snippets, rather than speculation).
3. **Provide actionable remediation advice** (how a developer can fix the issue).
4. **Include a fixture test** with an anonymized CI log reproducing the failure.

### Anonymizing CI Logs
Before committing any sample CI logs or test fixtures:
- ⚠️ **Remove all sensitive credentials**, tokens, secret environment variables, and internal hostnames/IPs.
- Replace sensitive organization names or private repository paths with generic placeholders (e.g., `org/repo`).

---

## 🧪 Running Tests & Quality Checks

Ensure all checks pass before opening a Pull Request:

```bash
# Run test suite with pytest
pytest

# Run tests with coverage
pytest --cov=ciautopsy --cov-report=term-missing

# Lint and format checks
ruff check .
ruff format --check .

# Type checking
mypy src/ciautopsy

# Run synthetic diagnostic benchmark
python scripts/run_benchmark.py
```

---

## 📬 Pull Request Guidelines

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/my-new-diagnostic-rule
   ```
2. **Write clear commit messages** following the [Conventional Commits](https://www.conventionalcommits.org/) convention:
   - `feat: add docker oom diagnostic rule`
   - `fix: resolve ansi escape sequence stripping issue`
   - `docs: update cli usage examples`
   - `test: add github actions fixture for npm timeout`
3. **Include tests:** Every new rule or bugfix must be accompanied by relevant test fixtures and unit tests.
4. **Push and open a PR** against the `main` branch with a clear description of the problem and proposed solution.

---

## 💡 Reporting Issues

- **Bug Reports:** If CIAUTOPSY misidentified a root cause or produced false positives, please open an issue including the sanitized log snippet, expected diagnosis, and actual output.
- **Feature Requests:** Suggest new CI platforms, ecosystem rules, or CLI export formats in GitHub Issues.
