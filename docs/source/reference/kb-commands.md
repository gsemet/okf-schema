# Knowledge Base Commands

The `kb` subcommand group (also available as the standalone `okfkb` command) provides tools
for managing OKF knowledge-base bundles — an opinionated bundle type designed for
agent-facing experimental findings.

```bash
okfkb init [PATH]              # Scaffold a new knowledge base
okfkb install-skills [PATH]    # Install skills and guidelines
okfkb new-finding [PATH]       # Record a new Finding
okfkb update [PATH]            # Regenerate indexes and lint frontmatter
okfkb validate [PATH]          # Validate bundle (strict mode)
okfkb search TEXT [PATH]       # Ranked keyword/fuzzy search
okfkb get ID [PATH]            # Exact fetch of one node by id/path
okfkb read TIER [PATH]         # Read a whole stable tier
okfkb query EXPR [PATH]        # Structured query (filter DSL + graph traversal)
```

`okfkb` is a standalone alias; `okf-schema kb <cmd>` and `okfkb <cmd>` are strictly equivalent.

## `okfkb init`

Scaffold a canonical knowledge-base folder layout with 8 content directories,
8 schema YAML files, `index.md`, and `log.md`.

```bash
okfkb init [PATH]
```

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `PATH` | — | `.` (current directory) | Destination directory for the new knowledge base. |

| Option | Description |
|--------|-------------|
| `--force` | Overwrite an existing non-empty directory. |

**Scaffolded layout:**

```
<PATH>/
├── _schema/
│   ├── Base.schema.yaml
│   ├── Concept.schema.yaml
│   ├── Experiment.schema.yaml
│   ├── Finding.schema.yaml
│   ├── Playbook.schema.yaml
│   ├── Principle.schema.yaml
│   ├── Reference.schema.yaml
│   ├── Structure.schema.yaml
│   ├── Hypothesis.schema.yaml
│   └── Outcome.schema.yaml
├── concepts/
├── experiments/
├── findings/
├── guides/
├── hypotheses/
├── outcomes/
├── principles/
├── reference/
├── structures/
├── index.md
└── log.md
```

The same scaffold is available through the `--pattern` flag on `okf-schema init`:

```bash
okf-schema init my-kb --pattern kb
```

## `okfkb install-skills`

Deploy the bundled `record-finding` and `consolidate-knowledge-base` skills, plus the
`knowledge-base.guidelines.md` guideline, into a target project directory.
Patches or creates `AGENTS.md` to reference the installed guideline.

```bash
okfkb install-skills [PATH]
```

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `PATH` | — | `.` (current directory) | Target project root. |

| Option | Description |
|--------|-------------|
| `--force` | Overwrite existing skill/guideline files (default: skip). |

**Install behaviour:**

- Detects whether `PATH/.agents/` or `PATH/.github/` exists; prefers `.agents/`; falls back
  to `.github/`; creates `.agents/` if neither exists.
- Copies skills to `<base>/skills/` and the guideline to `<base>/guidelines/`.
- Existing files are skipped (with a warning) unless `--force` is passed.
- `AGENTS.md` patching is always idempotent — the guideline reference is never duplicated.

## `okfkb new-finding`

Record a new empirical Finding in the KB bundle at PATH. Generates a timestamped,
schema-valid markdown file under `PATH/findings/` with the filename pattern
`YYYY.MM.DD-HH.MM-<slug>.md`.

```bash
okfkb new-finding [PATH] --title TEXT [OPTIONS]
```

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `PATH` | — | `.` (current directory) | KB root directory. |

| Option | Required | Default | Description |
|--------|----------|---------|-------------|
| `--title`, `-t` | **yes** | — | Short human-readable title. |
| `--description`, `-d` | no | *(title)* | One-line summary (defaults to title). |
| `--confidence`, `-c` | no | `low` | Confidence level: `low`, `medium`, `high`, or `confirmed`. |
| `--context` | no | `"No additional context recorded."` | Background and assumptions at recording time. |
| `--tags` | no | *(empty)* | Comma-separated keyword tags. |

**Example:**

```bash
okfkb new-finding my-kb/ \
  --title "Cache eviction too aggressive" \
  --confidence medium \
  --context "Observed under 500 RPS load; eviction rate 3× higher than expected." \
  --tags "cache,performance,memory"
```

**Generated file** (`my-kb/findings/2026.07.04-14.30-cache-eviction-too-aggressive.md`):

