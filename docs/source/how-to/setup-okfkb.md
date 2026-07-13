# Set Up an OKF-KB (Knowledge Base)

Quick reference for initializing and using an OKF-KB.

> **Want to see OKF-KB in action?**
> See [HW Debugging Workflow Tutorial](../tutorials/okfkb-hw-debugging-workflow.md) for a real automotive debugging scenario.
>
> **Want to understand the design philosophy?**
> See [OKF-KB Design Choices](../explanation/okfkb-choices.md).
>
> **Want agent-assisted maintenance?**
> See [Maintain an OKFKB with agent skills](maintain-okfkb-with-skills.md).

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
okfkb validate .
```

Strictly checks required fields, timestamps, schema values, and link validity.

## Add the Agent Workflows

Deploy the project-local capture and interactive consolidation skills:

```bash
okfkb install-skills /path/to/project
```

The repository-level skills add two broader workflows:

- **`okfkb`** teaches the lifecycle, chooses the right knowledge type, routes
  empirical discoveries to `record-finding`, and navigates from stable tiers to
  raw evidence.
- **`okfkb-gardening`** performs an explicitly invoked, autonomous maintenance
  pass. It repairs graph mechanics, reconciles Finding lifecycles, consolidates
  stable knowledge, refreshes operational/planning layers, and runs checks
  discovered from the project's `AGENTS.md`.

Gardening may update every KB layer except Principles. It reports Principle
candidates with rationale and evidence; a human must explicitly agree before a
Principle is created or changed.

## Navigating the KB

Four commands expose the KB as agent-native **navigation tools** — pull the right granularity
instead of loading whole folders:

```bash
# Coarse ranked search across titles, context, tags, body
okfkb search "pll lock time" --tier findings

# Exact fetch of a single node
okfkb get findings/2026.07.03-14.20-pll-temp-drift.md

# Read a whole stable tier (top-down entry point)
okfkb read concepts --status active

# Structured query: filter DSL (flat frontmatter)
okfkb query "type:finding confidence:>=high tag:pll status:active"

# Structured query: arrow traversal over the link/promotion graph
#   ->  follows links   <-  follows backlinks   ^  follows promotion
okfkb query "finding[tag=pll,confidence=high] -> concept -> principle"
```

**When to use which:** `read` a stable tier for the big picture, `query`/`search` to locate
relevant nodes by criteria, then `get` a specific node for evidence-level detail. See the
[KB Commands Reference](../reference/kb-commands.md) for the full `query` grammar.

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
status: active | contradicted | superseded
contradicted_by: [findings/...]
```

### Concepts: `concepts/<name>.md`

Stable understanding promoted from converged findings.

```yaml
type: Concept
title: Stable understanding
description: Concise explanation of the stable idea
derived_from: [findings/..., findings/...]
links: [concepts/..., principles/...]
backlinks: []
status: active | deprecated
```

### Hypotheses: `hypotheses/<name>.md`

Testable propositions.

```yaml
type: Hypothesis
title: Proposition to test
description: Testable explanation of observations
derived_from: [findings/... or concepts/...]
links: []
status: proposed | under_test | confirmed | falsified
```

### Experiments: `experiments/<name>.md`

Planned investigations.

```yaml
type: Experiment
title: What are we testing?
description: Reusable procedure for testing the hypothesis
hypothesis: hypotheses/...
steps: [Prepare the target, Run the measurement, Capture the signals]
expected_signals: [Signal expected if true, Signal expected if false]
status: proposed | active | retired | superseded
derived_findings: [findings/...]
```

### Principles: `principles/<name>.md`

Team-agreed standards (rarely created, high stakes).

```yaml
type: Principle
title: Standard or policy we agree on
description: Human-agreed normative rule
rationale: Why this rule exists
authority: team
supported_by: [findings/...]
```

### Structures: `structures/<name>.md`

System composition patterns.

```yaml
type: Structure
title: System composition or pattern
description: How the subject is composed or works
derived_from: [findings/...]
links: [concepts/...]
status: active | deprecated
```

### Outcomes: `outcomes/<name>.md`

Planned deliverables.

```yaml
type: Outcome
title: Project or deliverable
description: Planned result derived from stable knowledge
status: planned | in_progress | done | cancelled
deliverable: Concrete artifact or result
derived_from: [concepts/...]
```

### Reference: `reference/<name>.md`

External sources.

```yaml
type: Reference
title: Paper/link title
description: What this source contributes
url: https://...
abstract: Summary
links: [concepts/..., findings/...]
```

### Playbooks: `guides/<name>.md`

Operational how-to notes.

```yaml
type: Playbook
title: How to do X
description: Reproducible workflow that produces a result
status: active | deprecated | superseded
links: []
```

## Linking Your Documents

Add `links:` entries to connect documents:

```yaml
links:
  - findings/2026-07-03-root-cause.md
  - concepts/subsystem-behavior.md
  - principles/timeout-policy.md
```

Run `okf-schema index --path .` to auto-compute backlinks.

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

## Tips for Success

1. **Findings are immutable** — once created, only update lifecycle fields (`status`, `contradicted_by`)
2. **Link aggressively** — more links = more navigable KB
3. **Index after batches** — run `okf-schema index` after each editing session
4. **Use tags for filtering** — tags help agents search by domain
5. **Review `log.md` regularly** — keep it human-readable; summarize weekly changes
6. **Principles are rare** — only for team consensus decisions
7. **Promotion requires judgment** — consider evidence quality, independence,
  scope, counter-evidence, and reuse value rather than relying on a fixed count
8. **Garden after meaningful batches** — explicitly invoke `okfkb-gardening`
  for autonomous consolidation and maintenance
9. **Principles remain human decisions** — gardening proposes; people agree

## Further Reading

- [OKF-KB Design Choices](../explanation/okfkb-choices.md) — Philosophy, tradeoffs, design rationale
- [HW Debugging Workflow](../tutorials/okfkb-hw-debugging-workflow.md) — Step-by-step tutorial (automotive example)
- [Maintain an OKFKB with agent skills](maintain-okfkb-with-skills.md) — Capture, navigate, consolidate, garden, and validate
- [Bootstrap an Existing KB](../how-to/bootstrap-knowledge-base) — Migrating legacy findings
- [Building a Knowledge Graph](../tutorials/knowledge-graph) — Cross-linking best practices
- [Lint Before Commit](../how-to/lint-before-commit) — Keeping frontmatter consistent
- [KB Commands Reference](../reference/kb-commands) — Full CLI reference
