# Agent skills

This directory contains agent-facing instructions for working with OKF bundles
and the opinionated OKFKB knowledge lifecycle. The skills complement the CLI:
the CLI performs deterministic file operations and validation, while the skills
teach an agent when and why to use each operation.

## Available skills

| Skill | Purpose | Use it when |
|---|---|---|
| [`okf-schema`](okf-schema/SKILL.md) | Operate the tool: initialize, validate, lint, index, query, and troubleshoot generic OKF bundles and schemas. | The task concerns CLI/API usage, OKF conformance, JSONSchema validation, frontmatter, links, or bundle structure. |
| [`okfkb`](okfkb/SKILL.md) | Understand and route the opinionated knowledge lifecycle: capture immutable Findings, choose a layer, consolidate evidence, navigate top-down, and protect human-governed Principles. | The task concerns what knowledge belongs in the KB, how it should mature, or which specialized workflow should handle it. |
| [`okfkb-gardening`](okfkb-gardening/SKILL.md) | Run an explicit, autonomous, zero-prompt maintenance pass: repair graph mechanics, reconcile Finding lifecycles, consolidate semantic knowledge, surface stale content, and validate the result. | The user explicitly asks to garden, refresh, consolidate, or maintain an OKFKB bundle. |

## How the skills fit together

```text
                         ┌──────────────────────────┐
                         │          okfkb           │
                         │ lifecycle + intent router│
                         └────────────┬─────────────┘
                                      │
              ┌───────────────────────┼────────────────────────┐
              │                       │                        │
              v                       v                        v
      record-finding*     consolidate-knowledge-base*   okfkb-gardening
      one empirical note   interactive review            autonomous batch
              │                       │                        │
              └───────────────────────┴────────────┬───────────┘
                                                   v
                                           okf-schema
                                  deterministic CLI + validation
```

`record-finding` and `consolidate-knowledge-base` are bundled project skills
deployed by `okfkb install-skills`. They are not duplicated in this directory:

- **`record-finding`** quickly captures one dated, immutable empirical Finding.
- **`consolidate-knowledge-base`** interactively reviews contradictions and
  promotions, confirming mutations with a human.

The repository-level `okfkb` skill routes to those specialized skills when they
are available. Its references provide the fallback lifecycle guidance.

## Choosing a skill

- Start with **`okf-schema`** for mechanics: “Why does validation fail?” or
  “How do I rebuild indexes?”
- Start with **`okfkb`** for semantics: “Is this a Finding or Concept?” or
  “Should these observations be promoted?”
- Invoke **`okfkb-gardening`** for periodic upkeep after Findings accumulate.
  It does not ask questions during the run and may update all KB layers except
  Principles.

Principles remain human-governed in every workflow. An agent may propose a
Principle with rationale and evidence, but it must not mutate one without
explicit human agreement.

## Recommended maintenance rhythm

1. During investigations, let `okfkb` assess durable discoveries and route
   valuable empirical observations to `record-finding`.
2. Navigate from Principles, Concepts, and Structures down to individual
   Findings only when evidence is needed.
3. After a meaningful batch of Findings, either:
   - use `consolidate-knowledge-base` for an interactive review; or
   - explicitly invoke `okfkb-gardening` for autonomous batch maintenance.
4. Run the project-prescribed index, lint, validation, and test commands. Skills
   discover those commands from the target project's `AGENTS.md` and linked
   guidelines rather than assuming one universal task runner.

## Progressive references

The [`okfkb`](okfkb/SKILL.md) skill keeps its main instructions compact and
loads detailed references only when needed:

- [Lifecycle and taxonomy](okfkb/references/lifecycle-and-taxonomy.md)
- [Finding quality](okfkb/references/finding-quality.md)
- [Consolidation judgment](okfkb/references/consolidation-judgment.md)
- [Navigation and maintenance](okfkb/references/navigation-and-maintenance.md)

For human-oriented guidance, see
[Maintain an OKFKB with agent skills](../docs/source/how-to/maintain-okfkb-with-skills.md)
and the
[HW debugging workflow tutorial](../docs/source/tutorials/okfkb-hw-debugging-workflow.md).
