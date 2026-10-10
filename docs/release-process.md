# Release Process & Distribution

This guide details how CIAUTOPSY versions are prepared, validated, and distributed.

---

## 1. Versioning Policy

CIAUTOPSY adheres to [Semantic Versioning 2.0.0](https://semver.org/):
- **Major (X.0.0):** Breaking CLI interface changes or JSON report schema overhauls.
- **Minor (0.X.0):** New diagnostic rules, new CI format support, or feature additions.
- **Patch (0.0.X):** Bug fixes, rule accuracy refinements, or security patches.

---

## 2. Release Checklist

Before creating a new release:

1. **Run Local Validation Suite:**
   ```bash
   # 1. Run unit, integration, and security tests
   pytest --cov=ciautopsy
   
   # 2. Check code style and formatting
   ruff check .
   ruff format --check .
   
   # 3. Static type analysis
   mypy src/ciautopsy
   
   # 4. Run synthetic benchmark
   python scripts/run_benchmark.py
   
   # 5. Validate examples & report generation
   python scripts/validate_examples.py
   ```

2. **Update Version & Changelog:**
   - Update `version = "x.y.z"` in `pyproject.toml`.
   - Update `schema_version` in `src/ciautopsy/models.py` if JSON schema changed.
   - Add release notes in `CHANGELOG.md` under `## [x.y.z] - YYYY-MM-DD`.

3. **Validate Package Build & Twine Metadata:**
   ```bash
   python -m build
   python -m twine check dist/*
   ```

4. **Verify Clean Installation:**
   ```bash
   python -m venv /tmp/test-env
   /tmp/test-env/bin/pip install dist/*.whl
   /tmp/test-env/bin/ciautopsy version
   /tmp/test-env/bin/ciautopsy rules
   ```

---

## 3. PyPI Trusted Publishing (OIDC)

Releases are published automatically via GitHub Actions `.github/workflows/release.yml` using **PyPI Trusted Publishing (OIDC)**:
1. Tag the release commit:
   ```bash
   git tag -a v0.1.0 -m "Release v0.1.0"
   git push origin v0.1.0
   ```
2. The GitHub Actions release workflow triggers, builds the artifacts, verifies the distribution, publishes to PyPI using PyPI's OpenID Connect token, and creates a GitHub Release with attached `.whl` and `.tar.gz` files.
