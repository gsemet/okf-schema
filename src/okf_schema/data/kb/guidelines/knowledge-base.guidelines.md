---
applyTo: "knowledge/**/*.md"
description: "The minimal rules a coding agent must follow to maintain the OKF knowledge bundle in knowledge/."
---

# Knowledge Base Maintenance Guidelines

`knowledge/` is an [OKF](https://github.com/gsemet/okf-schema) bundle. Each `.md`
file has a `type` in its frontmatter that maps to a schema in `_schema/`. This
document is the strict minimal rule set for maintaining it correctly.

## 1. Choose the right type

| You want to record… | type | Folder | Layer | Nature |
|---------------------|------|--------|-------|--------|
| A raw observation at time T | `Finding` | `findings/` | Storage | Empirical, immutable |
| A testable idea to validate | `Hypothesis` | `hypotheses/` | Testing | Testable, mutable |
| A reusable test procedure | `Experiment` | `experiments/` | Testing | Template, run 1–2× |
| A stable idea / "what is this?" | `Concept` | `concepts/` | Semantic | Explanatory, mutable |
| How an object is composed / works | `Structure` | `structures/` | Semantic | Descriptive, mutable |
| A human-agreed standard | `Principle` | `principles/` | Governance | Normative, stable |
| A reproducible workflow | `Playbook` | `guides/` | Operational | Procedural, mutable |
| A planned deliverable | `Outcome` | `outcomes/` | Planning | Goal-oriented, mutable |
| External papers, lookup tables | `Reference` | `reference/` | Lookup | Lookup, immutable |

Rules of thumb:

- Document only what is **non-trivial** for coding agents. Do not paraphrase code
  or existing docs — link instead.
- Keep each file focused and concise, important information first.
- Findings are the empirical layer; Hypotheses and Experiments are the testing
  layer; Concepts and Structures are the semantic layer; Principles are the
  governance layer; Playbooks are the operational layer; Outcomes are the
  planning layer; References are the lookup layer.
- Agents dump Findings freely; stable docs are promoted deliberately by the
  `consolidate-knowledge-base` skill — never dumped ad hoc.
- Hypotheses are promoted to Concept or Structure by human decision, never
  automatically.
- Falsified Hypotheses remain in the knowledge base with `status: falsified`.
- Playbooks are experienced until proven false; use `superseded_by` when a
  better workflow emerges.
- Outcomes track progress and may reference Playbooks for execution.

## 2. Required frontmatter

All documents (except `index.md` and `log.md`) require:

```yaml
type: <one of the types above>   # must match the const in _schema/<Type>.schema.yaml
title: Human-Readable Title       # non-empty
description: Short summary.        # non-empty
tags: [keyword]                    # optional but encouraged
timestamp: 2026-07-02T00:00:00Z   # ISO 8601 (YYYY-MM-DDTHH:MM:SSZ)
```

Type-specific required fields:

- **Finding**: also `timestamp`, `confidence` (`low|medium|high`), and `context`
  (what you believed and the scope you actually tested).
- **Experiment**: also `hypothesis` and `steps`.

## 3. Finding immutability & contradictions

- A Finding's **body and claim are frozen** once written. Never reword or delete.
- To correct a Finding, write a NEW Finding with `contradicts: [<old-id>]` or
  `supersedes: [<old-id>]`.
- The only permitted edits to an existing Finding are the lifecycle fields
  `status` (`contradicted|superseded`), `contradicted_by`, `superseded_by`,
  appended by the `consolidate-knowledge-base` review.
- Promotion of converged Findings into Concept/Structure/Principle is done by
  `consolidate-knowledge-base` with human confirmation — Principles are always
  agreed with humans.

## 4. Skills

- **`record-finding`** (fast, non-interactive): dump one Finding after an
  investigation or debugging session.
- **`consolidate-knowledge-base`** (interactive, human-confirmed): detect
  contradictions, mark findings, propose Experiments, propose promotions.

## 5. Validate before commit

```bash
just knowledge-lint          # auto-format frontmatter + rebuild index
just knowledge-validate      # 0 errors, 0 warnings required
just knowledge-lint-check    # verify no pending format changes
```

Pre-commit checklist:

- [ ] Correct `type` and folder for the information recorded.
- [ ] Required frontmatter present and valid.
- [ ] No Finding body was reworded or deleted.
- [ ] All three commands above pass (also covered by `just preflight`).

Add a dated entry to `knowledge/log.md` for significant changes. Use plain
ISO-8601 date headings; avoid parenthetical annotations (they trigger warnings).
