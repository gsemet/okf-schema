"""Navigation and query engine for OKF knowledge-base bundles.

Implements the ``search`` / ``get`` / ``read`` / ``query`` navigation tools
exposed by the ``okfkb`` CLI. These let an agent actively pull the right
granularity from a stratified KB instead of loading whole tier folders.

The ``query`` engine supports two complementary styles:

* **Filter DSL** — flat frontmatter selection, e.g.
  ``type:finding confidence:>=high tag:pll status:active``.
* **Arrow traversal** — a pocket-Cypher over the ``links`` / ``backlinks`` /
  ``promoted_from`` graph, e.g.
  ``finding[tag=pll,confidence=high] -> concept -> principle``.
"""

from __future__ import annotations

import operator
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from okf_schema._internal.utils import RESERVED_FILES, collect_markdown_files
from okf_schema._internal.yaml import extract_frontmatter, parse_yaml

# Ordinal ranking for confidence comparisons (low < medium < high < confirmed).
_CONFIDENCE_ORDER = {"low": 0, "medium": 1, "high": 2, "confirmed": 3}

# Ordered comparison operators, used for numeric and lexical fallbacks.
_ORDERED_OPS: dict[str, Callable[[float | str, float | str], bool]] = {
    ">=": operator.ge,
    "<=": operator.le,
    ">": operator.gt,
    "<": operator.lt,
}

# Canonical tier folders in a KB bundle.
_TIER_FOLDERS = (
    "concepts",
    "experiments",
    "findings",
    "guides",
    "hypotheses",
    "outcomes",
    "principles",
    "reference",
    "structures",
)

# Map singular/plural/type aliases to the canonical tier folder name.
_TIER_ALIASES: dict[str, str] = {}
for _folder in _TIER_FOLDERS:
    _TIER_ALIASES[_folder] = _folder
    _singular = _folder[:-1] if _folder.endswith("s") else _folder
    _TIER_ALIASES[_singular] = _folder
# Irregular / explicit aliases.
_TIER_ALIASES.update(
    {
        "hypothesis": "hypotheses",
        "hypotheses": "hypotheses",
        "reference": "reference",
        "references": "reference",
        "ref": "reference",
    }
)


@dataclass
class KbNode:
    """A single knowledge-base node (one markdown file with frontmatter)."""

    path: str
    tier: str
    type: str
    title: str
    confidence: str
    status: str
    tags: list[str]
    timestamp: str
    frontmatter: dict
    body: str

    def links(self) -> list[str]:
        """Return outgoing ``links`` as bundle-relative paths."""
        return _as_str_list(self.frontmatter.get("links"))

    def backlinks(self) -> list[str]:
        """Return incoming ``backlinks`` as bundle-relative paths."""
        return _as_str_list(self.frontmatter.get("backlinks"))

    def promoted_from(self) -> list[str]:
        """Return promotion sources (``promoted_from``) as paths."""
        return _as_str_list(self.frontmatter.get("promoted_from"))


def _as_str_list(value: object) -> list[str]:
    """Coerce a frontmatter value into a list of stripped strings."""
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    text = str(value).strip()
    return [text] if text else []


def normalize_tier(label: str) -> str:
    """Resolve a tier *label* (singular/plural/type) to its folder name.

    Raises:
        ValueError: When *label* does not map to a known tier.
    """
    key = label.strip().lower()
    if key in _TIER_ALIASES:
        return _TIER_ALIASES[key]
    raise ValueError(f"Unknown tier {label!r}. Valid tiers: {', '.join(_TIER_FOLDERS)}.")


def _load_node(path: Path, bundle: Path) -> KbNode | None:
    """Load a single :class:`KbNode` from *path*, or ``None`` to skip it."""
    if path.name in RESERVED_FILES:
        return None
    rel = path.relative_to(bundle).as_posix()
    parts = rel.split("/")
    if parts[0] == "_schema":
        return None
    tier = parts[0] if len(parts) > 1 else ""

    text = path.read_text(encoding="utf-8")
    fm_text, body = extract_frontmatter(text)
    frontmatter: dict = {}
    if fm_text is not None:
        parsed = parse_yaml(fm_text)
        if isinstance(parsed, dict):
            frontmatter = parsed

    return KbNode(
        path=rel,
        tier=tier,
        type=str(frontmatter.get("type", "")).strip(),
        title=str(frontmatter.get("title", path.stem)).strip(),
        confidence=str(frontmatter.get("confidence", "")).strip(),
        status=str(frontmatter.get("status", "")).strip(),
        tags=_as_str_list(frontmatter.get("tags")),
        timestamp=str(frontmatter.get("timestamp", "")).strip(),
        frontmatter=frontmatter,
        body=body,
    )


