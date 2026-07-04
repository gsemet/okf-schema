"""Tests for okf_schema.kb.patterns — INIT_PATTERNS registry."""

from __future__ import annotations

from pathlib import Path

import pytest


def test_init_patterns_is_dict() -> None:
    """INIT_PATTERNS must be a dict mapping str to callable."""
    from okf_schema.kb.patterns import INIT_PATTERNS

    assert isinstance(INIT_PATTERNS, dict)


def test_init_patterns_contains_kb() -> None:
    """The 'kb' key must be present and callable after module import."""
    from okf_schema.kb.patterns import INIT_PATTERNS

    assert "kb" in INIT_PATTERNS
    assert callable(INIT_PATTERNS["kb"])


def test_register_pattern_adds_to_registry() -> None:
    """register_pattern must add a new entry to INIT_PATTERNS."""
    from okf_schema.kb.patterns import INIT_PATTERNS, register_pattern

    def dummy(path: Path, force: bool) -> None:  # noqa: ARG001
        pass

    name = "_test_register_add"
    # Clean up any leftover from previous runs
    INIT_PATTERNS.pop(name, None)

    register_pattern(name, dummy)
    assert name in INIT_PATTERNS
    assert INIT_PATTERNS[name] is dummy

    # Cleanup
    INIT_PATTERNS.pop(name)


def test_register_duplicate_raises_valueerror() -> None:
    """Registering a name twice must raise ValueError."""
    from okf_schema.kb.patterns import INIT_PATTERNS, register_pattern

    def dummy(path: Path, force: bool) -> None:  # noqa: ARG001
        pass

    name = "_test_register_dup"
    INIT_PATTERNS.pop(name, None)

    register_pattern(name, dummy)
    with pytest.raises(ValueError, match=f"Pattern '{name}' is already registered."):
        register_pattern(name, dummy)

    # Cleanup
    INIT_PATTERNS.pop(name)


def test_list_patterns_returns_sorted_names() -> None:
    """list_patterns must return a sorted list of all registered pattern names."""
    from okf_schema.kb.patterns import INIT_PATTERNS, list_patterns, register_pattern

    def dummy(path: Path, force: bool) -> None:  # noqa: ARG001
        pass

    names_added = ["_zzz", "_aaa"]
    for n in names_added:
        INIT_PATTERNS.pop(n, None)
        register_pattern(n, dummy)

    result = list_patterns()
    assert result == sorted(result)
    for n in names_added:
        assert n in result

    # Cleanup
    for n in names_added:
        INIT_PATTERNS.pop(n)
