"""Check opt-in ``x-okf-link`` annotations in JSON Schema documents.

The annotation is deliberately separate from JSON Schema validation. It
describes how a string value names a Markdown or project file, while the
standard validator continues to enforce only the schema's normal keywords.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path, PureWindowsPath
from typing import Any, Literal

from jsonschema import Draft202012Validator

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
    code: str
    message: str
    field_path: str


def _field_path(path: tuple[str | int, ...]) -> str:
    result = ""
    for part in path:
        if isinstance(part, int):
            result += f"[{part}]"
        else:
            result += f".{part}" if result else part
    return result or "<root>"


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
        return bool(validator.evolve(schema=branch).is_valid(value))
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
) -> Iterator[tuple[Any, Any, str]]:
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
        yield schema["x-okf-link"], value, _field_path(path)

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
) -> str | FileLinkDiagnostic:
    if not isinstance(value, str):
        return _error(field_path, "file-link value must be a string")
    if syntax == "plain":
        return value
    if not value.startswith("[[") or not value.endswith("]]"):
        return _error(
            field_path,
            "wikilink value must use [[target]], [[target#fragment]], or [[target|label]] syntax",
        )

    content = value[2:-2]
    target_with_fragment = content.split("|", 1)[0].strip()
    target = target_with_fragment.split("#", 1)[0].strip()
    if not target:
        return _error(field_path, "wikilink target is empty")
    return target


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


def _check_exact_target(
    target: str,
    resolution: str,
    document_path: Path,
    bundle_root: Path | None,
    project_root: Path | None,
    field_path: str,
) -> FileLinkDiagnostic | None:
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
    candidate = (root / filename).resolve(strict=False)
    if resolution != "document-relative" and not _within(candidate, root):
        return _error(field_path, f"target '{target}' escapes its {resolution} root")
    if not candidate.is_file():
        return _error(field_path, f"target '{target}' does not resolve to a file")
    return None


def _check_filename_stem(
    target: str,
    bundle_root: Path | None,
    field_path: str,
) -> FileLinkDiagnostic | None:
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
    for candidate in root.rglob("*.md"):
        if candidate.stem != target or not candidate.is_file():
            continue
        try:
            resolved = candidate.resolve()
        except OSError:
            continue
        if _within(resolved, root):
            matches.append(resolved)

    if not matches:
        return _skipped(
            field_path,
            f"no Markdown file with basename '{target}' was found in the bundle; "
            "the workspace may be unavailable",
        )
    if len(matches) > 1:
        locations = ", ".join(str(path.relative_to(root)) for path in sorted(matches))
        return _error(
            field_path,
            f"filename stem '{target}' is ambiguous in the bundle ({locations})",
        )
    return None


def check_file_links(
    frontmatter: dict[str, Any],
    schema: dict[str, Any],
    document_path: Path,
    *,
    bundle_root: Path | None = None,
    project_root: Path | None = None,
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
        Errors for malformed annotations, missing exact targets, ambiguous
        stems, and root escapes; warnings for checks that cannot be resolved
        without an available root or workspace.

    .. versionchanged:: 0.13.0
        Local ``$ref`` targets and applicable union branches are followed
        while checking annotations. ``bundle-relative-stem`` resolves an exact
        extensionless bundle Markdown path by appending ``.md``.

    Examples:
        >>> check_file_links({}, {"type": "object"}, Path("note.md"))
        []
    """
    # @implements_req SwRS-OKFSCHEMA-CORE-007
    diagnostics: list[FileLinkDiagnostic] = []
    seen: set[tuple[str, str, str]] = set()
    try:
        validator: Any | None = Draft202012Validator(schema)
    except Exception:  # noqa: BLE001
        validator = None
    for annotation, value, field_path in _iter_annotations(
        schema,
        frontmatter,
        validator=validator,
    ):
        parsed_annotation = _parse_annotation(annotation, field_path)
        if isinstance(parsed_annotation, FileLinkDiagnostic):
            diagnostics.append(parsed_annotation)
            continue
        resolution, syntax = parsed_annotation
        parsed_value = _parse_value(value, syntax, field_path)
        if isinstance(parsed_value, FileLinkDiagnostic):
            diagnostics.append(parsed_value)
            continue
        key = (field_path, resolution, parsed_value)
        if key in seen:
            continue
        seen.add(key)
        if resolution == "filename-stem":
            diagnostic = _check_filename_stem(parsed_value, bundle_root, field_path)
        else:
            diagnostic = _check_exact_target(
                parsed_value,
                resolution,
                document_path,
                bundle_root,
                project_root,
                field_path,
            )
        if diagnostic is not None:
            diagnostics.append(diagnostic)
    return diagnostics
