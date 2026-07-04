"""Generate new Finding documents in a KB bundle."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path

from ruamel.yaml import YAML

_SLUG_RE = re.compile(r"[^a-z0-9]+")

_VALID_CONFIDENCE = frozenset({"low", "medium", "high", "confirmed"})


def _slugify(text: str) -> str:
    """Convert *text* to a URL-safe slug, capped at 60 characters."""
    return _SLUG_RE.sub("-", text.lower()).strip("-")[:60]


def new_finding(
    kb_path: Path,
    title: str,
    *,
    description: str | None = None,
    confidence: str = "low",
    context: str = "No additional context recorded.",
    tags: list[str] | None = None,
) -> Path:
    """Create a new Finding document in ``<kb_path>/findings/``.

    Generate a timestamped, schema-valid Finding file with a date-slugged
    filename of the form ``YYYY.MM.DD-HH.MM-<slug>.md``.

    Args:
        kb_path: Root directory of the knowledge base.
        title: Short human-readable title for the finding.
        description: One-line summary (defaults to *title* when omitted).
        confidence: Confidence level — ``low``, ``medium``, ``high``, or
            ``confirmed``.
        context: Background and assumptions at the time of recording.
        tags: Optional keyword tags for categorisation.

    Returns:
        Path to the created file.

    Raises:
        ValueError: When *kb_path* does not exist or *confidence* is invalid.
    """
    if not kb_path.exists():
        raise ValueError(f"KB path does not exist: {kb_path}")
    if confidence not in _VALID_CONFIDENCE:
        raise ValueError(
            f"Invalid confidence {confidence!r}. "
            f"Must be one of: {', '.join(sorted(_VALID_CONFIDENCE))}"
        )

    findings_dir = kb_path / "findings"
    findings_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc)
    date_prefix = now.strftime("%Y.%m.%d-%H.%M")
    slug = _slugify(title)
    filename = f"{date_prefix}-{slug}.md"
    filepath = findings_dir / filename

    yaml = YAML()
    yaml.default_flow_style = False
    yaml.width = 100

    frontmatter: dict[str, object] = {
        "type": "Finding",
        "title": title,
        "description": description if description is not None else title,
        "confidence": confidence,
        "context": context,
        "timestamp": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "tags": list(tags) if tags else [],
        "links": [],
        "backlinks": [],
        "status": "active",
    }

    buf = StringIO()
    yaml.dump(frontmatter, buf)
    fm_yaml = buf.getvalue().rstrip()

    content = (
        f"---\n{fm_yaml}\n---\n\n"
        f"# Finding: {title}\n\n"
        "## Observation\n\n"
        "<!-- Describe what you observed. -->\n\n"
        "## Evidence\n\n"
        "<!-- Add supporting evidence, logs, or test results. -->\n\n"
        "## Implications\n\n"
        "<!-- What does this mean? What should change? -->\n"
    )

    filepath.write_text(content, encoding="utf-8")
    return filepath
