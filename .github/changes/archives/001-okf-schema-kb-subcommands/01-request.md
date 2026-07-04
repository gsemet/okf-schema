# Change Request — okf-schema-kb-subcommands

**JIRA**: none
**Date**: 2026-07-03

## Summary

Add `okf-schema kb` as a dedicated subcommand group (with alias `okfkb`) for
managing OKF knowledge-base bundles — a specialised OKF bundle structure
designed for agent-facing experimental-findings traceability. The initial
command is `okfkb init [PATH]`, which scaffolds the canonical KB folder layout.
Bundled skills (`record-finding`, `consolidate-knowledge-base`) and guidelines
are packaged inside the wheel and installable into target projects via a CLI
command.

## Full Description

### 1 — `okf-schema kb` subcommand group

- New Click group `kb` registered under the main `okf-schema` CLI.
- Alias `okfkb` exposed as an independent console-script entry point that
  delegates to `okf-schema kb`.

### 2 — `okfkb init [PATH]`

- Scaffolds the knowledge-base folder structure found in:
  `/Users/az02065/Projects/DevTools/copilot-session-usage/knowledge`
- Equivalent to `okf-schema init --pattern kb [PATH]`.

### 3 — `--pattern kb` flag on `okf-schema init`

- Extends the existing `okf-schema init` command with an optional
  `--pattern <name>` flag.
- When `--pattern kb` is passed, runs the same scaffold as `okfkb init`.

### 4 — Bundled skills + guidelines

Source assets to bundle (kept in a dedicated package directory, loaded via
importlib):
- `copilot-session-usage/.github/skills/consolidate-knowledge-base/`
- `copilot-session-usage/.github/skills/record-finding/`
- `copilot-session-usage/.github/guidelines/knowledge-base.guidelines.md`

Install target (new CLI command `okfkb install-skills [PATH]` or similar):
- Skills → `.agents/skills/` (or `.github/skills/` if `.agents/` absent)
- Guideline → `.agents/guidelines/` (or `.github/guidelines/`)
- Auto-patch AGENTS.md to reference the installed guideline.

### 5 — Knowledge-base concept

A KB bundle is an OKF bundle of a special type where:
- Experimental findings are recorded with metadata.
- Findings can be analysed, synthesised (promoted), or rejected.
- Full traceability is maintained for any future operation.
