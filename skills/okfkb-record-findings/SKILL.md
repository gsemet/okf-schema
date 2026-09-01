---
name: okfkb-record-findings
description: 'Record one immutable empirical Finding in an OKF knowledge base after an investigation or debugging session.'
---

# okfkb-record-findings

## Agent configuration directory precedence

When resolving project instructions or guidelines, use `.agents/` if it exists.
Use `.github/` only when `.agents/` does not exist. Never prefer `.github/` over
an existing `.agents/` directory, and do not create both locations for the same
configuration.

Use this skill after an investigation, debugging session, or verification when
one non-trivial empirical observation should be handed off for later curation.
Record exactly one dated, falsifiable Finding describing what was observed and
believed in its actual context. Findings can later be wrong; preserve the
observation rather than rewriting history.

Do not use this skill for standards, conventions, stable concepts, structures,
or outcomes. Those are deliberately promoted by `okfkb-distill`.

## Procedure

1. Write exactly one file to `knowledge/findings/<slug>.md`, where `<slug>` is a
   short hyphenated summary of the claim.
2. Use this frontmatter, with all listed fields:

   ```yaml
   ---
   type: Finding
   title: Short claim as a title
   description: One-sentence summary of the finding.
   tags: [relevant, keywords]
   generated:
     at: <ISO-8601 UTC, e.g. 2026-07-02T14:30:00Z>
     by: <actor, e.g. human:alice or bot:collector>
   confidence: low | medium | high | confirmed
   kb_status: active
   context: >-
     What you believed and the situation at the time, including assumptions
     that may later prove wrong and the scope you actually tested.
   ---
   ```

3. In the body, state what was observed, why it matters, and the caveats or
   limits of what was verified.
4. If this Finding contradicts or replaces an earlier one, add
   `contradicts: [<finding-id>]` or `supersedes: [<finding-id>]`. Do not edit the
   older Finding.
5. If an Experiment produced the Finding, add
   `derived_from: [experiments/<extensionless-name>]`. Never edit computed
   `derives_to`.

## Immutability and validation

Once written, never reword or delete the Finding body. Corrections are new
Findings. Validate the knowledge base after recording:

```console
just knowledge-lint
just knowledge-validate
```

Do not run `okfkb-distill` while recording; capture remains fast and separate
from interactive consolidation.
