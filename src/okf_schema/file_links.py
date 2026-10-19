"""Check opt-in ``x-okf-link`` annotations in JSON Schema documents.

The annotation is deliberately separate from JSON Schema validation. It
describes how a string value names a Markdown or project file, while the
standard validator continues to enforce only the schema's normal keywords.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path, PureWindowsPath
from typing import Any, Literal

from jsonschema import Draft202012Validator, FormatChecker

RESOLUTIONS = frozenset(
    {
        "document-relative",
        "bundle-relative",
        "bundle-relative-stem",
        "project-relative",
        "filename-stem",
    }
)
SYNTAXES = frozenset({"plain", "wikilink"})


@dataclass(frozen=True)
class FileLinkDiagnostic:
    """A result from opt-in file-link checking.

    ``severity`` is ``"error"`` for a resolvable invalid target or malformed
    annotation and ``"warning"`` for a check that was deliberately skipped.
    """

    severity: Literal["error", "warning"]
    code: Literal["E10", "W15"]
    message: str
    field_path: str


@dataclass(frozen=True)
class ParsedFileLink:
    """Parsed target components from a plain or wikilink value."""

    target: str
    query: str | None
    fragment: str | None
    label: str | None


@dataclass(frozen=True)
class FileLinkResult:
    """A structured result for one annotated frontmatter value.

    .. versionadded:: 0.13.0

    .. versionchanged:: 0.13.0
        ``value_identity`` is an escaped JSON Pointer, distinct from the
        human-readable ``field_path``. Stem indexes are scoped to one inspection.

    ``status`` is ``"valid"`` for a resolved target, ``"invalid"`` for an
    ``E10`` result, and ``"unavailable"`` for a skipped ``W15`` check.
    ``value_identity`` is the stable JSON Pointer identity used by consumers;
    ``array_index`` is populated separately for an annotated array item.
    """

    value: Any
    value_identity: str
    field_path: str
    array_index: int | None
    syntax: str | None
    resolution: str | None
    target: str | None
    normalized_target: str | None
    resolved_path: Path | None
    query: str | None
    fragment: str | None
    label: str | None
    status: Literal["valid", "invalid", "unavailable"]
    code: Literal["E10", "W15"] | None
    severity: Literal["error", "warning"] | None
    message: str


@dataclass(frozen=True)
class _ResolvedFileLink:
    path: Path
    normalized_target: str


@dataclass
class _FileLinkContext:
    """Cache a bundle's Markdown candidates for one validation campaign only."""

    stems: dict[Path, dict[str, list[Path]]] = field(default_factory=dict)

    def candidates(self, root: Path, target: str) -> list[Path]:
        if root not in self.stems:
            index: dict[str, list[Path]] = {}
            for candidate in root.rglob("*.md"):
                index.setdefault(candidate.stem, []).append(candidate)
            self.stems[root] = index
        return self.stems[root].get(target, [])


def _field_path(path: tuple[str | int, ...]) -> str:
    result = ""
    for part in path:
        if isinstance(part, int):
            result += f"[{part}]"
        else:
            result += f".{part}" if result else part
    return result or "<root>"


def _value_identity(path: tuple[str | int, ...]) -> str:
    return "".join("/" + str(part).replace("~", "~0").replace("/", "~1") for part in path)


def _resolve_local_ref(root_schema: dict[str, Any], ref: str) -> Any | None:
    if ref == "#":
        return root_schema
    if not ref.startswith("#/"):
        return None

    current: Any = root_schema
    for token in ref[2:].split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict):
            if token not in current:
                return None
            current = current[token]
        elif isinstance(current, list):
            if token == "0":
                index = 0
            elif token.isdigit() and not token.startswith("0"):
                index = int(token)
            else:
                return None
            if index >= len(current):
                return None
            current = current[index]
        else:
            return None
    return current


def _branch_applies(
    validator: Any | None,
    branch: Any,
    value: Any,
) -> bool:
    if validator is None:
        return False
    try:
        # Descend from the root validator so local references keep their scope
        # and $ref siblings remain conjunctive constraints, not dict overrides.
        return next(validator.descend(value, branch), None) is None
    except Exception:  # noqa: BLE001
        return False


