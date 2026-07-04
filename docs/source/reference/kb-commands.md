# Knowledge Base Commands

The `kb` subcommand group (also available as the standalone `okfkb` command) provides tools
for managing OKF knowledge-base bundles — an opinionated bundle type designed for
agent-facing experimental findings.

```bash
okfkb init [PATH]              # Scaffold a new knowledge base
okfkb install-skills [PATH]    # Install skills and guidelines
okfkb new-finding [PATH]       # Record a new Finding
```

`okfkb` is a standalone alias; `okf-schema kb <cmd>` and `okfkb <cmd>` are strictly equivalent.

---

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
│   └── Structure.schema.yaml
├── concepts/
├── experiments/
├── findings/
├── guides/
├── ideas/
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

---

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

---

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

---

## `okf-schema kb`

The `kb` subcommand group is also registered directly on the top-level `okf-schema` CLI:

```bash
okf-schema kb --help
okf-schema kb init [PATH]
okf-schema kb install-skills [PATH]
okf-schema kb new-finding [PATH] --title TEXT
```

This is identical to `okfkb`; use whichever form is more convenient.
