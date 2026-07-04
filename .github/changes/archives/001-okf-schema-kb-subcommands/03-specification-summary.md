# Specification Summary: OKF Knowledge Base Subcommand Group

**JIRA**: none

## What This Change Brings

This change adds `okf-schema kb`, a dedicated CLI subcommand group for managing a specialised
OKF bundle type called a "knowledge base." The `okfkb` alias makes the group reachable as a
first-class command. A knowledge base is an opinionated, agent-targeted bundle where
experimental findings are recorded, analysed, synthesised into stable knowledge artefacts
(Concepts, Principles, Structures), or rejected — all with full traceability.

Two commands ship in this release: `okfkb init [PATH]` scaffolds the canonical 10-entry KB
folder layout (8 schema files, 8 content directories, `index.md`, `log.md`), and
`okfkb install [PATH]` deploys the bundled `record-finding` and
`consolidate-knowledge-base` skills plus a project guideline into any target project,
auto-creating or patching `AGENTS.md` as needed.

The existing `okf-schema init` command is extended with an extensible `--pattern <name>`
flag; `--pattern kb` is the first pattern, delegating to the same scaffold as `okfkb init`.
All bundled assets live inside the wheel as package data and are loaded via
`importlib.resources`.

## StRS Impact Analysis

| Aspect | Details |
|--------|---------|
| **Impacted existing requirements** | None |
| **New requirements proposed** | None |
| **Severity** | none |

No StRS impact detected.

## Advantages

- Turns the proven `copilot-session-usage` knowledge-base pattern into a reusable,
  installable tool available to any project via `pip install okf-schema`.
- `--pattern kb` adds future extensibility to `okf-schema init` without breaking
  existing behaviour.
- Bundled skills are immediately useful after install — no manual copy-paste required.
- Minimal AGENTS.md creation ensures the guideline is always referenced even in fresh
  projects.

## Drawbacks / Trade-offs

- Adds a new `src/okf_schema/data/kb/` data directory to the wheel, increasing install
  size slightly (~15 KB of YAML + Markdown).
- The 96% coverage bar means every edge case of the install logic (conflict, force,
  missing AGENTS.md) must be exercised in tests.

## User Journeys (summarized)

- **Bootstrap a new KB**: A developer runs `okfkb init knowledge/` and gets a fully
  structured, schema-validated knowledge base ready for agent use in seconds.
- **Install KB tooling into a project**: A developer runs `okfkb install .` and the
  `record-finding` and `consolidate-knowledge-base` skills plus the guideline are
  deployed under `.agents/`, with AGENTS.md updated automatically.
- **okf-schema init --pattern kb**: A developer already familiar with `okf-schema init`
  runs it with `--pattern kb` and gets the same KB scaffold without learning a new
  entry point.

## Estimated Cost

<details>
<summary>Click to expand cost estimation details</summary>

| Mode        | Tasks | Cost      |
|-------------|-------|-----------|
| Fast-Middle | ~14   | ~14 GU    |
| Safe-Middle | ~14   | ~21 GU    |

**Recommended**: Safe-Middle — greenfield subpackage, bundled-data pipeline, and filesystem
mutations warrant extra review gates.

</details>
