# OKFKB Gardening

Keep an OKF knowledge-base bundle healthy: fix broken links, propagate
superseded-document redirects, run pairwise coherence checks with a small
model, and surface obsolescence candidates — all in one batch run.

---

## Trigger

```
okfkb garden /path/to/kb
```

---

## Prerequisites

- `okf-schema` CLI installed and on `$PATH` (or available via `uv run okf-schema`)
- Bundle is a valid OKFKB layout (run `okfkb validate /path/to/kb` to confirm)
- Git repository wrapping the bundle (required for the broken-link auto-fix step)

---

## Workflow

Run the steps below **in order**. Every step produces findings; collect them
all and present the full batch report at the very end (Step 6). Never pause
mid-run to ask the user a question — queue ambiguous items instead.

---

### Step 1 — Baseline validation

```bash
okfkb validate /path/to/kb
```

Record the initial error and warning counts. Use this as a before/after
comparison in the final report.

---

### Step 2 — Broken-link detection and auto-fix

**Goal:** repair links whose targets were moved, renamed, or deleted.

1. Collect every internal link from all frontmatter `links:` fields and
   markdown body `[text](path)` patterns.
2. For each link target, check whether the file exists on disk.
3. **Broken link found?**
   - Run `git log --follow --diff-filter=R --name-status -- <old-path>` to
     detect renames in git history.
   - If git returns a single confident rename (`similarity > 85%`), apply the
     fix: update the link in the document body to the new path.
   - If git returns no result or multiple candidates, add to the
     **deferred queue** (do not touch the file).
4. After all auto-fixes, run `okfkb update /path/to/kb` so that
   `links`/`backlinks` frontmatter is refreshed.

---

### Step 3 — Superseded-link propagation

This step is built into `okfkb update` as of okf-schema ≥ 0.x.

```bash
okfkb update /path/to/kb
```

`okfkb update` now automatically:
- Scans for documents with `status: superseded` and a `superseded_by` field
- Rewrites all body links pointing to the superseded document to the replacement
- Reports deferred items (missing or non-existent `superseded_by`) in stdout

Capture deferred items from the command output and add them to the batch report.

---

### Step 4 — Pairwise coherence checks (small model)

**Goal:** detect links that are technically valid but semantically stale.

For each document D in the bundle:

1. Collect the list of documents D links to (from the `links:` frontmatter field
   after Step 3 update).
2. For each linked target T, spawn a subagent with the following task:

   > Read source document D and linked document T.
   > Answer: Does the link from D to T still make sense?
   > Is T still relevant to the context described in D?
   > Reply with: COHERENT | INCOHERENT | UNCERTAIN, followed by one sentence of reasoning.

3. **Concurrency limit: 4 subagents at a time.**
4. **Model preference:** Kimi K2.7 Code first; fall back to Claude Haiku if
   Kimi is unavailable or returns an error.
5. Collect all INCOHERENT and UNCERTAIN verdicts into the **coherence issues queue**.

---

### Step 5 — Obsolescence scan (small model)

**Goal:** surface active findings that may be outdated without being formally superseded.

Collect all documents with `status: active` (or no status field) and `type: Finding`.
Batch them into groups of 10. For each group, spawn a subagent:

> You are reviewing a batch of knowledge-base Findings for potential obsolescence.
> For each Finding, state whether it appears LIKELY_OBSOLETE, POSSIBLY_OBSOLETE,
> or STILL_VALID, and give one sentence of reasoning.
> Findings to review:
> [paste titles, descriptions, and timestamps]

Collect all LIKELY_OBSOLETE and POSSIBLY_OBSOLETE candidates into the
**obsolescence candidates queue**.

**Concurrency limit: 4 subagent calls at a time.**
**Model preference:** Kimi K2.7 Code first; fall back to Claude Haiku.

---

### Step 6 — Batch report (chat only, no file written)

Present a single structured summary in chat with these sections:

#### Auto-Fixed Broken Links
| Document | Old Path | New Path |
|----------|----------|----------|
| ...      | ...      | ...      |

#### Broken Links — Needs Manual Review
| Document | Broken Link | Reason (no git match / ambiguous) |
|----------|-------------|-----------------------------------|
| ...      | ...         | ...                               |

#### Superseded Links — Deferred (needs `superseded_by` field)
| Superseded Document | Reason |
|---------------------|--------|
| ...                 | ...    |

#### Coherence Issues (AI-flagged)
| Source | Target | Verdict | Reasoning |
|--------|--------|---------|-----------|
| ...    | ...    | ...     | ...       |

#### Obsolescence Candidates (AI-flagged)
| Document | Verdict | Reasoning |
|----------|---------|-----------|
| ...      | ...     | ...       |

#### Summary
- Baseline: N errors, M warnings
- Auto-fixed broken links: X
- Deferred broken links: Y
- Superseded-link rewrites applied: Z
- Superseded links deferred: W
- Coherence issues flagged: P
- Obsolescence candidates: Q

---

## Contextual Metadata (Future)

> **Note:** Support for project-version context (e.g., marking findings as
> relevant only to project version 26.2 or 28.2) is planned but not yet
> specified. When the `applies_to` metadata design is finalised, a
> **Context Mismatch** section will be added to Step 6's report.

---

## Example Session

```
User: okfkb garden /path/to/sdv-kb

[Step 1] Baseline: 2 errors, 5 warnings

[Step 2] Scanning for broken links...
  Auto-fixed: findings/2024-01-15-pll.md: ../concepts/old-pll.md → ../concepts/pll-v2.md
  Deferred: findings/2024-03-01-brake.md: ../systems/brake-ecu.md (no git match)

[Step 3] Running okfkb update...
  Superseded rewrites: 3
  Deferred: 1 (findings/2024-06-01-deprecated.md: no superseded_by)

[Step 4] Running coherence checks (4 parallel)...
  12 pairs checked, 2 flagged INCOHERENT

[Step 5] Running obsolescence scan...
  31 findings scanned, 4 candidates flagged

[Step 6] Batch report presented.
```
