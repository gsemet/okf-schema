"""Extensible registry of KB initialisation patterns.

Patterns are callables with the signature ``(path: Path, force: bool) -> None``.
New patterns are registered at import time by calling :func:`register_pattern`.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

#: Maps pattern name → scaffold callable ``(path, force) -> None``.
INIT_PATTERNS: dict[str, Callable[[Path, bool], None]] = {}


def register_pattern(name: str, fn: Callable[[Path, bool], None]) -> None:
    """Register an init pattern.

    Args:
        name: Pattern identifier (e.g., ``"kb"``).
        fn: Callable that accepts ``(path, force)`` and performs the scaffold.

    Raises:
        ValueError: If *name* is already registered.
    """
    if name in INIT_PATTERNS:
        raise ValueError(f"Pattern '{name}' is already registered.")
    INIT_PATTERNS[name] = fn


def list_patterns() -> list[str]:
    """Return a sorted list of registered pattern names.

    Returns:
        Alphabetically sorted list of all registered pattern identifiers.
    """
    return sorted(INIT_PATTERNS.keys())


# ---------------------------------------------------------------------------
# Built-in patterns — registered at import time
# ---------------------------------------------------------------------------

from okf_schema.kb.scaffold import scaffold_kb  # noqa: E402  (circular-safe)

register_pattern("kb", scaffold_kb)