def _iter_annotations(
    schema: Any,
    value: Any,
    path: tuple[str | int, ...] = (),
    *,
    root_schema: dict[str, Any] | None = None,
    validator: Any | None = None,
    active_refs: frozenset[tuple[str, int]] = frozenset(),
) -> Iterator[tuple[Any, Any, tuple[str | int, ...], int | None]]:
    if not isinstance(schema, dict):
        return

    if root_schema is None:
        root_schema = schema

    ref_value = schema.get("$ref")
    if isinstance(ref_value, str):
        ref_key = (ref_value, id(value))
        if ref_key not in active_refs:
            resolved = _resolve_local_ref(root_schema, ref_value)
            if isinstance(resolved, dict):
                yield from _iter_annotations(
                    resolved,
                    value,
                    path,
                    root_schema=root_schema,
                    validator=validator,
                    active_refs=active_refs | {ref_key},
                )

        siblings = {key: child for key, child in schema.items() if key != "$ref"}
        if siblings:
            yield from _iter_annotations(
                siblings,
                value,
                path,
                root_schema=root_schema,
                validator=validator,
                active_refs=active_refs,
            )
        return

    if "x-okf-link" in schema:
        yield (
            schema["x-okf-link"],
            value,
            path,
            path[-1] if path and isinstance(path[-1], int) else None,
        )

    properties = schema.get("properties")
    if isinstance(properties, dict) and isinstance(value, dict):
        for name, child_schema in properties.items():
            if name in value:
                yield from _iter_annotations(
                    child_schema,
                    value[name],
                    (*path, str(name)),
                    root_schema=root_schema,
                    validator=validator,
                    active_refs=active_refs,
                )

    items = schema.get("items")
    prefix_items = schema.get("prefixItems")
    if isinstance(value, list):
        if isinstance(items, dict):
            start_index = len(prefix_items) if isinstance(prefix_items, list) else 0
            for index, item in enumerate(value[start_index:], start=start_index):
                yield from _iter_annotations(
                    items,
                    item,
                    (*path, index),
                    root_schema=root_schema,
                    validator=validator,
                    active_refs=active_refs,
                )
        elif isinstance(items, list):
            for index, (item, child_schema) in enumerate(zip(value, items, strict=False)):
                yield from _iter_annotations(
                    child_schema,
                    item,
                    (*path, index),
                    root_schema=root_schema,
                    validator=validator,
                    active_refs=active_refs,
                )

        if isinstance(prefix_items, list):
            for index, (item, child_schema) in enumerate(zip(value, prefix_items, strict=False)):
                yield from _iter_annotations(
                    child_schema,
                    item,
                    (*path, index),
                    root_schema=root_schema,
                    validator=validator,
                    active_refs=active_refs,
                )

    for keyword in ("allOf", "anyOf", "oneOf"):
        branches = schema.get(keyword)
        if isinstance(branches, list):
            if keyword in {"anyOf", "oneOf"}:
                branches = [
                    branch for branch in branches if _branch_applies(validator, branch, value)
                ]
            for branch in branches:
                yield from _iter_annotations(
                    branch,
                    value,
                    path,
                    root_schema=root_schema,
                    validator=validator,
                    active_refs=active_refs,
                )

    if "if" in schema:
        keyword = "then" if _branch_applies(validator, schema["if"], value) else "else"
        if keyword in schema:
            yield from _iter_annotations(
                schema[keyword],
                value,
                path,
                root_schema=root_schema,
                validator=validator,
                active_refs=active_refs,
            )


def _error(field_path: str, message: str) -> FileLinkDiagnostic:
    return FileLinkDiagnostic("error", "E10", f"{message} at '{field_path}'", field_path)


def _skipped(field_path: str, message: str) -> FileLinkDiagnostic:
    return FileLinkDiagnostic(
        "warning",
        "W15",
        f"Skipped file-link check at '{field_path}': {message}",
        field_path,
    )


