---
name: consolidate-knowledge-base
description: 'Interactively review the OKF knowledge base to detect contradictions between Findings, mark contradicted/superseded Findings, propose Experiments to resolve open questions, and propose promotions of converged Findings into stable Concept/Structure/Principle documents. Every mutation is confirmed by a human before it is written. Use periodically or after a batch of recorded Findings.'
---

# consolidate-knowledge-base

Turn a pile of dated Findings into consolidated, trustworthy knowledge — without
ever rewriting history. This skill is **interactive**: it proposes, the human
confirms, then it writes.

## When to use

- After a batch of Findings has been dumped by `record-finding`.
- Periodically, to keep the empirical layer coherent with the stable layer.
- When you suspect two findings disagree.

## Guardrails

- NEVER edit or delete a Finding's body. Only append lifecycle frontmatter
  (`status`, `contradicted_by`, `superseded_by`).
- NEVER promote to a Principle without explicit human confirmation — principles
  are agreed with humans.
- Ask before every write, using `vscode_askQuestions`.

## Procedure

### 1. Scan
Read `knowledge/findings/`, plus `principles/`, `structures/`, `concepts/`.
Build a map of claims, tags, and existing `contradicts`/`supersedes` links.

### 2. Detect contradictions
Identify pairs where a newer Finding disagrees with an older Finding, or where a
Finding conflicts with a Principle/Structure/Concept. Present each candidate
contradiction to the human for confirmation.

### 3. Mark (on confirmation)
For each confirmed contradiction, append metadata-only fields:
- On the newer finding: `contradicts: [<old-id>]` (if not already present).
- On the older finding: `status: contradicted` and `contradicted_by: [<new-id>]`.
Use the same pattern with `supersedes`/`superseded_by` for replacements.
The body of both files stays untouched.

### 4. Propose Experiments
For unresolved or low-confidence contradictions, propose a new `Experiment`
document (hypothesis, steps, expected_signals, `max_runs: 1–2`) that would
settle the question. Write it to `knowledge/experiments/` only on confirmation.

### 5. Propose promotions
When several Findings converge on a stable truth, propose promoting the insight
into the stable layer:
- "how it works" → `Structure` in `structures/`
- "the idea" → `Concept` in `concepts/`
- "the standard/convention" → `Principle` in `principles/` (always human-agreed)
Link the promoted doc back to its supporting findings (`supported_by` /
`related_concepts`). Write only on confirmation. Findings remain untouched.

### 6. Validate
```bash
just knowledge-lint
just knowledge-validate
```
Both must pass before finishing.

## Output

A short chat summary: contradictions found and marked, experiments proposed,
promotions made, and any open questions left for a future run.