```yaml
---
type: Finding
title: Cache eviction too aggressive
description: Cache eviction too aggressive
confidence: medium
context: Observed under 500 RPS load; eviction rate 3× higher than expected.
timestamp: 2026-07-04T14:30:00Z
tags:
- cache
- performance
- memory
links: []
backlinks: []
status: active
---

# Finding: Cache eviction too aggressive

## Observation

<!-- Describe what you observed. -->

## Evidence

<!-- Add supporting evidence, logs, or test results. -->

## Implications

<!-- What does this mean? What should change? -->
```

**Filename convention:** The slug is derived from the title by lower-casing, replacing non-alphanumeric
runs with `-`, and truncating at 60 characters. The timestamp uses the current UTC time.

## `okfkb update`

Regenerate all `index.md` files and lint frontmatter in a knowledge base.
This is equivalent to running `okf-schema index` followed by `okf-schema lint`
— the recommended workflow after editing concepts.

```bash
okfkb update [PATH]
```

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `PATH` | — | `.` (current directory) | KB root directory. |

| Option | Description |
|--------|-------------|
| `--check` | Report what would change without modifying files. |
| `--diff` | Show unified diff for lint changes without modifying files. |
| `--links` / `--no-links` | Update `links` and `backlinks` frontmatter fields (default: `--links`). |

**Example:**

```bash
okfkb update my-kb/
okfkb update my-kb/ --check
```

**Output:**

```
Index: 2 updated, 1 created, 5 unchanged, 0 skipped
Linted: concepts/test.md
Linted 1 file(s).
```

## `okfkb validate`

Validate a knowledge base bundle with strict mode (warnings treated as errors).
This is equivalent to running ``okf-schema validate --strict``.

```bash
okfkb validate [PATH]
```

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `PATH` | — | `.` (current directory) | KB root directory. |

**Example:**

```bash
okfkb validate my-kb/
```

**Output (valid):**

```
Bundle is conformant (0 errors, 0 warnings).
```

**Output (invalid):**

```
my-kb/concepts/missing-frontmatter.md
  WARNING [W1] Missing frontmatter

Validation failed: 0 error(s), 1 warning(s) (strict mode).
```

## Navigating the KB

`okfkb` exposes the knowledge base as a small set of **navigation tools**, so an agent (or
human) can actively pull the right granularity instead of loading whole tier folders into
context. The four commands mirror a natural drill-down:

| Command | Role |
|---------|------|
| `okfkb search` | Coarse ranked retrieval — "where might the answer be?" |
| `okfkb get` | Exact fetch of one node — "show me exactly this." |
| `okfkb read` | Read a whole stable tier — "give me the settled understanding." |
| `okfkb query` | Structured selection & graph traversal — "select by criteria / follow links." |

A typical top-down navigation is: `read principles` → `read concepts` → `query`/`search` to
locate supporting findings → `get` a specific finding for evidence-level detail.

## `okfkb search`

Ranked keyword / fuzzy search across node titles, `context`, `tags`, and body text. Returns a
compact list of matches (tier, id, title, confidence) for follow-up `get`.

```bash
okfkb search TEXT [PATH] [OPTIONS]
```

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `TEXT` | **yes** | — | Free-text query. |
| `PATH` | — | `.` (current directory) | KB root directory. |

| Option | Description |
|--------|-------------|
| `--tier TIER` | Restrict search to one tier (`findings`, `concepts`, `principles`, …). Repeatable. |
| `--limit N` | Maximum number of results (default: `10`). |
| `--format table\|json\|paths` | Output format (default: `table`). |

**Example:**

```bash
okfkb search "pll lock time" my-kb/ --tier findings --limit 5
```

## `okfkb get`

Fetch a single node by its id or bundle-relative path and print it. This is the exact
drill-down after a `search` or `query`.

```bash
okfkb get ID [PATH] [OPTIONS]
```

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `ID` | **yes** | — | Node id or bundle-relative path (e.g. `findings/2026.07.03-14.20-pll-temp-drift.md`). |
| `PATH` | — | `.` (current directory) | KB root directory. |

| Option | Description |
|--------|-------------|
| `--format md\|json\|frontmatter` | What to print: full markdown, JSON node, or frontmatter only (default: `md`). |

**Example:**

```bash
okfkb get findings/2026.07.03-14.20-pll-temp-drift.md my-kb/ --format frontmatter
```

## `okfkb read`

