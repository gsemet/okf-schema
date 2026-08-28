---
name: okfkb-distill
description: 'Interactively consolidate OKF Findings, resolve contradictions, and propose promotions into stable knowledge layers with human confirmation.'
---

# okfkb-distill

<!-- @implements_req SwRS-OKFSCHEMA-OKFKB-005 -->

After a batch of Findings, scan findings and stable tiers, identify contradictions,
and propose promotions without rewriting history. Ask the human before every
write using `vscode_askQuestions`. Never edit or delete a Finding body. Only
append lifecycle metadata (`kb_status`, contradiction/supersession fields) or
links; Principles always require explicit human
confirmation. Propose Experiments for unresolved contradictions and promote
convergent knowledge to Concepts, Structures, or Principles. Finish with
`just knowledge-lint` and `just knowledge-validate`.
