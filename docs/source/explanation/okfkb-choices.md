# Why OKFKB separates evidence, explanations and decisions

OKFKB is an opinionated knowledge-base profile built on the generic OKF tooling.
Its folders and schemas distinguish empirical observations, maintained knowledge,
investigation plans, operational procedures and agreed rules. This page explains
the reasons and costs of those choices.

For the concepts, illustrations, commands and a complete worked investigation,
start with [Build and maintain an evidence-based knowledge base](../tutorials/okfkb-workflow.md).
The tutorial is the single OKFKB learning path; it does not require the generic
graph exercise first.

## Separate document roles instead of treating every note as equivalent

The same investigation can produce several kinds of statement:

- a trace recorded 800 microseconds under particular conditions;
- the fixed wait may be too short;
- the wait does not cover the measured timing in that configuration;
- the team plans to implement and test another readiness check; and
- the team agrees a policy for hardware-ready checks.

Putting these statements in one evolving note makes their ownership and status
harder to distinguish. A reader needs to know whether a sentence is a historical
observation, an explanation to investigate, current understanding, planned work
or an agreed rule. OKFKB assigns these roles to Finding, Hypothesis, Concept,
Outcome and Principle respectively. Structure, Experiment, Playbook and Reference
cover system relationships, repeatable tests/procedures and external sources.

The comparison below shows how explicit document roles help readers distinguish
evidence, explanations and rules. A generic graph can also be organized; OKFKB
makes these distinctions part of the shared profile.

```{image} ../_static/generic-vs-okfkb-kb.svg
:alt: Generic linked notes compared with OKFKB document roles for observations, explanations and agreed rules
:width: 100%
```

These roles are not a universal maturity ladder. An Outcome is not a more
confident Concept, and a Principle is not automatically justified by a high
Finding count. `confidence` and each type's `kb_status` remain separate metadata.
The type also does not validate a statement's truth.

The cost is choosing a type and maintaining relationships between documents.
For a small collection of unrelated notes, a simpler generic OKF bundle may be
sufficient. The profile is useful when preserving evidence and revisiting an
investigation matters enough to justify that structure.

## Preserve observations while allowing explanations to change

A Finding records what was observed and believed under a specific context at
capture time. Its body and claim should remain historical. If later evidence
changes the conclusion, rewriting the old observation would erase what was
actually available to the earlier investigation.

Concepts and Structures have a different job: they present the current reusable
explanation or system model. They can change as evidence accumulates. Their
provenance should make it possible to follow that synthesis back to the records
that support or limit it. This avoids requiring every reader to reconstruct the
entire investigation before using the current explanation.

The CLI generates dated Finding filenames and validates metadata, but ordinary
Markdown remains editable. Immutability is a maintenance policy reinforced by
agent instructions, review and version control; it is not a filesystem access
restriction. Humans and agents can both record Findings. Tools can preserve
history only when the project's workflow respects that boundary.

The hardware investigation below illustrates the division of work. Sessions
capture Findings; consolidation maintains explanations and plans; readers and
agents follow links back to the measurements. Principles remain subject to human
agreement. These are related activities, not a required sequence for every note.

```{image} ../_static/okfkb-hw-debugging-overview-v2.svg
:alt: Hardware investigation sessions capture Findings, consolidation produces reusable knowledge and plans, and agents navigate evidence while Principles remain human-governed
:width: 100%
```

## Distinguish contradiction from a change of scope

Different results do not necessarily contradict one another. A different board,
software revision, environment or measurement procedure may explain the change.
Collapsing those contexts into a single confidence label loses information.

When claims are incompatible under materially comparable conditions, the KB can
retain both records and represent contradiction in lifecycle metadata. When a
new record intentionally replaces an earlier account, supersession expresses
that relation instead. Neither relation is a license to erase inconvenient data.
An unresolved disagreement can motivate a Hypothesis and an Experiment rather
than an immediate promotion or a guessed winner.

This requires judgment about context and evidence quality. Schema validation
can check permitted values and some paths; it cannot decide whether two physical
measurements are comparable or whether a result is reproducible.

