"""Project schema-declared metadata onto the fields every OKF v0.2 consumer reads.

A plain OKF consumer reads lifecycle from ``status`` and relations from
Markdown links in the body. Bundles that keep richer metadata declare, in their
JSON Schemas, how it is projected for such consumers:

- ``x-okf-link`` may carry a ``link-projection`` label. Each value of the field
  becomes a Markdown link in a generated ``### Links`` body section, one group per
  annotated field, in schema order (base schema first).
- A property may carry an ``x-okf-status-projection`` mapping from its values to
  the OKF ``status`` values ``draft``, ``stable`` and ``deprecated``.

A field without a projection annotation is never projected. The generated body
section is delimited by :data:`LINKS_START` and :data:`LINKS_END`; it is removed
when no annotated field has a value.

.. versionadded:: 0.17.0

Examples:
    >>> schema = {
    ...     "properties": {
    ...         "state": {"enum": ["wip", "done"],
    ...                   "x-okf-status-projection": {"wip": "draft", "done": "stable"}},
    ...         "parents": {"items": {"x-okf-link": {
    ...             "resolution": "filename-stem", "syntax": "plain",
    ...             "link-projection": "Parents"}}},
    ...     }
    ... }
    >>> projection = schema_projection(schema)
    >>> projection.status_field, [link.label for link in projection.links]
    ('state', ['Parents'])
"""

from __future__ import annotations

import os
from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ruamel.yaml.comments import CommentedMap

from okf_schema._internal.yaml import (
    _normalize_yaml_value,
    dump_yaml,
    extract_frontmatter,
    make_yaml,
    parse_yaml,
)
from okf_schema.file_links import (
    PROJECTABLE_RESOLUTIONS,
    FileLinkDiagnostic,
    _FileLinkContext,
    _parse_value,
    _resolve_exact_target,
    _resolve_filename_stem,
)

LINKS_START = "<!-- okf:links:start -->"
LINKS_END = "<!-- okf:links:end -->"
LINKS_HEADING = "### Links"
LINKS_NOTICE = "<!-- Generated from the frontmatter relations; edit them instead. -->"
LINK_PROJECTION_KEY = "link-projection"
STATUS_PROJECTION_KEY = "x-okf-status-projection"
OKF_STATUSES = ("draft", "stable", "deprecated")

Derive = Callable[[CommentedMap], Mapping[str, tuple[Any, str | None]]]


class ProjectionError(ValueError):
    """Raised when a generated Links section cannot be replaced safely."""


@dataclass(frozen=True)
class LinkProjection:
    """One relation field projected as a group of Markdown links."""

    field: str
    label: str
    resolution: str
    syntax: str = "plain"


@dataclass(frozen=True)
class SchemaProjection:
    """What a schema asks to project: link groups and the status mapping."""

    links: tuple[LinkProjection, ...] = ()
    status_field: str | None = None
    status_map: dict[str, str] = field(default_factory=dict)


def _properties(schema: Any) -> Iterator[tuple[str, dict[str, Any]]]:
    """Yield schema properties in projection order: ``allOf`` branches first."""
    if isinstance(schema, list):
        for item in schema:
            yield from _properties(item)
        return
    if not isinstance(schema, dict):
        return
    yield from _properties(schema.get("allOf"))
    properties = schema.get("properties")
    if isinstance(properties, dict):
        for name, prop in properties.items():
            if isinstance(prop, dict):
                yield str(name), prop


def _link_annotation(prop: dict[str, Any]) -> Any:
    """Return the ``x-okf-link`` annotation of a property or of its items."""
    if "x-okf-link" in prop:
        return prop["x-okf-link"]
    items = prop.get("items")
    return items.get("x-okf-link") if isinstance(items, dict) else None


