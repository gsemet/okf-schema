"""Tests for package-level functionality."""

import okf_schema


def test_version() -> None:
    """okf_schema exports a __version__ string."""
    assert isinstance(okf_schema.__version__, str)
    assert len(okf_schema.__version__) > 0
