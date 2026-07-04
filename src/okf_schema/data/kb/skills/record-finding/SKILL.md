---
name: record-finding
description: 'Dump a single empirical Finding into the OKF knowledge base after an investigation or debugging session. Fast and non-interactive. Records what you truthfully observed and believed at this moment, with confidence and context, as an immutable dated note under knowledge/findings/. Use after diagnosing a bug, verifying behavior, or discovering something non-trivial worth remembering.'
---

# record-finding

Record ONE Finding: a dated, empirical, falsifiable note of what you observed and
believed right now. Findings can later be wrong — that is fine. Be truthful about
the moment, not about eternal truth.

## When to use

- You just finished an investigation, debugging session, or verification.
- You learned something non-trivial about how the external world (VS Code,
  Copilot, pricing, logs) behaves.
- You want to hand off "what I found and believed" for later consolidation.

Do NOT use this to record standards/conventions (that is a Principle), how an
object is composed (Structure), or a stable idea (Concept). Those are promoted
deliberately by `consolidate-knowledge-base`, not dumped.

## Procedure

1. Write exactly one file to `knowledge/findings/<slug>.md` where `<slug>` is a
   short hyphenated summary of the claim.
2. Use this frontmatter (all listed fields are required):

   ```yaml
   ---
   type: Finding
   title: Short claim as a title
   description: One-sentence summary of the finding.
   tags: [relevant, keywords]
   timestamp: <ISO-8601 UTC, e.g. 2026-07-02T14:30:00Z>
   confidence: low | medium | high
   context: >-
     What you believed and the situation at the time — including assumptions
     that may later prove wrong, and the scope you actually tested.
   ---
   ```

3. In the body, state plainly: what was observed, why it matters, and the
   caveats / limits of what you verified.
4. If this finding contradicts or replaces an earlier one, add
   `contradicts: [<finding-id>]` or `supersedes: [<finding-id>]`. Do NOT edit the
   older finding — the `consolidate-knowledge-base` skill handles backlinks.
5. If a run of an Experiment produced this finding, add `derived_from: <experiment-id>`.

## Immutability

Once written, never reword or delete a finding's body. This is enforced by the
`Findings Are Immutable` principle. Corrections happen by writing a NEW finding.

## Validate

```bash
just knowledge-lint
just knowledge-validate
```

Both must pass. Do not run `consolidate-knowledge-base` here — dumping stays fast.
