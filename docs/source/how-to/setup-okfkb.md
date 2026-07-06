# Set Up an OKF-KB (Knowledge Base)

Quick reference for initializing and using an OKF-KB.

> **Want to see OKF-KB in action?**
> See [HW Debugging Workflow Tutorial](../tutorials/okfkb-hw-debugging-workflow.md) for a real automotive debugging scenario.
>
> **Want to understand the design philosophy?**
> See [OKF-KB Design Choices](../explanation/okfkb-choices.md).

---

## Quick Start (5 Minutes)

### 1. Initialize

```bash
mkdir my-kb
cd my-kb
okfkb init
```

Creates: `index.md`, `log.md`, and tier folders (`findings/`, `concepts/`, `principles/`, etc.).

### 2. Agent Creates a Finding

```bash
okfkb new-finding "What was observed"
```

Creates `findings/YYYY.MM.DD-HH.MM-<slug>.md` with template frontmatter.
Agent edits, then:

```bash
okfkb update findings/YYYY.MM.DD-HH.MM-<slug>.md
```

### 3. Index

```bash
okf-schema index --path .
```

Computes backlinks, regenerates `index.md` and `log.md`.

### 4. Validate

```bash
okf-schema lint --path .
```

Checks required fields, timestamps, link validity.

---

## Schema Reference

### Findings: `findings/YYYY.MM.DD-HH.MM-<slug>.md`

Immutable raw observations. Created by agents.

```yaml
type: Finding
title: What was observed?
confidence: low | medium | high
context: System state, configuration, environment
timestamp: 2026-07-04T14:30:00Z
tags: [domain, tags]
links: [findings/..., concepts/...]
backlinks: []  # Auto-computed
status: active | contradicted | archived
contradicted_by: [findings/...]
```

### Concepts: `concepts/<name>.md`

Stable understanding promoted from converged findings.

```yaml
type: Concept
title: Stable understanding
confidence: high
promoted_from: [findings/..., findings/...]
links: [concepts/..., principles/...]
backlinks: []
status: active | superseded
```

### Hypotheses: `hypotheses/<name>.md`

Testable propositions.

```yaml
type: Hypothesis
title: Proposition to test
proposed_by: [findings/... or concepts/...]
links: []
status: open | validated | refuted
```

### Experiments: `experiments/<name>.md`

Planned investigations.

```yaml
type: Experiment
title: What are we testing?
hypothesis: [hypotheses/...]
expected_outcome: What we expect if true
planned_for: YYYY-MM-DD
status: planned | in-progress | completed
results_in: [findings/...]
```

### Principles: `principles/<name>.md`

Team-agreed standards (rarely created, high stakes).

```yaml
type: Principle
title: Standard or policy we agree on
status: active | deprecated
effective_date: YYYY-MM-DD
```

### Structures: `structures/<name>.md`

System composition patterns.

```yaml
type: Structure
title: System composition or pattern
links: [concepts/...]
status: active
```

### Outcomes: `outcomes/<name>.md`

Planned deliverables.

```yaml
type: Outcome
title: Project or deliverable
depends_on: [concepts/...]
status: planned | in-progress | completed
target_date: YYYY-MM-DD
```

### Reference: `reference/<name>.md`

External sources.

```yaml
type: Reference
title: Paper/link title
url: https://...
abstract: Summary
links: [concepts/..., findings/...]
```

### Guides: `guides/<name>.md`

Operational how-to notes.

```yaml
type: Guide
title: How to do X
status: active
links: []
```

---

## Linking Your Documents

Add `links:` entries to connect documents:

```yaml
links:
  - findings/2026-07-03-root-cause.md
  - concepts/subsystem-behavior.md
  - principles/timeout-policy.md
```

Run `okf-schema index --path .` to auto-compute backlinks.

---

## Frontmatter Validation

```bash
okf-schema lint --path .
```

Verifies:
- Required fields present
- Confidence values valid (`low`, `medium`, `high`)
- Timestamps in ISO 8601 format
- All `links:` point to existing files
- `status:` values match schema

---

## Tips for Success

1. **Findings are immutable** — once created, only update lifecycle fields (`status`, `contradicted_by`)
2. **Link aggressively** — more links = more navigable KB
3. **Index after batches** — run `okf-schema index` after each editing session
4. **Use tags for filtering** — tags help agents search by domain
5. **Review `log.md` regularly** — keep it human-readable; summarize weekly changes
6. **Principles are rare** — only for team consensus decisions
7. **Promotion requires convergence** — wait for 2+ findings before creating a concept

---

## Further Reading

- [OKF-KB Design Choices](../explanation/okfkb-choices.md) — Philosophy, tradeoffs, design rationale
- [HW Debugging Workflow](../tutorials/okfkb-hw-debugging-workflow.md) — Step-by-step tutorial (automotive example)
- [Bootstrap an Existing KB](../how-to/bootstrap-knowledge-base) — Migrating legacy findings
- [Building a Knowledge Graph](../tutorials/knowledge-graph) — Cross-linking best practices
- [Lint Before Commit](../how-to/lint-before-commit) — Keeping frontmatter consistent
- [KB Commands Reference](../reference/kb-commands) — Full CLI reference
