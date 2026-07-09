# Specification — okfkb-gardening Skill

**Date:** 2026-07-09
**Target:** `/Users/az02065/Projects/DevTools/okf-schema/.github/skills/okfkb-gardening/SKILL.md`
**Status:** Ready for implementation planning

---

## 1. Overview

`okfkb-gardening` is an on-demand Copilot agent skill that performs health-checking and auto-repair of an OKFKB bundle. It runs in batch mode: auto-fixing what it can, then presenting all decisions requiring human input as a single report at the end.

**Trigger phrase:** `okfkb garden /path/to/kb`

---

## 2. Deliverables

| Deliverable | Description |
|-------------|-------------|
| `SKILL.md` | Agent skill definition at `.github/skills/okfkb-gardening/SKILL.md` |
| CLI extension | Extend `okfkb update` in `src/okf_schema/kb/cli.py` to handle `superseded_by` backlink rewriting |

---

## 3. Skill Workflow (Step by Step)

```
okfkb garden /path/to/kb
    │
    ├─ Step 1: Initial validation
    │    Run: okfkb validate /path/to/kb
    │    Purpose: snapshot initial state, capture error baseline
    │
    ├─ Step 2: Link existence check
    │    For every link stored in frontmatter (links: field):
    │      - Check if the target file exists on disk
    │      - Broken? → attempt auto-fix via `git log --follow` to detect renames
    │      - Confident fix found? → auto-apply (update frontmatter)
    │      - Ambiguous / not found? → queue for user review
    │
    ├─ Step 3: okfkb update (extended)
    │    Run: okfkb update /path/to/kb
    │    Standard behavior:
    │      - Regenerate all index.md files
    │      - Normalize frontmatter (lint)
    │      - Recompute links / backlinks
    │    New behavior (CLI extension):
    │      - Scan all documents with status: superseded
    │      - Follow superseded_by: <path> field on each
    │      - Rewrite all backlinks pointing to the superseded doc → replacement path
    │      - If superseded_by is absent → defer to batch report
    │
    ├─ Step 4: Pairwise coherence checks (small model)
    │    For each document in the bundle:
    │      - Read source document + each of its linked target documents
    │      - Spawn subagent (model: Kimi K2.7 Code, fallback: Claude Haiku)
    │      - Max 4 concurrent subagent calls at a time
    │      - Subagent verifies: does the link still make sense? Is the target
    │        document still relevant to the context of the source?
    │      - Incoherent pairs → queued for user review
    │
    ├─ Step 5: Obsolescence scan (small model)
    │    - Small model reads all documents with status: active
    │    - Flags candidates that appear outdated, contradicted, or superseded
    │      by other findings in the bundle
    │    - Candidates → queued for user confirmation
    │
    └─ Step 6: Batch report (chat only)
         Present to user in a single summary:
           - Auto-fixed broken links (with before/after paths)
           - Broken links needing user decision (no confident git match)
           - Superseded-doc links deferred (no superseded_by set)
           - AI-flagged incoherent source↔target link pairs
           - Obsolescence candidates awaiting user confirmation
           - Context mismatches (DEFERRED — pending Q4 resolution)
```

---

## 4. CLI Extension: `okfkb update` Enhancement

**File:** `src/okf_schema/kb/cli.py` (and supporting internal logic)

**New internal step added to `update` command:**

After the existing `index_bundle()` + `lint_bundle()` passes:

```
superseded_by rewriting pass:
  1. Scan all documents: find docs with status: superseded
  2. For each superseded doc:
     a. Read superseded_by field → get replacement path
     b. If replacement path exists on disk:
        - Find all backlinks pointing to the superseded doc
        - Rewrite each backlink to point to the replacement instead
        - Update the links/backlinks frontmatter fields accordingly
     c. If superseded_by is absent or replacement path missing:
        - Record as deferred item (returned to caller for reporting)
  3. Return: list of rewrites performed, list of deferred items
```

**Frontmatter field added to Finding schema:**

```yaml
superseded_by: findings/2024-12-01-new-finding.md   # optional; only on superseded docs
```

This field should be added to `_schema/Finding.schema.yaml` (and possibly `Base.schema.yaml` if applicable to all types).

---

## 5. Model Configuration

| Purpose | Primary model | Fallback |
|---------|--------------|---------|
| Pairwise coherence check | Kimi K2.7 Code | Claude Haiku |
| Obsolescence candidate scan | Kimi K2.7 Code | Claude Haiku |

The skill should attempt Kimi K2.7 first; if unavailable or if the call fails, fall back to Haiku.

---

## 6. Output

- **No file written** — output is a chat summary only
- The summary contains tables for each category of finding (auto-fixed, deferred, flagged)
- The user acts on deferred/flagged items manually after reviewing the summary

---

## 7. UNRESOLVED Items

| Item | Notes |
|------|-------|
| Q4 — Contextual metadata storage | How project-version context (e.g., 26.2 vs 28.2) is stored per Finding and per bundle is deferred. Once decided, a new "context mismatch" step will be added to the workflow (Step 6 already has a placeholder). Candidate approaches: new frontmatter field `applies_to`, tags, or bundle-level `_schema/kb-context.yml`. |

---

## 8. Key Constraints

- **Skill-only orchestration** for Steps 1–3 and 6 (existing CLI commands)
- **One CLI change** required: `okfkb update` extended with `superseded_by` rewriting
- **Batch mode only** — skill never pauses mid-run to ask questions
- **Max 4 parallel subagent calls** for coherence and obsolescence checks
- **No report file written** — all output is in-chat

---

## 9. Skill File Location

```
/Users/az02065/Projects/DevTools/okf-schema/
└── .github/
    └── skills/
        └── okfkb-gardening/
            └── SKILL.md         ← to be created
```
