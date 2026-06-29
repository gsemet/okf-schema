"""Built-in OKF schemas."""

from __future__ import annotations

MINIMAL_SCHEMA: dict = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "properties": {
        "type": {
            "type": "string",
            "minLength": 1,
        },
    },
    "required": ["type"],
}


def get_builtin_schema() -> dict:
    """Return the built-in minimal OKF schema.

    The minimal schema requires that frontmatter contains a ``type``
    field which is a non-empty string.
    """
    return MINIMAL_SCHEMA.copy()
