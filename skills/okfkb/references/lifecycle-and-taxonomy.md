# OKFKB lifecycle and taxonomy

OKFKB stratifies knowledge so an agent can distinguish evidence, open questions,
stable understanding, governance, operations, plans, and external sources before
reading full documents.

## Layers and document types

| Layer | Type | Default folder | Question answered | Lifecycle |
|---|---|---|---|---|
| Storage | `Finding` | `findings/` | What did we observe at time $T$? | Immutable body; lifecycle metadata may be appended. |
| Testing | `Hypothesis` | `hypotheses/` | What testable explanation might be true? | Mutable until confirmed or falsified. |
| Testing | `Experiment` | `experiments/` | How can we test it reproducibly? | Mutable while proposed/active; results become Findings. |
| Semantic | `Concept` | `concepts/` | What stable idea explains this? | Living document; update with evidence or deprecate. |
| Semantic | `Structure` | `structures/` | How is this system composed or how does it work? | Living document; update with evidence or deprecate. |
| Governance | `Principle` | `principles/` | What must, should, or must not be done? | Human-agreed and stable; never agent-decided. |
| Operational | `Playbook` | `guides/` | How do we reproducibly achieve a result? | Mutable while active; deprecate or supersede. |
| Planning | `Outcome` | `outcomes/` | What deliverable do we intend to achieve? | Tracks planned work and progress. |
| Lookup | `Reference` | `reference/` | What does an external source say? | Immutable representation of an external source. |

The local `_schema/` directory is authoritative when fields or statuses differ.
For the bundled schema, use `derived_from` on Concepts and Structures and
`supported_by` on Principles. Do not substitute prose-era aliases such as
`promoted_from` unless the local schema explicitly permits them.

## Normal knowledge flow

```text
observation ──> Finding ──┬──> Concept ──┬──> Structure
                          │               ├──> Playbook
                          │               └──> Principle proposal ──> human agreement
                          └──> Hypothesis ──> Experiment ──> Finding

Concept / Structure / Playbook ──> Outcome
Reference ──> evidence context for any appropriate layer
```

Direct promotion from Findings to Concept or Structure is valid when the
evidence already converges. Hypothesis and Experiment are not ceremonial gates;
use them when a claim remains uncertain or a contradiction needs a discriminating
test.

## Mutability rules

### Immutable records

- A Finding's claim and body freeze after creation.
- A Reference preserves what the external source said at capture time.
- Corrections are new records connected by contradiction, supersession, or a
  newer Reference version.

### Living knowledge

- Concepts and Structures may be updated in place as understanding changes.
- Preserve `derived_from` evidence and add new supporting IDs.
- Log material semantic revisions. If the subject itself has been replaced,
  deprecating the old document and creating a new one may be clearer than
  rewriting it into a different idea.
- Playbooks evolve with operational experience. Supersede an old workflow when
  retaining it is useful for traceability.

### Human-governed knowledge

- Findings may support a Principle, but they cannot establish one.
- Agents may present a Principle proposal with rationale and evidence.
- Only explicit human agreement permits a Principle mutation.

## Type-selection tests

- It happened under stated conditions: **Finding**.
- It might explain observations and can be falsified: **Hypothesis**.
- It is a reusable test designed to produce evidence: **Experiment**.
- It defines an idea independent of one implementation: **Concept**.
- It describes parts, relationships, architecture, or mechanics: **Structure**.
- It prescribes a normative rule backed by human authority: **Principle**.
- It gives repeatable operational steps: **Playbook**.
- It commits to making or changing something: **Outcome**.
- It mirrors a paper, website, standard, or lookup source: **Reference**.

One document should have one primary purpose. Split mixed documents rather than
using a convenient but inaccurate type.