---
name: okfkb-record-findings
description: 'Record one immutable empirical Finding in an OKF knowledge base after an investigation or debugging session.'
---

# okfkb-record-findings

Record exactly one dated, falsifiable Finding after an investigation. Write it to
`knowledge/findings/<slug>.md`, preserve the actual context and caveats, and do
not rewrite earlier findings. Use the Finding frontmatter required by the
knowledge-base schema, including `generated.at`, `generated.by`, and
`kb_status: active`. Do not use this skill for standards, stable concepts,
structures, or outcomes; those are handled by `okfkb-distill`.

After recording, run `just knowledge-lint` and `just knowledge-validate`. Never
edit or delete a Finding body; corrections are new Findings. Do not run the
distillation workflow while recording.
