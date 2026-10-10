"""Command-Line Interface (CLI) for CIAUTOPSY."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure UTF-8 output encoding across all operating systems
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from ciautopsy import __version__
from ciautopsy.config import IngestionConfig
from ciautopsy.engine.analyzer import analyze_target
from ciautopsy.errors import ArchiveSecurityError, CiautopsyError, InputValidationError
from ciautopsy.reports import (
    format_console_report,
    format_json_report,
    format_markdown_report,
)
from ciautopsy.rules import RuleRegistry


def build_parser() -> argparse.ArgumentParser:
    """Constructs the command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="ciautopsy",
        description="CIAUTOPSY 🩺 - Evidence-based root-cause analysis for failed CI/CD pipelines.",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Command: version
    subparsers.add_parser("version", help="Print CIAUTOPSY version and exit")

    # Command: analyze
    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Analyze a CI/CD log file or ZIP archive to identify root causes and evidence",
    )
    analyze_parser.add_argument(
        "target", help="Path to the CI log file (.log, .txt) or archive (.zip) to analyze"
    )
    analyze_parser.add_argument(
        "-b",
        "--baseline",
        help="Optional path to a successful baseline CI log or archive for comparison",
    )
    analyze_parser.add_argument(
        "-f",
        "--format",
        choices=["console", "markdown", "json"],
        default="console",
        help="Report output format (default: console)",
    )
    analyze_parser.add_argument(
        "-o", "--output", help="Optional output file path to write report into"
    )
    analyze_parser.add_argument(
        "--max-lines",
        type=int,
        default=100_000,
        help="Maximum log lines to parse (default: 100,000)",
    )
    analyze_parser.add_argument(
        "--no-color", action="store_true", help="Disable colored console output"
    )

    # Command: rules
    subparsers.add_parser("rules", help="List all registered diagnostic rules")

    return parser


def _safe_write_output(content: str, output_path_str: str) -> None:
    """Safely writes report content to the designated output path."""
    out_path = Path(output_path_str).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)
        if not content.endswith("\n"):
            f.write("\n")
    print(f"Report written to: {out_path}")


def handle_analyze(args: argparse.Namespace) -> int:
    """
    Executes the analyze subcommand.
    Exit codes:
      0: Analysis completed successfully (regardless of whether original CI job failed)
      2: Input validation error or invalid arguments
      3: Internal processing error
    """
    try:
        config = IngestionConfig(max_lines=args.max_lines)
        report = analyze_target(
            target_path=args.target,
            baseline_path=args.baseline,
            config=config,
        )
    except (InputValidationError, ArchiveSecurityError, FileNotFoundError) as e:
        sys.stderr.write(f"Error: {e}\n")
        return 2
    except CiautopsyError as e:
        sys.stderr.write(f"CIAUTOPSY Error: {e}\n")
        return e.exit_code
    except Exception as e:
        sys.stderr.write(f"Unexpected internal error: {e}\n")
        return 3

    # Render report according to requested format
    if args.format == "markdown":
        output = format_markdown_report(report)
    elif args.format == "json":
        output = format_json_report(report)
    else:
        use_color = False if args.no_color else None
        output = format_console_report(report, use_color=use_color)

    if args.output:
        _safe_write_output(output, args.output)
    else:
        print(output)

    return 0


def handle_rules() -> int:
    """Lists registered diagnostic rules in a clean tabular view."""
    rules = RuleRegistry.get_all_rules()
    print("=====================================================================")
    print(f"  CIAUTOPSY Registered Diagnostic Rules ({len(rules)} total)")
    print("=====================================================================")
    for rule in sorted(rules, key=lambda r: r.rule_id):
        print(
            f"  [{rule.rule_id}] {rule.name:<42} | {rule.category.value:<25} | {rule.severity.value}"
        )
    print("=====================================================================")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Main CLI entrypoint."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    if args.command == "version":
        print(f"ciautopsy {__version__}")
        return 0
    elif args.command == "analyze":
        return handle_analyze(args)
    elif args.command == "rules":
        return handle_rules()

    return 0


if __name__ == "__main__":
    sys.exit(main())