def load_nodes(bundle: Path) -> list[KbNode]:
    """Load every content node in *bundle* (excludes reserved/schema files)."""
    nodes: list[KbNode] = []
    for path in collect_markdown_files(bundle):
        node = _load_node(path, bundle)
        if node is not None:
            nodes.append(node)
    return nodes


# ---------------------------------------------------------------------------
# search
# ---------------------------------------------------------------------------


@dataclass
class SearchHit:
    """A ranked search result over a KB bundle."""

    node: KbNode
    score: int


def search(
    bundle: Path,
    text: str,
    *,
    tiers: list[str] | None = None,
    limit: int = 10,
) -> list[SearchHit]:
    """Rank nodes by keyword relevance to *text*.

    Matches (case-insensitive) against title, tags, type, description, and
    body, with weighted scoring. Results are sorted by descending score,
    then by path.
    """
    needle = text.strip().lower()
    if not needle:
        return []
    tier_filter = {normalize_tier(t) for t in tiers} if tiers else None

    hits: list[SearchHit] = []
    for node in load_nodes(bundle):
        if tier_filter is not None and node.tier not in tier_filter:
            continue
        score = 0
        if needle in node.title.lower():
            score += 3
        score += 2 * sum(1 for tag in node.tags if needle in tag.lower())
        if needle in node.type.lower():
            score += 2
        description = str(node.frontmatter.get("description", "")).lower()
        if needle in description:
            score += 1
        context = str(node.frontmatter.get("context", "")).lower()
        if needle in context:
            score += 1
        if needle in node.body.lower():
            score += 1
        if score > 0:
            hits.append(SearchHit(node=node, score=score))

    hits.sort(key=lambda h: (-h.score, h.node.path))
    return hits[:limit] if limit and limit > 0 else hits


# ---------------------------------------------------------------------------
# get
# ---------------------------------------------------------------------------


def get(bundle: Path, node_id: str) -> KbNode:
    """Fetch a single node by id or bundle-relative path.

    The id may be given with or without the ``.md`` extension, and either as
    a full path (``findings/2026...md``) or a bare filename/stem.

    Raises:
        FileNotFoundError: When no node matches *node_id*.
    """
    wanted = node_id.strip()
    candidate = bundle / wanted
    if candidate.is_file():
        node = _load_node(candidate, bundle)
        if node is not None:
            return node

    with_ext = wanted if wanted.endswith(".md") else f"{wanted}.md"
    nodes = load_nodes(bundle)
    for node in nodes:
        if node.path == wanted or node.path == with_ext:
            return node
    # Fall back to matching by filename or stem.
    for node in nodes:
        name = node.path.rsplit("/", 1)[-1]
        if name == with_ext or name[:-3] == wanted:
            return node

    raise FileNotFoundError(f"No node matches id {node_id!r} in bundle {bundle}.")


# ---------------------------------------------------------------------------
# read
# ---------------------------------------------------------------------------


def read_tier(bundle: Path, tier: str, *, status: str | None = None) -> list[KbNode]:
    """Return all nodes in *tier*, optionally filtered by ``status``.

    Raises:
        ValueError: When *tier* is not a known tier folder.
    """
    folder = normalize_tier(tier)
    nodes = [n for n in load_nodes(bundle) if n.tier == folder]
    if status is not None:
        wanted = status.strip().lower()
        nodes = [n for n in nodes if n.status.lower() == wanted]
    nodes.sort(key=lambda n: n.path)
    return nodes


# ---------------------------------------------------------------------------
# query — filter DSL + arrow traversal
# ---------------------------------------------------------------------------

