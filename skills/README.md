# Agent skills

This directory contains agent-facing instructions for the three layers provided
by `okf-schema`. The skills complement the CLI: the CLI performs deterministic
file operations and validation, while the skills teach an agent when and why to
use each operation.

## Skill Scopes

These names describe different scopes, not interchangeable names for the same
tool:

| Scope | What it is | Primary command | Use it for |
|---|---|---|---|
| **Generic OKF tooling** | The foundational `okf-schema` validator, linter, indexer, and Python API for ordinary OKF bundles. | `okf-schema` | Bundle structure, schemas, frontmatter, links, indexing, linting, and conformance. |
| **Knowledge-base subset** | The opinionated `okfkb` bundle pattern and lifecycle for Findings, Hypotheses, Experiments, Concepts, Structures, Principles, Playbooks, and Outcomes. | `okfkb` or `okf-schema kb` | Capturing and maturing engineering knowledge while preserving evidence and human governance. |
| **Requirements subset** | The separate `okfreq` bundle pattern for stakeholder and software requirements, lifecycle, derivation, verification markers, coverage, and traceability. | `okfreq` | Authoring and auditing requirements; it is not a knowledge-base tier and does not replace `okfkb`. |

Both subsets build on the generic layer, but their documents and workflows stay
separate. Use `okf-schema` for mechanics, `okfkb` for knowledge-lifecycle
semantics, and `okfreq` for requirements traceability. A project may use either
subset, both subsets, or only generic OKF bundles.

## Available skills

| Skill | Purpose | Use it when |
|---|---|---|
| [`okf-schema`](okf-schema/SKILL.md) | Operate the tool: initialize, validate, lint, index, inspect, and troubleshoot generic OKF bundles and schemas. | The task concerns CLI/API usage, OKF conformance, JSONSchema validation, frontmatter, links, or bundle structure. |
| [`okfkb`](okfkb/SKILL.md) | Understand and route the opinionated knowledge lifecycle: capture immutable Findings, choose a layer, consolidate evidence, navigate top-down, and protect human-governed Principles. | The task concerns what knowledge belongs in the KB, how it should mature, or which specialized workflow should handle it. |
| [`okfkb-gardening`](okfkb-gardening/SKILL.md) | Run an explicit, autonomous, zero-prompt maintenance pass: repair graph mechanics, reconcile Finding lifecycles, consolidate semantic knowledge, surface stale content, and validate the result. | The user explicitly asks to garden, refresh, consolidate, or maintain an OKFKB bundle. |
| [`okfkb-record-findings`](okfkb-record-findings/SKILL.md) | Record one immutable empirical Finding after an investigation. | A debugging or investigation session produced one durable observation. |
| [`okfkb-distill`](okfkb-distill/SKILL.md) | Interactively review Findings, contradictions, experiments, and promotions. | A human is ready to consolidate a batch of Findings. |
| [`okfreq`](okfreq/SKILL.md) | Understand and route the living-requirements lifecycle from stakeholder intent through software behavior to source, tests, and reports. | The task concerns setting up, authoring, implementing, tracing, or maintaining `okfreq` requirements. |
| [`okfreq-gardening`](okfreq-gardening/SKILL.md) | Audit and safely improve requirement traceability, hierarchy, coverage, and configuration. | The user explicitly asks to garden, audit, refresh, or reconcile an `okfreq` bundle. |

The `okfreq-gardening` skill is the requirements-oriented workflow. It operates
on `okfreq` bundles and must not be used to classify or promote `okfkb`
knowledge documents. The `okfkb` skill is the knowledge-base router; it is not
the requirements subset.

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
    okfkb-record-findings*     okfkb-distill*           okfkb-gardening
      one empirical note     interactive review         autonomous batch
              │                       │                        │
              └───────────────────────┼────────────────────────┘
                                      v
                                  okf-schema
                         deterministic CLI + validation
```

`okfkb-record-findings` and `okfkb-distill` are bundled project skills deployed
by `okfkb install-skills` and packaged in this directory:

- **`okfkb-record-findings`** quickly captures one dated, immutable empirical Finding.
- **`okfkb-distill`** interactively reviews contradictions and
  promotions, confirming mutations with a human.

The repository-level `okfkb` skill routes to those specialized skills when they
are available. Its references provide the fallback lifecycle guidance.

## How the requirements skills fit together

The requirements subset follows a separate path. `okfreq` owns requirement
identities, hierarchy, lifecycle, derivation, implementation/test markers, and
coverage; the generic `okf-schema` layer still performs the underlying OKF
validation and Markdown mechanics.

```text
          ┌────────────────────────────────────┐
          │            okf-schema              │
          │ generic OKF mechanics + validation │
          └───────────────┬────────────────────┘
                          │
                          v
          ┌────────────────────────────────────┐
          │             okfreq                 │
          │ requirements + traceability CLI    │
          └───────────────┬────────────────────┘
                          │
          ┌───────────────┼────────────────────┐
          │               │                    │
          v               v                    v
create requirements  derive StRS → SwRS   trace markers
     and lifecycle      hierarchy         and coverage
          │               │                    │
          └───────────────┼────────────────────┘
                             v
                      okfreq-gardening
                      audit + reconcile
```

Use this requirements flow only for an `okfreq` bundle. Do not place
requirements in the `okfkb` knowledge tiers merely because both formats use
OKF Markdown, and do not use the `okfkb` lifecycle skills as a substitute for
requirements traceability.

## Choosing a skill

- Start with **`okf-schema`** for mechanics: “Why does validation fail?” or
  “How do I rebuild indexes?”
- Start with **`okfkb`** for semantics: “Is this a Finding or Concept?” or
  “Should these observations be promoted?”
- Start with **`okfreq`** for requirements semantics: “Is this stakeholder
  intent or observable software behavior?” or “How should this requirement be
  connected to code and tests?”
- Invoke **`okfkb-gardening`** for periodic upkeep after Findings accumulate.
  It does not ask questions during the run and may update all KB layers except
  Principles.

Principles remain human-governed in every workflow. An agent may propose a
Principle with rationale and evidence, but it must not mutate one without
explicit human agreement.

## Recommended maintenance rhythm

1. During investigations, let `okfkb` assess durable discoveries and route
  valuable empirical observations to `okfkb-record-findings`.
2. Navigate from Principles, Concepts, and Structures down to individual
   Findings only when evidence is needed.
3. After a meaningful batch of Findings, either:
   - use `okfkb-distill` for an interactive review; or
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
