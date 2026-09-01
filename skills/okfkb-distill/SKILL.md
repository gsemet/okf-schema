---
name: okfkb-distill
description: 'Interactively consolidate OKF Findings, resolve contradictions, and propose promotions into stable knowledge layers with human confirmation.'
---

# okfkb-distill

## Agent configuration directory precedence

When resolving project instructions or guidelines, use `.agents/` if it exists.
Use `.github/` only when `.agents/` does not exist. Never prefer `.github/` over
an existing `.agents/` directory, and do not create both locations for the same
configuration.

Use this skill after a batch of Findings, periodically, or when Findings appear
to disagree. It turns empirical observations into coherent, trustworthy
knowledge without rewriting history. It proposes changes; a human confirms
each mutation.

## Guardrails

- Never edit or delete a Finding body. Only append lifecycle metadata such as
  `kb_status`, `contradicted_by`, or `superseded_by`.
- Never promote a Finding to a Principle without explicit human confirmation.
- Ask before every write using `vscode_askQuestions`.

## Procedure

1. Read `knowledge/findings/`, `principles/`, `structures/`, and `concepts/`.
   Build a map of claims, tags, and existing contradiction or replacement links.
2. Identify newer Findings that disagree with older Findings or with stable
   knowledge. Present every candidate contradiction to the human.
3. On confirmation, add `contradicts: [<old-id>]` to the newer Finding and
   `kb_status: contradicted` plus `contradicted_by: [<new-id>]` to the older one.
   Use the equivalent `supersedes` and `superseded_by` fields for replacements.
   Keep both bodies unchanged.
4. For unresolved or low-confidence contradictions, propose an `Experiment`
   with a hypothesis, steps, expected signals, and `max_runs: 1–2`. Write it
   only after confirmation.
5. For convergent Findings, propose a promotion:
   - how it works → `Structure`;
   - stable idea or definition → `Concept`;
   - standard or convention → `Principle`.
   Link promoted documents to their sources with authored `derived_from`
   canonical bundle-relative, extensionless paths. Never edit computed
   `derives_to`. Write only after confirmation.
6. Run the knowledge-base validation commands before finishing:

   ```console
   just knowledge-lint
   just knowledge-validate
   ```

## Output

Summarize contradictions found and marked, Experiments proposed, promotions
made, and open questions left for a future run.