def _parse_annotation(
    annotation: Any,
    field_path: str,
) -> tuple[str, str] | FileLinkDiagnostic:
    if not isinstance(annotation, dict):
        return _error(field_path, "x-okf-link must be an object")

    resolution = annotation.get("resolution")
    syntax = annotation.get("syntax")
    if not isinstance(resolution, str) or resolution not in RESOLUTIONS:
        return _error(
            field_path,
            "x-okf-link resolution must be one of " + ", ".join(sorted(RESOLUTIONS)),
        )
    if not isinstance(syntax, str) or syntax not in SYNTAXES:
        return _error(
            field_path,
            "x-okf-link syntax must be one of " + ", ".join(sorted(SYNTAXES)),
        )
    return resolution, syntax


def _parse_value(
    value: Any,
    syntax: str,
    field_path: str,
) -> ParsedFileLink | FileLinkDiagnostic:
    if not isinstance(value, str):
        return _error(field_path, "file-link value must be a string")
    label: str | None = None
    target_with_suffix = value
    if syntax == "wikilink":
        if not value.startswith("[[") or not value.endswith("]]"):
            return _error(
                field_path,
                "wikilink value must use [[target]], [[target#fragment]], "
                "or [[target|label]] syntax",
            )
        content = value[2:-2]
        target_with_suffix, separator, label_value = content.partition("|")
        label = label_value if separator else None
        target_with_suffix = target_with_suffix.strip()

    fragment_index = target_with_suffix.find("#")
    path_and_query = (
        target_with_suffix if fragment_index < 0 else target_with_suffix[:fragment_index]
    )
    fragment = None if fragment_index < 0 else target_with_suffix[fragment_index + 1 :]
    query_index = path_and_query.find("?")
    target = path_and_query if query_index < 0 else path_and_query[:query_index]
    query = None if query_index < 0 else path_and_query[query_index + 1 :]
    target = target.strip()
    if "\x00" in target:
        return _error(field_path, "file-link target contains a null character")
    if not target:
        return _error(
            field_path,
            "wikilink target is empty" if syntax == "wikilink" else "file-link target is empty",
        )
    return ParsedFileLink(target, query, fragment, label)


def _root_path(path: Path | None) -> Path | None:
    if path is None:
        return None
    try:
        resolved = path.expanduser().resolve()
    except OSError:
        return None
    return resolved if resolved.is_dir() else None


def _git_root(document_path: Path) -> Path | None:
    try:
        current = document_path.expanduser().resolve()
    except OSError:
        return None
    if not current.is_dir():
        current = current.parent
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate
    return None


def _within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _reject_absolute(target: str, field_path: str) -> FileLinkDiagnostic | None:
    path = Path(target)
    windows_path = PureWindowsPath(target)
    if path.is_absolute() or path.drive or windows_path.is_absolute() or windows_path.drive:
        return _error(field_path, f"absolute target '{target}' is not allowed")
    return None


def _resolve_exact_target(
    target: str,
    resolution: str,
    document_path: Path,
    bundle_root: Path | None,
    project_root: Path | None,
    field_path: str,
) -> _ResolvedFileLink | FileLinkDiagnostic:
    absolute_error = _reject_absolute(target, field_path)
    if absolute_error is not None:
        return absolute_error

    if resolution == "document-relative":
        root = _root_path(document_path.parent)
    elif resolution in {"bundle-relative", "bundle-relative-stem"}:
        root = _root_path(bundle_root)
    else:
        root = _root_path(project_root) or _git_root(document_path)

    if root is None:
        return _skipped(
            field_path,
            f"{resolution} root is unavailable; provide --project-root when needed",
        )

    filename = f"{target}.md" if resolution == "bundle-relative-stem" else target
    try:
        candidate = (root / filename).resolve(strict=False)
        is_file = candidate.is_file()
    except (OSError, RuntimeError) as exc:
        return _skipped(field_path, f"target '{target}' could not be inspected: {exc}")
    if resolution != "document-relative" and not _within(candidate, root):
        return _error(field_path, f"target '{target}' escapes its {resolution} root")
    if not is_file:
        return _error(field_path, f"target '{target}' does not resolve to a file")
    normalized_target = f"{target}.md" if resolution == "bundle-relative-stem" else target
    return _ResolvedFileLink(candidate, normalized_target)