## Keep navigation links distinct from derivation provenance

An ordinary body link means that another document is relevant reading in that
sentence. It does not, by itself, say that a claim was derived from that document.
OKFKB retains ordinary Markdown links and adds authored `derived_from` provenance.

Generated `links`/`backlinks` expose body references in both directions.
Generated `derives_to` is the reciprocal view of `derived_from`. This lets a
reader move from a conclusion to its evidence or from an observation to the
conclusions that depend on it, without manually maintaining both edge directions.

The current conventions are explicit but different: body links include `.md`
and are relative to their source document; `derived_from` uses bundle-relative,
extensionless document IDs. The distinction needs teaching and can cause path
mistakes. Local schemas and opt-in target checking help make those mistakes
visible. Generated edges remain declared provenance, not proof that the source
supports the claim.

## Promote through evidence review rather than a fixed count

Repeated Findings may be copies of the same underlying observation. A collection
of similar records can also omit relevant counter-evidence or cover only one
configuration. Counting records cannot establish that an explanation is reusable.

Consolidation therefore considers evidence quality and independence, scope,
uncertainty, counter-evidence, existing knowledge and the value of a synthesis.
A Concept or Structure may be justified directly from Findings when that review
supports it; Hypotheses and Experiments are available when uncertainty requires
further investigation. They are not mandatory intermediate paperwork.

The cost is that promotion cannot be reduced to a deterministic CLI operation.
Interactive distillation supports human review of proposed mutations. Explicitly
invoked gardening allows autonomous maintenance of non-Principle layers under
project rules. Neither mode guarantees correct judgment; inspect the resulting
evidence trail and diff.

## Keep governance distinct from empirical inference

A measurement describes what happened. A Principle says what the team agrees
should be done. Evidence can motivate a rule without deciding its trade-offs,
exceptions or authority. OKFKB therefore reserves creation and modification of
Principles for explicit human agreement.

This boundary does not prohibit an agent from proposing a Principle with its
rationale, evidence and implications. It prevents a synthesis step from silently
turning an engineering suggestion into policy. Outcomes and Playbooks also remain
separate: planned work is not demonstrated success, and a procedure is not a
universal rule.

## Prefer inspectable files while accepting maintenance costs

Markdown bodies support explanations and evidence context alongside structured
YAML metadata. The profile keeps documents, schema changes and relationships in
files that can be reviewed together with the project. It does not require a graph
database or hosted retrieval service.

A database or wiki can also support structured evidence and history. Those
systems may be preferable for concurrent editing, centralized access control,
large-scale queries or other project constraints. File-based storage instead
makes the project's filesystem, version control and validation harness part of
the operating model. It requires a strategy for concurrent changes, naming,
regeneration and keeping authored guidance current.

Frontmatter is a compact entry point for selecting documents by type, status,
context and provenance. It does not guarantee how much an agent will read or
how well it will understand a claim. `read`, `search`, `get` and `query` offer
different retrieval scopes; the agent still needs a sensible reading strategy
and should stop when it has enough context for the task. Large tiers and broad
queries can still return more text than is useful.

## Separate generated views from semantic history

Indexes and graph arrays are derived views. Running `okfkb update` refreshes them,
including supported superseded-link rewrites. Review the resulting diff. The
maintained `log.md` has another purpose: significant promotions, contradictions,
revisions and decisions should explain what changed and why. The tool does not
invent that history during formatting or indexing.

A valid bundle establishes structural consistency within the implemented checks.
It does not establish completeness, scientific validity, correctness of an agent's
reasoning or that a planned Outcome succeeded. Real experiment/test execution,
review and governance remain part of the project's workflow.

For practical procedures, use the [single OKFKB tutorial](../tutorials/okfkb-workflow.md)
and [agent-maintenance guide](../how-to/maintain-okfkb-with-skills.md).
For exact fields and commands, use the [setup reference](../how-to/setup-okfkb.md)
and [KB CLI reference](../reference/kb-commands.md).