_COMPARE_OPS = (">=", "<=", "!=", ">", "<", "~")
_HOP_RE = re.compile(r"\s*(->|<-|\^)\s*")
_NODE_RE = re.compile(r"^([A-Za-z_]+)(?:\[(.*)\])?$")


@dataclass
class _Condition:
    key: str
    op: str
    value: str


@dataclass
class _NodeStep:
    tier: str | None
    conditions: list[_Condition] = field(default_factory=list)


def _split_op(term: str, *, colon_prefixed: bool) -> _Condition:
    """Parse a single ``key op value`` term into a :class:`_Condition`.

    When *colon_prefixed* is ``True`` the syntax is ``key:value`` /
    ``key:<op>value`` (filter DSL). Otherwise it is ``key<op>value`` /
    ``key=value`` (inline traversal filter).
    """
    if colon_prefixed:
        if ":" not in term:
            raise ValueError(f"Invalid filter term {term!r} (expected key:value).")
        key, rest = term.split(":", 1)
        for op in _COMPARE_OPS:
            if rest.startswith(op):
                return _Condition(key.strip().lower(), op, rest[len(op) :].strip())
        return _Condition(key.strip().lower(), "=", rest.strip())

    for op in _COMPARE_OPS:
        if op in term:
            key, value = term.split(op, 1)
            return _Condition(key.strip().lower(), op, value.strip())
    if "=" in term:
        key, value = term.split("=", 1)
        return _Condition(key.strip().lower(), "=", value.strip())
    raise ValueError(f"Invalid inline filter {term!r} (expected key=value).")


def _parse_node_step(token: str) -> _NodeStep:
    """Parse a traversal node token such as ``finding[tag=pll,confidence=high]``."""
    match = _NODE_RE.match(token.strip())
    if match is None:
        raise ValueError(f"Invalid node expression {token!r}.")
    label, inner = match.group(1), match.group(2)
    tier = normalize_tier(label)
    conditions: list[_Condition] = []
    if inner:
        for part in inner.split(","):
            part = part.strip()
            if part:
                conditions.append(_split_op(part, colon_prefixed=False))
    return _NodeStep(tier=tier, conditions=conditions)


def _compare(node: KbNode, cond: _Condition) -> bool:
    """Evaluate a single condition against *node*."""
    key = cond.key
    op = cond.op
    value = cond.value

    if key in ("type", "tier"):
        if op in ("=", "~"):
            target = value.lower()
            if op == "~":
                return target in node.tier.lower() or target in node.type.lower()
            return node.tier == normalize_tier(value) or node.type.lower() == target
        return False

    if key == "tag":
        tags = [t.lower() for t in node.tags]
        if op == "~":
            return any(value.lower() in t for t in tags)
        return value.lower() in tags

    if key == "confidence":
        return _compare_confidence(node.confidence, op, value)

    if key in ("since", "until"):
        stamp = node.timestamp
        if not stamp:
            return False
        return stamp >= value if key == "since" else stamp <= value

    # Generic frontmatter scalar (status, title, timestamp, description, ...).
    raw = node.frontmatter.get(key)
    if raw is None and key == "title":
        raw = node.title
    if isinstance(raw, list):
        items = [str(v).lower() for v in raw]
        return value.lower() in items if op in ("=", "~") else False
    text = "" if raw is None else str(raw)
    return _compare_scalar(text, op, value)


def _compare_confidence(node_value: str, op: str, value: str) -> bool:
    """Compare confidence using ordinal ranking for ordered operators."""
    left = _CONFIDENCE_ORDER.get(node_value.lower())
    right = _CONFIDENCE_ORDER.get(value.lower())
    if op in ("=", "~"):
        return node_value.lower() == value.lower()
    if op == "!=":
        return node_value.lower() != value.lower()
    if left is None or right is None:
        return False
    if op == ">=":
        return left >= right
    if op == "<=":
        return left <= right
    if op == ">":
        return left > right
    if op == "<":
        return left < right
    return False


def _compare_scalar(text: str, op: str, value: str) -> bool:
    """Compare a scalar string with numeric fallback for ordered operators."""
    lowered = text.lower()
    target = value.lower()
    if op == "=":
        return lowered == target
    if op == "!=":
        return lowered != target
    if op == "~":
        try:
            return re.search(value, text, re.IGNORECASE) is not None
        except re.error:
            return target in lowered
    left_num, right_num = _try_floats(text, value)
    if left_num is not None and right_num is not None:
        return _ordered(left_num, right_num, op)
    return _ordered(lowered, target, op)


