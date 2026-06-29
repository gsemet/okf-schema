"""YAML helpers using ruamel.yaml for OKF frontmatter handling."""

from __future__ import annotations

from datetime import date, datetime
from typing import cast

from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError


def make_yaml() -> YAML:
    """Return a configured ruamel.yaml instance for round-trip parsing.

    Configures ``preserve_quotes=True`` and ``default_flow_style=False``
    so that formatting and comments are retained during load/dump cycles.
    """
    y = YAML()
    y.preserve_quotes = True
    y.default_flow_style = False
    return y


def _normalize_yaml_value(value: object) -> object:
    """Recursively convert YAML-native types to JSON-compatible primitives.

    ruamel.yaml parses ISO 8601 dates as ``datetime.date`` and
    ``datetime.datetime`` objects.  JSON Schema validators expect
    ``type: string`` fields to be actual strings, so we transparently
    convert them to ISO 8601 strings here.
    """
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _normalize_yaml_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_normalize_yaml_value(item) for item in value]
    return value


def extract_frontmatter(text: str) -> tuple[str | None, str]:
    """Extract YAML frontmatter from markdown text.

    Frontmatter is delimited by ``---`` at the start of the file and a
    closing ``---`` on its own line. Returns ``(frontmatter_yaml, body)``
    or ``(None, text)`` when no valid frontmatter block is found.
    """
    if not text.startswith("---"):
        return None, text

    end_marker = "\n---"
    end_idx = text.find(end_marker, 3)
    if end_idx == -1:
        return None, text

    fm_text = text[3:end_idx]
    body = text[end_idx + len(end_marker) :]
    if body.startswith("\n"):
        body = body[1:]
    return fm_text, body


def parse_yaml(yaml_text: str) -> dict | None:
    """Parse YAML text into a plain dict.

    Uses :func:`make_yaml` for consistent configuration. Returns ``None``
    when the text is not valid YAML or does not parse to a mapping.

    Date and datetime values are automatically converted to ISO 8601
    strings so that JSON Schema ``type: string`` validation works
    transparently for unquoted YAML dates.
    """
    y = make_yaml()
    try:
        data = y.load(yaml_text)
    except YAMLError:
        return None
    if not isinstance(data, dict):
        return None
    # ruamel.yaml returns CommentedMap — convert to plain dict
    # and normalize native datetime types to strings
    return cast(dict, _normalize_yaml_value(dict(data)))


def dump_yaml(data: dict) -> str:
    """Serialize a dict to a YAML string.

    Uses :func:`make_yaml` so that quotes and comments are preserved
    when round-tripping through :func:`parse_yaml`.
    """
    from io import StringIO

    y = make_yaml()
    buf = StringIO()
    y.dump(data, buf)
    return buf.getvalue()
