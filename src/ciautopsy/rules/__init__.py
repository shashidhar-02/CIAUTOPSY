"""Rules package importing all diagnostic rule modules into the registry."""

# Import all modules so @register_rule executes
from ciautopsy.rules import (  # noqa: F401
    builds,
    dependencies,
    infrastructure,
    network,
    secrets,
    testing,
)
from ciautopsy.rules.base import DiagnosticRule, RuleRegistry, register_rule

__all__ = [
    "DiagnosticRule",
    "RuleRegistry",
    "register_rule",
]
