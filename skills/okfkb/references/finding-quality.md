# Finding quality

A Finding is the atomic empirical record: an honest, dated statement of what
was observed and believed under a bounded context. It need not remain correct;
it must remain truthful to the moment.

## Record a Finding when

The knowledge is all of the following:

1. **Empirical** — learned through investigation, execution, measurement, or
   verification rather than copied from code or documentation.
2. **Non-trivial** — a future agent would not cheaply infer it from obvious
   source or existing docs.
3. **Durable enough to reuse** — likely to matter beyond the current response.
4. **Falsifiable or bounded** — another investigation could challenge it, or its
   scope is stated precisely enough to know where it applies.
5. **Not already captured** — search the KB before creating a duplicate.

Do not record chat summaries, implementation plans, opinions, generic best
practices, or facts already canonical in code/docs as Findings.

## Required content

Follow the local Finding schema. A strong Finding contains:

- a title phrased as the observed claim;
- a short description useful in indexes and search;
- an exact timestamp;
- confidence reflecting the reporter's certainty at capture time;
- context: environment, versions, configuration, inputs, assumptions, and
  tested scope;
- body: observation, evidence or reproduction, why it matters, and limits;
- links to relevant Findings, Experiments, Concepts, or external evidence.

Use `confirmed` confidence only when the local schema permits it and evidence is
direct, repeatable, and decisive. Confidence describes the evidence available
at capture time, not the document's age or popularity.

## Atomicity

Record one principal claim per Finding. If an investigation reveals multiple
independently falsifiable claims, create multiple linked Findings. This makes
later contradiction and promotion precise.

## Corrections and disagreement

Never rewrite the original body. Create a newer Finding and use the relationship
allowed by the local schema:

- `contradicts`: the newer evidence conflicts with the older claim; both may
  remain relevant under different contexts until reviewed.
- `supersedes`: the newer Finding replaces an older account, measurement, or
  scoped understanding.
- `derived_from`: the Finding was produced by an Experiment.

Consolidation appends reciprocal lifecycle metadata to the older Finding, such
as `status: contradicted`, `contradicted_by`, `status: superseded`, or
`superseded_by`. Appending lifecycle metadata is not permission to alter prose.

## Before finishing

Search for related records, use schema-valid fields, update generated navigation
if project rules require it, and run the KB checks prescribed by `AGENTS.md`.