def schema_projection(schema: Any) -> SchemaProjection:
    """Read the projections declared by a resolved schema.

    Malformed annotations are ignored here; :func:`projection_problems` reports them.

    Args:
        schema:
            A schema with its ``$ref`` already resolved, or ``None``.

    Returns:
        The link groups in schema order and the first status mapping found.
    """
    links: list[LinkProjection] = []
    seen: set[str] = set()
    status_field: str | None = None
    status_map: dict[str, str] = {}
    for name, prop in _properties(schema):
        annotation = _link_annotation(prop)
        if isinstance(annotation, dict) and name not in seen:
            label = annotation.get(LINK_PROJECTION_KEY)
            resolution = annotation.get("resolution")
            if isinstance(label, str) and label.strip() and resolution in PROJECTABLE_RESOLUTIONS:
                syntax = annotation.get("syntax")
                links.append(
                    LinkProjection(
                        name,
                        label.strip(),
                        str(resolution),
                        syntax if isinstance(syntax, str) else "plain",
                    )
                )
                seen.add(name)
        mapping = prop.get(STATUS_PROJECTION_KEY)
        if status_field is None and isinstance(mapping, dict):
            status_field = name
            status_map = {str(key): str(value) for key, value in mapping.items()}
    return SchemaProjection(tuple(links), status_field, status_map)


def projection_problems(schema: Any) -> list[str]:
    """Report malformed ``link-projection`` and ``x-okf-status-projection`` annotations.

    Args:
        schema:
            A schema with its ``$ref`` already resolved.

    Returns:
        One message per problem, prefixed with the property name: an empty or
        non-string label, a label on a resolution that leaves the bundle, a status
        mapping that is not a mapping, maps to a value outside ``draft``, ``stable``
        and ``deprecated``, or misses a value of the property ``enum``.

    Examples:
        >>> projection_problems({"properties": {"files": {"items": {"x-okf-link": {
        ...     "resolution": "project-relative", "link-projection": "Files"}}}}})
        ['files: x-okf-link link-projection needs a resolution inside the bundle (bundle-relative, bundle-relative-stem, filename-stem), not project-relative']
    """  # noqa: E501
    # @implements_req SwRS-OKFSCHEMA-CORE-009
    problems: list[str] = []
    for name, prop in _properties(schema):
        annotation = _link_annotation(prop)
        if isinstance(annotation, dict) and LINK_PROJECTION_KEY in annotation:
            label = annotation[LINK_PROJECTION_KEY]
            resolution = annotation.get("resolution")
            if not isinstance(label, str) or not label.strip():
                problems.append(f"{name}: x-okf-link link-projection must be a non-empty string")
            elif resolution not in PROJECTABLE_RESOLUTIONS:
                allowed = ", ".join(sorted(PROJECTABLE_RESOLUTIONS))
                problems.append(
                    f"{name}: x-okf-link link-projection needs a resolution inside the "
                    f"bundle ({allowed}), not {resolution}"
                )
        if STATUS_PROJECTION_KEY not in prop:
            continue
        mapping = prop[STATUS_PROJECTION_KEY]
        if not isinstance(mapping, dict) or not mapping:
            problems.append(
                f"{name}: {STATUS_PROJECTION_KEY} must map each {name} value to an OKF status"
            )
            continue
        for key, value in mapping.items():
            if value not in OKF_STATUSES:
                problems.append(
                    f"{name}: {STATUS_PROJECTION_KEY} maps {key} to {value}; "
                    f"expected one of {', '.join(OKF_STATUSES)}"
                )
        enum = prop.get("enum")
        if isinstance(enum, list):
            mapped = {str(key) for key in mapping}
            missing = [str(value) for value in enum if str(value) not in mapped]
            if missing:
                problems.append(
                    f"{name}: {STATUS_PROJECTION_KEY} has no OKF status for {', '.join(missing)}"
                )
    return list(dict.fromkeys(problems))


def projected_status(data: Mapping[str, Any], projection: SchemaProjection) -> str | None:
    """Return the OKF ``status`` mapped from the annotated field, or ``None``."""
    if projection.status_field is None or projection.status_field not in data:
        return None
    return projection.status_map.get(str(data.get(projection.status_field)))


def _links_span(body: str) -> tuple[int, int] | None:
    """Return the span of the generated Links section, or ``None`` without one."""
    starts, ends = body.count(LINKS_START), body.count(LINKS_END)
    if starts == 0 and ends == 0:
        return None
    if starts != 1 or ends != 1 or body.index(LINKS_START) > body.index(LINKS_END):
        raise ProjectionError("expected one complete generated Links section")
    return body.index(LINKS_START), body.index(LINKS_END) + len(LINKS_END)


