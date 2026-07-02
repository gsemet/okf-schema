"""Frontmatter formatter for OKF bundles."""

from __future__ import annotations

import difflib
import io
from dataclasses import dataclass
from pathlib import Path

from okf_schema._internal.utils import collect_markdown_files
from okf_schema._internal.yaml import extract_frontmatter, make_yaml


@dataclass
class FormattedResult:
    """Result of formatting a single file."""

    path: Path
    changed: bool
    diff: str | None = None


def flatten_value(value: object) -> object:
    """Recursively flatten nested lists; pass through scalars and dicts.

    Args:
        value: Any Python value (scalar, dict, or list).

    Returns:
        The same value with all nested lists flattened into a single
        one-dimensional list. Dicts inside lists are preserved.
    """
    if isinstance(value, list):
        flat: list[object] = []
        for item in value:
            flattened = flatten_value(item)
            if isinstance(flattened, list):
                flat.extend(flattened)
            else:
                flat.append(flattened)
        return flat
    return value


def format_frontmatter(text: str) -> str | None:
    """Extract frontmatter, flatten nested lists, and re-serialize.

    Uses ``ruamel.yaml`` round-trip mode so that comments and quotes
    are preserved wherever possible.

    Args:
        text: Full markdown file content.

    Returns:
        The full text with flattened frontmatter, or ``None`` when no
        frontmatter block is present.
    """
    fm_text, body = extract_frontmatter(text)
    if fm_text is None:
        return None

    y = make_yaml()
    data = y.load(fm_text)
    if data is None or not isinstance(data, dict):
        return text

    changed = False
    for key in list(data.keys()):
        value = data[key]
        if isinstance(value, list):
            flat = flatten_value(value)
            if flat != value:
                data[key] = flat
                changed = True

    if not changed:
        return text

    buf = io.StringIO()
    y.dump(data, buf)
    new_fm = buf.getvalue().rstrip("\n")
    return f"---\n{new_fm}\n---\n{body}"


def _fix_whitespace(text: str) -> str:
    """Strip trailing whitespace and ensure exactly one final newline."""
    lines = [line.rstrip() for line in text.splitlines()]
    return "\n".join(lines) + "\n"


def lint_frontmatter(text: str) -> str | None:
    """Extract frontmatter, flatten nested lists, and convert to inline.

    Uses ``ruamel.yaml`` round-trip mode so that comments and quotes
    are preserved wherever possible.  This keeps frontmatter compact,
    which is important for coding agents that load only the first *n*
    lines of a file.

    Args:
        text: Full markdown file content.

    Returns:
        The full text with flattened and inline lists, or ``None`` when
        no frontmatter block is present.
    """
    fm_text, body = extract_frontmatter(text)
    if fm_text is None:
        return None

    y = make_yaml()
    data = y.load(fm_text)
    if data is None or not isinstance(data, dict):
        return text

    changed = False
    for key in list(data.keys()):
        value = data[key]
        if isinstance(value, list):
            flat = flatten_value(value)
            if flat != value:
                data[key] = flat
                changed = True
        if hasattr(value, "fa") and hasattr(value.fa, "set_flow_style"):
            value.fa.set_flow_style()
            changed = True

    if not changed:
        return _fix_whitespace(text)

    buf = io.StringIO()
    y.dump(data, buf)
    new_fm = buf.getvalue().rstrip("\n")
    return _fix_whitespace(f"---\n{new_fm}\n---\n{body}")


def format_file(path: Path, check: bool = False, diff: bool = False) -> bool:
    """Format a single OKF concept file.

    Args:
        path: Path to the markdown file.
        check: If ``True``, do not modify the file; only report whether
            changes would be needed.
        diff: If ``True``, do not modify the file; only report whether
            changes would be needed (the actual diff is produced by
            :func:`format_bundle`).

    Returns:
        ``True`` if the file needed formatting changes.
    """
    text = path.read_text(encoding="utf-8")
    result = format_frontmatter(text)
    if result is None or result == text:
        return False

    if not check and not diff:
        path.write_text(result, encoding="utf-8")

    return True


def format_bundle(bundle: Path, check: bool = False, diff: bool = False) -> list[FormattedResult]:
    """Format all concept files in an OKF bundle.

    Args:
        bundle: Root directory of the OKF bundle.
        check: If ``True``, do not modify any files.
        diff: If ``True``, include a unified diff string in each
            :class:`FormattedResult` without modifying files.

    Returns:
        A list of results, one per markdown file found in the bundle.
    """
    results: list[FormattedResult] = []
    for path in collect_markdown_files(bundle):
        text = path.read_text(encoding="utf-8")
        original = text
        formatted = format_frontmatter(text)

        if formatted is None or formatted == original:
            results.append(FormattedResult(path=path, changed=False))
            continue

        diff_str: str | None = None
        if diff:
            diff_str = "".join(
                difflib.unified_diff(
                    original.splitlines(keepends=True),
                    formatted.splitlines(keepends=True),
                    fromfile=str(path),
                    tofile=str(path),
                )
            )

        if not check and not diff:
            path.write_text(formatted, encoding="utf-8")

        results.append(FormattedResult(path=path, changed=True, diff=diff_str))

    return results


def lint_bundle(bundle: Path, check: bool = False, diff: bool = False) -> list[FormattedResult]:
    """Lint all concept files in an OKF bundle (convert block lists to inline).

    Args:
        bundle: Root directory of the OKF bundle.
        check: If ``True``, do not modify any files.
        diff: If ``True``, include a unified diff string in each
            :class:`FormattedResult` without modifying files.

    Returns:
        A list of results, one per markdown file found in the bundle.
    """
    results: list[FormattedResult] = []
    for path in collect_markdown_files(bundle):
        text = path.read_text(encoding="utf-8")
        original = text
        linted = lint_frontmatter(text)

        if linted is None or linted == original:
            results.append(FormattedResult(path=path, changed=False))
            continue

        diff_str: str | None = None
        if diff:
            diff_str = "".join(
                difflib.unified_diff(
                    original.splitlines(keepends=True),
                    linted.splitlines(keepends=True),
                    fromfile=str(path),
                    tofile=str(path),
                )
            )

        if not check and not diff:
            path.write_text(linted, encoding="utf-8")

        results.append(FormattedResult(path=path, changed=True, diff=diff_str))

    return results
