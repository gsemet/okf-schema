---
name: okfkb
description: 'Understand, use, and maintain an opinionated OKFKB knowledge base: capture immutable empirical Findings, choose the correct knowledge layer, consolidate converged evidence into Concepts and Structures, preserve contradictions, navigate from stable knowledge to raw evidence, and route recurring maintenance to okfkb-gardening. Use when the user mentions OKFKB, knowledge lifecycle, recording durable findings, consolidating a knowledge base, promoting findings, choosing a KB document type, or maintaining an agent knowledge base.'
metadata:
  keywords: [okfkb, knowledge-base, findings, consolidation, knowledge-lifecycle, concepts, structures, principles, playbooks, agent-memory]
  url: https://github.com/gsemet/okf-schema
---

# okfkb

Use OKFKB as an external memory that separates dated empirical evidence from
stable understanding and human governance. Teach the model, identify the user's
intent, then route to the smallest appropriate workflow.

This skill explains the **opinionated knowledge lifecycle**. Use the
`okf-schema` skill for CLI syntax, schema validation, generic OKF conformance,
or implementation details of the tool itself.

## Start with project rules

1. Locate the knowledge-base root. Prefer an explicit path; otherwise infer it
   from the workspace and the presence of `_schema/`, `index.md`, and tier
   directories.
2. Read the nearest `AGENTS.md` and any linked knowledge-base guidelines before
   reading or writing KB documents. Local rules and schemas are authoritative.
3. Inspect the bundle's `_schema/` files before inventing fields, statuses, or
   transitions. Preserve extension fields that the bundle already uses.

## Route the intent

| Intent | Action |
|---|---|
| Understand the layers or choose a type | Read [lifecycle and taxonomy](references/lifecycle-and-taxonomy.md). |
| Preserve a new empirical discovery | Use `record-finding`; apply [Finding quality](references/finding-quality.md). |
| Review contradictions or promote knowledge with the user | Use `consolidate-knowledge-base`; apply [consolidation judgment](references/consolidation-judgment.md). |
| Perform recurring autonomous KB upkeep | Use `okfkb-gardening`. It is explicit-invocation, zero-prompt maintenance. |
| Find existing knowledge | Apply [navigation and maintenance](references/navigation-and-maintenance.md), starting from stable tiers. |
| Validate, lint, initialize, or troubleshoot OKF structure | Use `okf-schema`. |

If a named specialized skill is unavailable, follow the corresponding reference
directly while preserving all guardrails.

## Core model

- **Findings are immutable historical evidence.** Capture what was observed,
  believed, and scoped at time $T$; never rewrite the body to make history look
  correct. Correct it with a newer Finding and lifecycle links.
- **Hypotheses and Experiments manage uncertainty.** Use them when evidence does
  not yet justify stable knowledge. They are optional when Findings already
  converge clearly.
- **Concepts and Structures are living semantic knowledge.** Promote directly
  from converged Findings or confirmed Hypotheses. Update them in place as the
  understanding improves, retain evidence links, and log material revisions.
- **Principles are human governance.** Never create, activate, edit, deprecate,
  or supersede a Principle without explicit human agreement. Evidence may
  suggest a Principle but cannot decide one.
- **Playbooks are operational knowledge.** The canonical type is `Playbook` in
  `guides/`; revise or supersede it as experience changes.
- **Outcomes describe intended deliverables**, not facts or procedures.
- **References preserve external sources**, not locally inferred truth.

## Capture durable discoveries proactively

At the end of meaningful debugging, investigation, or verification work, assess
whether the result is non-trivial, empirical, useful to a future agent, and not
already captured. If it clearly is, route to `record-finding` without waiting
for a separate user request. Do not record routine code facts that are cheaper
to rediscover from source or existing documentation.

## Universal guardrails

1. Never edit or delete a Finding's body or claim after creation.
2. Never silently erase disagreement. Link contradictions and supersession in
   both directions using fields allowed by the local schemas.
3. Never promote merely because several files repeat the same unsupported
   assertion. Judge evidence quality, independence, scope, and reuse value.
4. Never turn an empirical pattern into a normative Principle automatically.
5. Do not bulk-load the KB. Read stable tiers first, query narrowly, and descend
   to Findings only when evidence is needed.
6. After mutations, run the validation/lint/index commands prescribed by the
   project's `AGENTS.md` or linked guidelines. Repair failures and report any
   unresolved errors honestly.

## Completion

Summarize what was learned or changed, cite affected KB paths, state validation
results, and list unresolved contradictions or proposed Principles. Do not
create a separate report artifact unless the project rules require one.