def _ordered(left: float | str, right: float | str, op: str) -> bool:
    """Apply an ordered comparison operator to two same-typed values."""
    comparator = _ORDERED_OPS.get(op)
    if comparator is None:
        return False
    return comparator(left, right)


def _try_floats(a: str, b: str) -> tuple[float | None, float | None]:
    """Return both values as floats, or ``(None, None)`` if either fails."""
    try:
        return float(a), float(b)
    except (TypeError, ValueError):
        return None, None


def _matches_all(node: KbNode, conditions: list[_Condition]) -> bool:
    """Return ``True`` when *node* satisfies every condition (logical AND)."""
    return all(_compare(node, cond) for cond in conditions)


def _is_traversal(expr: str) -> bool:
    """Heuristically detect the arrow-traversal form of a query."""
    if any(tok in expr for tok in ("->", "<-", "^", "[")):
        return True
    # A bare tier label (e.g. ``finding``) is a start-set traversal.
    return expr.strip().lower() in _TIER_ALIASES


def _run_traversal(nodes: list[KbNode], expr: str) -> list[KbNode]:
    """Execute an arrow-traversal query and return the reached nodes."""
    hops = _HOP_RE.split(expr.strip())
    # hops = [node, op, node, op, node, ...]
    if not hops or not hops[0]:
        raise ValueError("Empty traversal expression.")

    by_path = {n.path: n for n in nodes}
    first = _parse_node_step(hops[0])
    current = [
        n
        for n in nodes
        if (first.tier is None or n.tier == first.tier) and _matches_all(n, first.conditions)
    ]

    i = 1
    while i < len(hops):
        op = hops[i]
        step = _parse_node_step(hops[i + 1])
        current = _apply_hop(current, op, step, by_path, nodes)
        i += 2

    # Deduplicate while preserving order, then sort by path.
    seen: set[str] = set()
    unique: list[KbNode] = []
    for node in current:
        if node.path not in seen:
            seen.add(node.path)
            unique.append(node)
    unique.sort(key=lambda n: n.path)
    return unique


def _apply_hop(
    current: list[KbNode],
    op: str,
    step: _NodeStep,
    by_path: dict[str, KbNode],
    all_nodes: list[KbNode],
) -> list[KbNode]:
    """Apply a single traversal hop and filter to *step*'s tier/conditions."""
    reached: list[KbNode] = []
    if op == "->":
        for node in current:
            for target in node.links():
                if target in by_path:
                    reached.append(by_path[target])
    elif op == "<-":
        for node in current:
            for source in node.backlinks():
                if source in by_path:
                    reached.append(by_path[source])
    elif op == "^":
        # Promotion: find nodes whose promoted_from references a current node.
        current_paths = {n.path for n in current}
        for candidate in all_nodes:
            if current_paths.intersection(candidate.promoted_from()):
                reached.append(candidate)
    else:  # pragma: no cover - guarded by regex
        raise ValueError(f"Unknown hop operator {op!r}.")

    return [
        n
        for n in reached
        if (step.tier is None or n.tier == step.tier) and _matches_all(n, step.conditions)
    ]


def query(bundle: Path, expr: str, *, limit: int | None = None) -> list[KbNode]:
    """Run a structured query over *bundle*.

    Dispatches to the arrow-traversal engine when *expr* uses ``->`` / ``<-``
    / ``^`` / ``[...]``, otherwise treats *expr* as a flat filter DSL.

    Raises:
        ValueError: When *expr* is empty or malformed.
    """
    expression = expr.strip()
    if not expression:
        raise ValueError("Empty query expression.")

    nodes = load_nodes(bundle)

    if _is_traversal(expression):
        result = _run_traversal(nodes, expression)
    else:
        conditions = [_split_op(term, colon_prefixed=True) for term in expression.split() if term]
        result = [n for n in nodes if _matches_all(n, conditions)]
        result.sort(key=lambda n: n.path)

    return result[:limit] if limit and limit > 0 else result