def _resolve_filename_stem(
    target: str,
    bundle_root: Path | None,
    field_path: str,
    context: _FileLinkContext | None = None,
) -> _ResolvedFileLink | FileLinkDiagnostic:
    absolute_error = _reject_absolute(target, field_path)
    if absolute_error is not None:
        return absolute_error
    root = _root_path(bundle_root)
    if root is None:
        return _skipped(
            field_path,
            "filename-stem lookup needs an available bundle root; the workspace may be unavailable",
        )

    matches: list[Path] = []
    escaped = False
    unavailable = False
    try:
        candidates = (context or _FileLinkContext()).candidates(root, target)
    except OSError as exc:
        return _skipped(field_path, f"bundle could not be inspected: {exc}")
    for candidate in candidates:
        try:
            if not candidate.is_file():
                continue
            resolved = candidate.resolve()
        except (OSError, RuntimeError):
            unavailable = True
            continue
        if _within(resolved, root):
            matches.append(resolved)
        else:
            escaped = True

    if not matches:
        if unavailable:
            return _skipped(
                field_path,
                f"the matching Markdown file for '{target}' could not be resolved; "
                "the workspace may be unavailable",
            )
        return _error(
            field_path,
            f"filename stem '{target}' escapes its filename-stem root"
            if escaped
            else f"filename stem '{target}' was not found",
        )
    matches = list(dict.fromkeys(matches))
    if len(matches) > 1:
        locations = ", ".join(str(path.relative_to(root)) for path in sorted(matches))
        return _error(
            field_path,
            f"filename stem '{target}' is ambiguous in the bundle ({locations})",
        )
    return _ResolvedFileLink(matches[0], target)


def _check_exact_target(
    target: str,
    resolution: str,
    document_path: Path,
    bundle_root: Path | None,
    project_root: Path | None,
    field_path: str,
) -> FileLinkDiagnostic | None:
    result = _resolve_exact_target(
        target,
        resolution,
        document_path,
        bundle_root,
        project_root,
        field_path,
    )
    return result if isinstance(result, FileLinkDiagnostic) else None


def _check_filename_stem(
    target: str,
    bundle_root: Path | None,
    field_path: str,
) -> FileLinkDiagnostic | None:
    result = _resolve_filename_stem(target, bundle_root, field_path)
    return result if isinstance(result, FileLinkDiagnostic) else None


def _result_for_diagnostic(
    value: Any,
    value_identity: str,
    field_path: str,
    array_index: int | None,
    *,
    syntax: str | None,
    resolution: str | None,
    target: str | None,
    query: str | None = None,
    fragment: str | None = None,
    label: str | None = None,
    diagnostic: FileLinkDiagnostic,
) -> FileLinkResult:
    return FileLinkResult(
        value=value,
        value_identity=value_identity,
        field_path=field_path,
        array_index=array_index,
        syntax=syntax,
        resolution=resolution,
        target=target,
        normalized_target=target,
        resolved_path=None,
        query=query,
        fragment=fragment,
        label=label,
        status="unavailable" if diagnostic.code == "W15" else "invalid",
        code=diagnostic.code,
        severity=diagnostic.severity,
        message=diagnostic.message,
    )


