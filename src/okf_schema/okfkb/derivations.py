"""Compute canonical reciprocal derivation links for OKFKB bundles.

OKFKB authors maintain ``derived_from`` using bundle-relative, extensionless
document paths. The maintenance tooling materializes the reverse
``derives_to`` field so agents can traverse provenance in either direction
from frontmatter alone.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from okf_schema._internal.utils import RESERVED_FILES, collect_markdown_files
from okf_schema._internal.yaml import extract_frontmatter, make_yaml, parse_yaml

DERIVATION_COMMENT = "knowledge graph fields generated automatically — do not edit manually"


@dataclass(frozen=True)
class InvalidDerivation:
    """An authored ``derived_from`` value that is not a canonical document ID."""

    document_id: str
    source_id: str


@dataclass(frozen=True)
class DerivationGraph:
    """Expected reverse edges and invalid authored derivation references."""

    derives_to: dict[str, list[str]]
    invalid: list[InvalidDerivation]


def document_id(path: Path, bundle: Path) -> str:
    """Return the canonical extensionless bundle-relative ID for *path*."""
    return path.relative_to(bundle).with_suffix("").as_posix()


def supports_derivation_graph(bundle: Path) -> bool:
    """Return whether *bundle* advertises the OKFKB derivation contract."""
    schema_path = bundle / "_schema" / "Base.schema.yaml"
    if not schema_path.is_file():
        return False
    try:
        data = make_yaml().load(schema_path.read_text(encoding="utf-8"))
    except OSError:
        return False
    if not isinstance(data, dict):
        return False
    properties = data.get("properties")
    return isinstance(properties, dict) and {
        "derived_from",
        "derives_to",
    }.issubset(properties)


def _load_frontmatter(path: Path) -> dict:
    """Load mapping frontmatter from *path*, returning an empty mapping on failure."""
    fm_text, _body = extract_frontmatter(path.read_text(encoding="utf-8"))
    if fm_text is None:
        return {}
    parsed = parse_yaml(fm_text)
    return parsed if isinstance(parsed, dict) else {}


def _content_documents(bundle: Path) -> dict[str, Path]:
    """Return canonical IDs mapped to content document paths."""
    documents: dict[str, Path] = {}
    for path in collect_markdown_files(bundle):
        if path.name in RESERVED_FILES or "_schema" in path.relative_to(bundle).parts:
            continue
        documents[document_id(path, bundle)] = path
    return documents


# @implements_req SwRS-OKFSCHEMA-OKFKB-006
def build_derivation_graph(bundle: Path) -> DerivationGraph:
    """Compute ``derives_to`` from authored canonical ``derived_from`` paths.

    Unknown, non-canonical, and malformed source references are excluded from
    the computed graph and returned in :attr:`DerivationGraph.invalid` for
    read-only validation to report.
    """
    documents = _content_documents(bundle)
    reverse: dict[str, list[str]] = {identifier: [] for identifier in documents}
    invalid: list[InvalidDerivation] = []

    for target_id, path in documents.items():
        authored = _load_frontmatter(path).get("derived_from")
        if authored is None:
            continue
        if not isinstance(authored, list):
            invalid.append(InvalidDerivation(target_id, str(authored)))
            continue
        for raw_source in authored:
            source_id = str(raw_source).strip()
            if not source_id or source_id not in documents:
                invalid.append(InvalidDerivation(target_id, source_id))
                continue
            reverse[source_id].append(target_id)

    for targets in reverse.values():
        targets[:] = sorted(set(targets))
    invalid.sort(key=lambda item: (item.document_id, item.source_id))
    return DerivationGraph(derives_to=reverse, invalid=invalid)


def content_document_paths(bundle: Path) -> dict[str, Path]:
    """Expose canonical content-document paths for linting and validation."""
    return _content_documents(bundle)