def strip_links_section(body: str) -> str:
    """Return *body* without its generated Links section.

    Malformed delimiters are left in place, so the caller still sees the text.

    Examples:
        >>> strip_links_section(f"Intro\\n\\n{LINKS_START}\\n- x\\n{LINKS_END}\\n")
        'Intro\\n\\n\\n'
    """
    try:
        span = _links_span(body)
    except ProjectionError:
        return body
    return body if span is None else body[: span[0]] + body[span[1] :]


def replace_links_section(body: str, block: str) -> str:
    """Replace or append the generated Links section at the end of *body*.

    An empty *block* removes the section. A body without a section and an empty
    block is returned unchanged.

    Raises:
        ProjectionError:
            If the body holds an incomplete or repeated section.
    """
    span = _links_span(body)
    if span is None and not block:
        return body
    if span is not None:
        head = body[: span[0]].rstrip("\n")
        tail = body[span[1] :].strip("\n")
        body = "\n\n".join(part for part in (head, tail) if part)
    body = body.rstrip("\n")
    if not block:
        return f"{body}\n" if body else ""
    return f"{body}\n\n{block}\n" if body else f"{block}\n"


def render_links_section(groups: Sequence[tuple[str, Sequence[str]]]) -> str:
    """Render the generated Links section, or an empty string without entries.

    Args:
        groups:
            Group labels with their rendered entries (a Markdown link or code).
    """
    lines: list[str] = []
    for label, entries in groups:
        if not entries:
            continue
        lines.append(f"- {label}:")
        lines.extend(f"  - {entry}" for entry in entries)
    if not lines:
        return ""
    return "\n".join([LINKS_START, LINKS_HEADING, "", LINKS_NOTICE, "", *lines, LINKS_END])


def set_field(data: CommentedMap, key: str, value: Any, *, after: str | None = None) -> bool:
    """Set, replace or remove a generated frontmatter field.

    A new key is inserted after *after* when present, else at the end. ``None``
    removes the key. Equal values, compared after date normalization, are kept.

    Returns:
        ``True`` when *data* changed.
    """
    if value is None:
        if key in data:
            del data[key]
            return True
        return False
    if key in data:
        if _normalize_yaml_value(data[key]) == _normalize_yaml_value(value):
            return False
        data[key] = value
        return True
    keys = list(data)
    data.insert(keys.index(after) + 1 if after in keys else len(keys), key, value)
    return True


def _values(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str) and item.strip()]
    return []


def _escape(text: str) -> str:
    return " ".join(text.split()).replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]")


class LinkResolver:
    """Resolve projected relation values to bundle files and read their titles.

    Stem indexes and titles are cached for one run over a bundle.
    """

    def __init__(self, bundle_root: Path) -> None:
        self.bundle_root = bundle_root
        self._context = _FileLinkContext()
        self._titles: dict[Path, str] = {}

    def resolve(self, value: str, link: LinkProjection, document: Path) -> Path | None:
        """Return the file a value names, or ``None`` when it does not resolve to one."""
        parsed = _parse_value(value, link.syntax, link.field)
        if isinstance(parsed, FileLinkDiagnostic):
            return None
        if link.resolution == "filename-stem":
            result = _resolve_filename_stem(
                parsed.target, self.bundle_root, link.field, self._context
            )
        else:
            result = _resolve_exact_target(
                parsed.target, link.resolution, document, self.bundle_root, None, link.field
            )
        return None if isinstance(result, FileLinkDiagnostic) else result.path

    def title(self, path: Path) -> str:
        """Return the frontmatter ``title`` of *path*, or an empty string."""
        if path not in self._titles:
            frontmatter, _ = extract_frontmatter(path.read_text(encoding="utf-8"))
            data = parse_yaml(frontmatter) if frontmatter is not None else None
            title = data.get("title") if isinstance(data, dict) else None
            self._titles[path] = " ".join(str(title).split()) if title else ""
        return self._titles[path]

    def entry(self, value: str, link: LinkProjection, document: Path) -> str:
        """Render one Links entry: a relative Markdown link, or code when unresolved."""
        target = self.resolve(value, link, document)
        if target is None:
            return f"`{value}`"
        relative = os.path.relpath(target, document.resolve().parent).replace(os.sep, "/")
        title = _escape(self.title(target))
        return f"[{_escape(value)}]({relative})" + (f": {title}" if title else "")