def inspect_file_links(
    frontmatter: dict[str, Any],
    schema: dict[str, Any],
    document_path: Path,
    *,
    bundle_root: Path | None = None,
    project_root: Path | None = None,
    _context: _FileLinkContext | None = None,
) -> list[FileLinkResult]:
    """Inspect every ``x-okf-link`` value, including successful values.

    .. versionadded:: 0.13.0

    Args:
        frontmatter:
            Parsed document frontmatter to inspect.
        schema:
            JSON Schema containing optional ``x-okf-link`` annotations.
        document_path:
            Markdown document whose frontmatter is being checked.
        bundle_root:
            Bundle root for bundle-relative and filename-stem references.
        project_root:
            Explicit project root for project-relative references. When it is
            unavailable, the containing Git root of *document_path* is used.

    Returns:
        One structured result for each applicable annotated value. Successful
        results include their resolved path and parsed suffix components.
    """
    context = _context or _FileLinkContext()
    results: list[FileLinkResult] = []
    seen: set[tuple[str, str, str, str]] = set()
    try:
        validator: Any | None = Draft202012Validator(
            schema,
            format_checker=FormatChecker(),
        )
    except Exception:  # noqa: BLE001
        validator = None
    for annotation, value, path, array_index in _iter_annotations(
        schema,
        frontmatter,
        validator=validator,
    ):
        field_path = _field_path(path)
        value_identity = _value_identity(path)
        parsed_annotation = _parse_annotation(annotation, field_path)
        if isinstance(parsed_annotation, FileLinkDiagnostic):
            results.append(
                _result_for_diagnostic(
                    value,
                    value_identity,
                    field_path,
                    array_index,
                    syntax=None,
                    resolution=None,
                    target=None,
                    diagnostic=parsed_annotation,
                )
            )
            continue
        resolution, syntax = parsed_annotation
        parsed_value = _parse_value(value, syntax, field_path)
        if isinstance(parsed_value, FileLinkDiagnostic):
            results.append(
                _result_for_diagnostic(
                    value,
                    value_identity,
                    field_path,
                    array_index,
                    syntax=syntax,
                    resolution=resolution,
                    target=None,
                    diagnostic=parsed_value,
                )
            )
            continue
        key = (value_identity, resolution, syntax, parsed_value.target)
        if key in seen:
            continue
        seen.add(key)
        resolved = (
            _resolve_filename_stem(parsed_value.target, bundle_root, field_path, context)
            if resolution == "filename-stem"
            else _resolve_exact_target(
                parsed_value.target,
                resolution,
                document_path,
                bundle_root,
                project_root,
                field_path,
            )
        )
        if isinstance(resolved, FileLinkDiagnostic):
            results.append(
                _result_for_diagnostic(
                    value,
                    value_identity,
                    field_path,
                    array_index,
                    syntax=syntax,
                    resolution=resolution,
                    target=parsed_value.target,
                    query=parsed_value.query,
                    fragment=parsed_value.fragment,
                    label=parsed_value.label,
                    diagnostic=resolved,
                )
            )
            continue
        results.append(
            FileLinkResult(
                value=value,
                value_identity=value_identity,
                field_path=field_path,
                array_index=array_index,
                syntax=syntax,
                resolution=resolution,
                target=parsed_value.target,
                normalized_target=resolved.normalized_target,
                resolved_path=resolved.path,
                query=parsed_value.query,
                fragment=parsed_value.fragment,
                label=parsed_value.label,
                status="valid",
                code=None,
                severity=None,
                message="",
            )
        )
    return results


def check_file_links(
    frontmatter: dict[str, Any],
    schema: dict[str, Any],
    document_path: Path,
    *,
    bundle_root: Path | None = None,
    project_root: Path | None = None,
    _context: _FileLinkContext | None = None,
) -> list[FileLinkDiagnostic]:
    """Check all ``x-okf-link`` annotations that apply to *frontmatter*.

    .. versionadded:: 0.13.0

    Args:
        frontmatter:
            Parsed document frontmatter to inspect.
        schema:
            JSON Schema containing optional ``x-okf-link`` annotations.
        document_path:
            Markdown document whose frontmatter is being checked.
        bundle_root:
            Bundle root for bundle-relative and filename-stem references.
        project_root:
            Explicit project root for project-relative references. When it is
            unavailable, the containing Git root of *document_path* is used.

    Returns:
        Errors for malformed annotations, missing exact targets, missing or
        ambiguous stems, and root escapes; warnings for checks that cannot be
        resolved because a root or matching candidate is unavailable.

    .. versionchanged:: 0.13.0
        Local ``$ref`` targets and applicable union branches are followed
        while checking annotations. ``bundle-relative-stem`` resolves an exact
        extensionless bundle Markdown path by appending ``.md``.

    Examples:
        >>> check_file_links({}, {"type": "object"}, Path("note.md"))
        []
    """
    # @implements_req SwRS-OKFSCHEMA-CORE-007
    return [
        FileLinkDiagnostic(result.severity, result.code, result.message, result.field_path)
        for result in inspect_file_links(
            frontmatter,
            schema,
            document_path,
            bundle_root=bundle_root,
            project_root=project_root,
            _context=_context,
        )
        if result.severity is not None and result.code is not None
    ]
