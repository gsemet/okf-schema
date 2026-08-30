"""Provide the built-in Open Knowledge Format (OKF) fallback schema.

The minimal schema checks only that frontmatter has a non-empty ``type``.
Applications that need type-specific validation should load a schema database
through :func:`okf_schema.validator.load_schema_database`.
"""

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


# @implements_req SwRS-OKFSCHEMA-CORE-001
def get_builtin_schema() -> dict:
    """Return the built-in minimal OKF schema.

    The minimal schema requires that frontmatter contains a ``type``
    field which is a non-empty string.

    Returns:
        A shallow copy of the minimal schema dictionary.

    Examples:
        >>> get_builtin_schema()["required"]
        ['type']
    """
    return MINIMAL_SCHEMA.copy()