def project_text(
    text: str,
    document: Path,
    projection: SchemaProjection,
    resolver: LinkResolver,
    *,
    status: bool = True,
    updates: Mapping[str, tuple[Any, str | None]] | None = None,
    derive: Derive | None = None,
) -> str:
    """Apply a schema projection to one Markdown document.

    Args:
        text:
            Full document text.
        document:
            Path of the document, used for relative links.
        projection:
            Projection read from the document's schema.
        resolver:
            Resolver shared by the documents of one bundle.
        status:
            Maintain ``status`` from the status mapping.
        updates:
            Extra generated fields as ``key: (value, insert_after)``; ``None``
            removes the key.
        derive:
            Callback computing more such fields from the round-trip frontmatter.

    Returns:
        The projected text; *text* itself when nothing changes. The frontmatter
        is re-serialized only when a field changed.

    Raises:
        ProjectionError:
            If the body holds an incomplete or repeated Links section.
    """
    # @implements_req SwRS-OKFSCHEMA-CORE-009
    frontmatter, body = extract_frontmatter(text)
    if frontmatter is None:
        return text
    data = make_yaml().load(frontmatter)
    if not isinstance(data, CommentedMap):
        return text
    changed = False
    if status and projection.status_field not in (None, "status"):
        changed |= set_field(
            data, "status", projected_status(data, projection), after=projection.status_field
        )
    for key, (value, after) in (updates or {}).items():
        changed |= set_field(data, key, value, after=after)
    for key, (value, after) in (derive(data) if derive is not None else {}).items():
        changed |= set_field(data, key, value, after=after)
    groups = [
        (
            link.label,
            [resolver.entry(value, link, document) for value in _values(data.get(link.field))],
        )
        for link in projection.links
    ]
    new_body = replace_links_section(body, render_links_section(groups))
    if not changed and new_body == body:
        return text
    head = f"---\n{dump_yaml(data)}---\n" if changed else text[: len(text) - len(body)]
    return head + new_body


class BundleProjector:
    """Project every document of a bundle through the schema of its ``type``.

    Args:
        bundle_root:
            Root that relation values resolve against.
        schemas:
            Resolved schemas keyed by type; a type matches exactly, else
            case-insensitively.
        status:
            Maintain ``status`` from status mappings.
    """

    def __init__(
        self,
        bundle_root: Path,
        schemas: Mapping[str, Any],
        *,
        status: bool = True,
    ) -> None:
        self.resolver = LinkResolver(bundle_root)
        self.schemas = dict(schemas)
        self._folded = {str(name).casefold(): schema for name, schema in schemas.items()}
        self.status = status
        self._cache: dict[str, SchemaProjection] = {}

    def projection_for(self, type_name: str) -> SchemaProjection:
        """Return the projection of the schema matching *type_name*."""
        if type_name not in self._cache:
            schema = self.schemas.get(type_name, self._folded.get(type_name.casefold()))
            self._cache[type_name] = schema_projection(schema)
        return self._cache[type_name]

    def project(
        self,
        path: Path,
        text: str,
        *,
        updates: Mapping[str, tuple[Any, str | None]] | None = None,
        derive: Derive | None = None,
    ) -> str:
        """Return *text* projected through the schema of its ``type``."""
        frontmatter, _ = extract_frontmatter(text)
        data = parse_yaml(frontmatter) if frontmatter is not None else None
        type_name = str(data.get("type") or "") if isinstance(data, dict) else ""
        return project_text(
            text,
            path,
            self.projection_for(type_name),
            self.resolver,
            status=self.status,
            updates=updates,
            derive=derive,
        )
