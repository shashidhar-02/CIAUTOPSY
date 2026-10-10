# Getting Support for CIAUTOPSY

Welcome to the CIAUTOPSY community! Here is how to get help, ask questions, or report issues.

## Where to Get Help

- **Documentation:** Browse the [`docs/`](docs/) directory for architecture guides, rule catalog, configuration, and troubleshooting tips.
- **GitHub Discussions:** If enabled on the repository, use GitHub Discussions to ask usage questions, share pipeline patterns, or propose feature ideas.
- **GitHub Issues:** Use GitHub Issues for bug reports and feature requests. Please follow our issue templates.

---

## Reporting a Problem

Before opening an issue:
1. Verify you are running the latest version: `ciautopsy version`.
2. Check existing open and closed issues to see if the topic has been discussed.
3. Test if the issue reproduces on a minimal sanitized log.

### Sanitization Guideline
When sharing CI logs:
- **Never paste production credentials, private tokens, internal domain names, or private keys.**
- CIAUTOPSY applies automated redaction, but you should manually verify that all proprietary or sensitive information is stripped before submitting a public report.
- Provide a minimal reproduction: 10–20 lines demonstrating the failure is much easier to diagnose and test than a 50,000-line raw log.

---

## Contributing Fixes and Rules

Want to add diagnostic rules for your favorite build tool or framework? Check out [CONTRIBUTING.md](CONTRIBUTING.md) and [docs/contributing-rules.md](docs/contributing-rules.md).