Read an entire stable tier at once — a fast top-down entry point. Concatenates the nodes of a
tier (optionally filtered by status) so an agent can absorb the settled understanding before
descending to evidence.

```bash
okfkb read TIER [PATH] [OPTIONS]
```

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `TIER` | **yes** | — | Tier name: `concepts`, `principles`, `structures`, `findings`, … |
| `PATH` | — | `.` (current directory) | KB root directory. |

| Option | Description |
|--------|-------------|
| `--status STATUS` | Only include nodes with this `status` (e.g. `active`, `resolved`). |
| `--format md\|frontmatter\|titles` | Full markdown, frontmatter only, or a title index (default: `md`). |

**Example:**

```bash
okfkb read concepts my-kb/ --status active
okfkb read principles my-kb/ --format titles
```

## `okfkb query`

Structured selection over the KB. `query` combines two complementary styles that can be used
independently: a flat **filter DSL** for frontmatter, and an **arrow traversal** for following
the `links` / `backlinks` / promotion graph (a lightweight, Cypher-inspired path syntax).

```bash
okfkb query EXPR [PATH] [OPTIONS]
```

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `EXPR` | **yes** | — | A filter expression or a traversal path (see below). |
| `PATH` | — | `.` (current directory) | KB root directory. |

| Option | Description |
|--------|-------------|
| `--format table\|json\|paths` | Output format (default: `table`). |
| `--limit N` | Maximum number of results. |

### Filter DSL (flat frontmatter selection)

Space-separated `key:value` or `key:op:value` terms, all **ANDed** together.

| Key | Matches |
|-----|---------|
| `type` / `tier` | Node type / tier (`finding`, `concept`, `principle`, …) |
| `confidence` | Ordinal: `low` < `medium` < `high` < `confirmed` — supports ranges |
| `status` | `active`, `contradicted`, `resolved`, … |
| `tag` | Membership in the `tags` array |
| `title` | Substring / regex match on the title |
| `since` / `until` | Timestamp bounds (ISO date) |

| Operator | Meaning |
|----------|---------|
| `:` | equals (or *contains*, for list fields like `tags`) |
| `>=` `<=` `>` `<` | ordered comparison (confidence, timestamps) |
| `!=` | not equal |
| `~` | substring / regex match |

```bash
# High-confidence, active PLL findings
okfkb query "type:finding confidence:>=high tag:pll status:active"

# Concepts whose title mentions "boot", created since July
okfkb query "type:concept title:~boot since:2026-07-01"
```

### Arrow traversal (pocket-Cypher over the link graph)

A start-set node (with an optional inline filter in `[...]`) followed by one or more hops.
Each node label is a tier name; hops follow graph edges:

| Hop | Follows |
|-----|---------|
| `->` | outgoing `links` |
| `<-` | incoming `backlinks` |
| `^` | promotion edge (`promoted_from`: finding → concept) |

Inline filters accept `=`, `>=`, `<=`, `~` (e.g. `[tag=pll,confidence=high]`).

```bash
# From high-confidence PLL findings, walk up to concepts, then principles
okfkb query "finding[tag=pll,confidence=high] -> concept -> principle"

# Which findings back a concept about boot?
okfkb query "concept[title~boot] <- finding"

# Findings promoted into concepts
okfkb query "finding[status=active] ^ concept"
```

The result is the set of nodes reached by the **final** hop, printed as a table (tier, id,
title, confidence, status) or as `--format json` / `paths`.

> **Evolving syntax.** The `query` grammar is intentionally small and may still
> evolve. The filter DSL and arrow traversal cover the common day-to-day needs; a
> fuller `MATCH … RETURN` grammar may be added later if the arrow form proves too
> limiting.

## `okf-schema kb`

The `kb` subcommand group is also registered directly on the top-level `okf-schema` CLI:

```bash
okf-schema kb --help
okf-schema kb init [PATH]
okf-schema kb install-skills [PATH]
okf-schema kb new-finding [PATH] --title TEXT
okf-schema kb update [PATH]
okf-schema kb validate [PATH]
```

This is identical to `okfkb`; use whichever form is more convenient.

## See also

- [Bootstrap a Knowledge Base](../how-to/bootstrap-knowledge-base) — step-by-step guide to setting up a KB.
- [Why an Opinionated Knowledge Base?](../explanation/okfkb-choices) — design rationale behind the KB structure.
- [CLI Reference](cli) — full reference for all `okf-schema` commands.
- [Getting Started](../tutorials/getting-started) — broader tutorial on OKF bundles.
