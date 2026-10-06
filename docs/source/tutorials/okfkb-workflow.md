# Build and maintain an evidence-based knowledge base

`okfkb` organizes project knowledge into typed Markdown documents. It keeps
observations separate from explanations, plans and team rules, while retaining
links between them. The documents can be read by people and coding agents;
the CLI maintains navigation and checks structure.

This is the main OKFKB tutorial. You do not need to complete the generic OKF
or knowledge-graph tutorials first. You will create a knowledge base, record
bounded observations, consolidate them into a reusable explanation, navigate its
evidence and maintain the result after a later investigation.

## Understand what belongs in the knowledge base

Use the KB for non-trivial information that a future investigation or coding
agent would otherwise have to rediscover: measured behavior, tested boundaries,
rejected explanations, subsystem relationships and established procedures.
Link to source or existing documentation instead of paraphrasing everything.

The generic `okf-schema` layer validates Markdown metadata and maintains links.
`okfkb` adds a particular vocabulary and folder layout for empirical knowledge.
The following illustration contrasts those organizational choices; it does not
mean every generic graph is disorganized or every layered KB is reliable.

```{image} ../_static/generic-vs-okfkb-kb.svg
:alt: A generic collection of linked notes is contrasted with OKFKB folders that distinguish observations, explanations and team rules
:width: 100%
```

The document type answers **what kind of claim this is**. It is not an automatic
confidence score or a sequence every document must pass through.

| Question | Type and folder | Maintenance rule |
|---|---|---|
| What did we observe, under which conditions? | `Finding`, `findings/` | Preserve its recorded body and claim; later evidence is another Finding. |
| What explanation still needs testing? | `Hypothesis`, `hypotheses/` | Revise while investigating; retain confirmed/falsified history. |
| How will we test it? | `Experiment`, `experiments/` | Describe a reusable procedure; record each actual result as a Finding. |
| What explanation is useful to rely on within a stated scope? | `Concept`, `concepts/` | Update as evidence refines the explanation; retain provenance. |
| How do components and dependencies fit together? | `Structure`, `structures/` | Maintain the system description as understanding changes. |
| What rule has the team explicitly agreed? | `Principle`, `principles/` | Human agreement is required before creation or change. |
| How do we perform a repeatable operation? | `Playbook`, `playbooks/` | Maintain the procedure and its applicability. |
| What deliverable follows from this knowledge? | `Outcome`, `outcomes/` | Track planned, in-progress, done or cancelled work. |
| Which external source should we consult? | `Reference`, `reference/` | Preserve source identity and context. |

A Finding's `confidence` records the reporter's assessment of its evidence at
capture time. `kb_status` records its type-specific lifecycle. A Concept is not
correct merely because it is in `concepts/`; a `done` Outcome records work state,
not the quality of its verification. Read the evidence and the local schemas.

(okfkb-worked-example)=
## Prepare the project and the worked example

You need Python 3.10+, `uv` and a text editor. A coding agent is optional. In an
existing project, keep its dependency environment and work on a branch. For an
isolated walkthrough:

```bash
mkdir okfkb-demo
cd okfkb-demo
uv init --bare
uv add --dev okf-schema
```

Use the package release matching this documentation. For unreleased docs,
install the checkout you are evaluating instead of the registry dependency,
for example `uv add --dev /path/to/okf-schema`.

We will use a **fictional hardware investigation**. All measurements below are
training inputs, not results obtained by running the CLI. The board's clock
circuit is called a PLL; its ready signal indicates that its clock has locked.
The bootloader starts memory initialization after waiting for that clock.

The question is whether its fixed wait covers the measured cold-start timing.
You do not need hardware to record, link and navigate the supplied evidence.
The CLI cannot determine whether a physical measurement or explanation is true.

```{image} ../_static/okfkb-hw-debugging-overview-v2.svg
:alt: Investigation sessions produce Findings; consolidation creates explanations and plans; an agent navigates stable knowledge and follows links back to measurements, while Principles remain human-governed
:width: 100%
```

The overview connects the whole workflow. Use the worked steps below rather than
interpreting the layers as automatic promotion or approval.

```{code-block} bash
:caption: Initialize the knowledge base

uv run okfkb init knowledge
```

This creates `_schema/`, `index.md`, `log.md` and all nine content folders under
`knowledge/`. Empty folders are available without requiring a document in every
layer. Start by reading the installed schemas. The main path uses Findings, a
Concept and an Outcome; other types are available when their question arises.

(okfkb-capture)=
## Capture observations before explanations

Record the supplied timing observation:

```{code-block} bash
:caption: Capture PLL timing

uv run okfkb new-finding knowledge \
  --title "Cold PLL lock takes 800 microseconds in the captured trace" \
  --confidence medium --tags boot,pll \
  --context "Fictional board A, bootloader revision demo-1; one trace at 0 C and one at 25 C."
```

The command prints a path such as
`knowledge/findings/YYYY.MM.DD-HH.MM-cold-pll-lock-takes-800-microseconds-in-the-captured-trace.md`.
Its timestamp is generated in UTC. Preserve the actual filename. In later
snippets, **`PLL_FINDING_STEM` means that filename without `.md`**, including the
generated date/time prefix. Do not leave the placeholder in your documents.

The CLI creates frontmatter with `type`, `title`, `description`, `confidence`,
`context`, provenance under `generated`, and initial navigation/lifecycle fields.
Complete the body below that frontmatter while capturing the Finding:

```{code-block} markdown
:caption: knowledge/findings/PLL_FINDING_STEM.md — body

# Captured PLL lock timing

## Observation

In the supplied board-A traces, PLL lock occurs 800 microseconds after enable
at 0 C and 200 microseconds after enable at 25 C.

## Evidence

| Trace condition | Time from PLL enable to ready |
|---|---:|
| 0 C, revision demo-1 | 800 microseconds |
| 25 C, revision demo-1 | 200 microseconds |

These are fictional training observations. There is one trace per condition;
there is no population estimate or demonstrated root cause.

## Implications

Compare the lock times with the bootloader sequence. More measurements would
be needed to establish a temperature range or failure frequency.
```

Once the observation and its context have been recorded and reviewed, preserve
that body and claim. A human can capture it directly, or ask an agent:

> Use the installed `okfkb-record-findings` skill to capture the supplied timing
> observation in `knowledge/`. Preserve the measurement conditions and small
> sample size. Do not infer a root cause, promote a Concept or change an older
> Finding. Treat the supplied values as fictional walkthrough data.

Record the separate source-inspection observation:

```{code-block} bash
:caption: Capture bootloader wait

uv run okfkb new-finding knowledge \
  --title "Bootloader demo-1 waits 400 microseconds before memory initialization" \
  --confidence high --tags boot,pll \
  --context "Fictional source inspection of board-A bootloader revision demo-1."
```

Call its actual filename without `.md` **`WAIT_FINDING_STEM`**. Substitute both
real stems in the next body and all later snippets. Markdown body links include
`.md` and are relative to the file containing the link.

```{code-block} markdown
:caption: knowledge/findings/WAIT_FINDING_STEM.md — body

# Inspected bootloader wait

## Observation

The supplied demo-1 sequence enables the PLL, waits 400 microseconds, then starts
memory initialization. It does not check the PLL-ready signal in that interval.

## Evidence

The fictional inspected sequence is: enable PLL; delay 400 microseconds; start
memory initialization. Compare it with the
[captured PLL timing](PLL_FINDING_STEM.md).

## Implications

The fixed delay is shorter than the cold trace's measured lock time. This
inspection alone does not demonstrate the cause of an intermittent boot failure.
```

The two records have different evidence and limits. Do not combine them into
one observation titled “PLL causes boot failures.” An untested explanation
belongs in a Hypothesis, with an Experiment if a repeatable test is needed.

```{code-block} bash
:caption: Update and validate the captured observations

uv run okfkb update knowledge
uv run okfkb validate knowledge --check-links
```

`update` refreshes indexes and generated navigation metadata. It does not
complete evidence or approve claims. `validate` checks structure and schemas;
`--check-links` also checks annotated file targets. KB validation treats warnings
as failures, so read and resolve the reported path rather than deleting evidence.

## Distinguish a related link from derivation evidence

The source-inspection body links to the measurement. After update:

- its generated `links` includes the measurement's bundle-relative `.md` path;
- the measurement's generated `backlinks` includes the source-inspection file;
- neither link, by itself, states that one observation was derived from the other.

A synthesis uses **authored `derived_from`** to state which documents support it.
These IDs are bundle-relative paths **without `.md`**. The tool computes the
reciprocal **`derives_to`** on the source documents. Do not edit the generated
`links`, `backlinks` or `derives_to` arrays manually.

| Relationship | You author | The tool computes |
|---|---|---|
| Related reading | A relative Markdown body link, including `.md` | Bundle-relative `links` and `backlinks`, including `.md` |
| Derivation/provenance | `derived_from: [findings/actual-stem]` | `derives_to: [concepts/cold-pll-wait]` on the source Finding |

The generic [links and backlinks exercise](knowledge-graph.md) covers the first
row on its own. It is optional; this walkthrough uses both relationships.

## Consolidate a bounded explanation

For this exercise, review and accept this limited inference: the 400-microsecond
wait does not cover the supplied 800-microsecond cold trace. It does not establish
behavior for every board or explain every startup failure.

Create `knowledge/concepts/cold-pll-wait.md` with the following complete document.
Replace `PLL_FINDING_STEM` and `WAIT_FINDING_STEM` with their actual stems. The
provenance date below belongs to the fictional walkthrough; use the actual
creation date and producer for real project knowledge.

```{code-block} markdown
:caption: knowledge/concepts/cold-pll-wait.md

---
type: Concept
title: Fixed wait is shorter than the observed cold PLL lock time
description: The demo-1 fixed wait does not cover the captured board-A cold timing.
generated:
  at: '2026-10-19T12:00:00Z'
  by: human:tutorial
kb_status: active
tags: [boot, pll]
derived_from: [findings/PLL_FINDING_STEM, findings/WAIT_FINDING_STEM]
---

# Fixed wait and observed cold PLL timing

The captured cold lock time is 800 microseconds; the inspected boot sequence
waits 400 microseconds before starting memory initialization. The fixed wait
therefore does not cover this observed timing on board A with revision demo-1.

The evidence is the [timing observation](../findings/PLL_FINDING_STEM.md) and
[source inspection](../findings/WAIT_FINDING_STEM.md). This explanation is scoped
to those inputs. It does not establish a board-independent timing bound or prove
the cause of every boot failure.
```

A Concept is a maintained explanation, not a rewritten Finding. Later evidence
can refine its text and provenance while the underlying observations stay intact.
Promotion needs judgment about evidence quality, scope, counter-evidence and
reuse value; a particular number of Findings is not sufficient.

For an agent-assisted review, choose the workflow explicitly:

| Skill | Use it for |
|---|---|
| `okfkb` | Choosing document types and navigating the knowledge lifecycle. |
| `okfkb-record-findings` | Capturing one bounded observation and its context. |
| `okfkb-distill` | Reviewing contradictions and proposed synthesis interactively before mutations. |
| `okfkb-gardening` | An explicitly requested autonomous maintenance pass under project rules; it may update non-Principle layers. |

For example, ask `okfkb-distill` to review whether the two Findings justify this
bounded Concept. Do not ask it to manufacture agreement. Neither the CLI nor a
skill invocation proves that the explanation is correct. A Principle would be
an agreed normative rule; only create or change one after explicit human agreement.

## Keep planned work separate from knowledge

The Concept motivates investigating bounded polling instead of relying on the
fixed delay. That proposed deliverable belongs in an Outcome, not in a Finding
that claims a fix already worked.

```{code-block} markdown
:caption: knowledge/outcomes/bounded-pll-polling.md

---
type: Outcome
title: Evaluate bounded PLL-ready polling
description: Implement and test a readiness check for the demo board.
generated:
  at: '2026-10-19T12:00:00Z'
  by: human:tutorial
kb_status: planned
deliverable: A reviewed readiness-check change and scoped verification results.
derived_from: [concepts/cold-pll-wait]
---

# Evaluate bounded PLL-ready polling

Investigate replacing the fixed wait with a PLL-ready check and a bounded timeout.
Define the timeout policy and failure handling before implementation. Preserve
results as new Findings; do not infer success from this plan.

The motivation is the [timing explanation](../concepts/cold-pll-wait.md).
```

```{code-block} bash
:caption: Generate the evidence graph

uv run okfkb update knowledge
uv run okfkb validate knowledge --check-links
```

Each source Finding now has `derives_to: [concepts/cold-pll-wait]`. The Concept
has a generated edge to the Outcome. The ordinary Markdown links also produce
`links` and `backlinks`. These are navigable relationships, not automated
verification that the synthesis or plan is sound.

Append a dated entry to `knowledge/log.md` explaining the new Concept, its
scope and evidence, the planned Outcome and the checks actually run. Merge into
an existing date section when appropriate; preserve earlier entries. The log
is authored history and is not regenerated by `update`.

## Read from the explanation down to evidence

A later engineer or agent should not need to read every historical Finding.
Start with the log and root index, then select the stable knowledge relevant to
the task:

```{code-block} bash
:caption: Navigate the resulting knowledge base

uv run okfkb read concepts knowledge --status active --format titles
uv run okfkb search "PLL" knowledge --tier findings --format paths
uv run okfkb get concepts/cold-pll-wait knowledge
uv run okfkb query "type:finding confidence:>=medium tag:pll" knowledge --format paths
uv run okfkb query "finding[tag=pll] ^ concept" knowledge --format paths
```

`read` selects a tier, `search` locates likely documents, `get` fetches an exact
node and `query` selects metadata or follows graph edges. In arrow queries,
`->` follows `links`, `<-` follows `backlinks` and `^` follows generated
`derives_to`. To inspect one measurement fully, run `get` with its actual
`findings/<generated-filename>.md` path and the same explicit `knowledge` root.

(okfkb-later-results)=
## Record later results without rewriting history

Suppose a later controlled test of a revised bootloader reports zero observed
failures in 100 cycles at -10 C. Record a **new Finding** with the revision,
procedure, sample size and result. Zero observed failures in that sample does
not demonstrate a zero failure probability or unrestricted temperature coverage.

For this fictional continuation:

1. Preserve the two original Finding bodies and claims.
2. Add the new result as evidence to the existing Concept if it refines the same
   explanation. Keep its applicable versions and limits clear.
3. Move the Outcome to `done` only if the agreed deliverable and verification
   scope are actually complete. A planned change is not a successful test.
4. Keep the Concept `active` while its explanation remains applicable. A fixed
   incident does not make the causal history `resolved` or `deprecated` by itself.
5. Log the material semantic changes, run update and validate, and review the diff.

If later evidence disagrees, first compare version, environment and measurement
conditions. Different revisions can explain different observations without
contradiction. Use contradiction metadata only for incompatible claims under
comparable conditions; use supersession for a replacement record. The exact
fields/statuses come from the installed schemas. Preserve both bodies and use a
Hypothesis/Experiment when a targeted test is needed to settle the disagreement.

## Make the KB usable by coding agents

Install the skill family in a location your agent discovers:

```{code-block} bash
:caption: Install the knowledge skills

uv run okfkb install-skills --local-agents
```

This installs `okfkb`, `okfkb-record-findings`, `okfkb-distill` and
`okfkb-gardening` under `.agents/skills/`. For Copilot project skills use
`--local-copilot`; an explicit destination is a skills directory, not an
inferred project root. Installing skills does not populate the knowledge base
or register project instructions automatically.

The scaffold does not install an agent guideline file. Add a local guideline,
for example `.agents/guidelines/knowledge.md`, based on the rules above and
register it in `AGENTS.md`. Point to the KB root and schema directory; require
immutable recorded Finding bodies, explicit provenance, human-governed Principles,
reviewed generated diffs and authored semantic log entries. Agents should start
with relevant stable knowledge, then follow evidence only as needed.

For a `uv` project using `just`, a minimal maintenance harness is:

```{code-block} make
:caption: justfile — knowledge targets

knowledge-refresh:
    uv run okfkb update knowledge

knowledge-check:
    uv run okfkb validate knowledge --check-links
    uv run okf-schema lint --path knowledge --check
```

Add the check target to the existing preflight alongside real project tests.
The refresh target writes generated views; review its diff locally. The check
target validates documents/targets and checks frontmatter formatting and graph
metadata; it is not a complete index-freshness or semantic-correctness check.
Keep the project tests and dependency lockfile in the normal harness as well.

## Further reading

- [Design rationale](../explanation/okfkb-choices.md): why roles, evidence history,
  mutable synthesis and explicit navigation were chosen, and their trade-offs.
- [Setup reference](../how-to/setup-okfkb.md): schema fields and configuration details.
- [Agent maintenance workflows](../how-to/maintain-okfkb-with-skills.md): capture,
  interactive distillation, autonomous gardening and governance boundaries.
- [KB command reference](../reference/kb-commands.md): navigation flags and query grammar.
- [Bootstrap an existing KB](../how-to/bootstrap-knowledge-base.md): migrating
  existing notes without inventing provenance or silently rewriting history.
- [Generic OKF links](knowledge-graph.md): an optional focused exercise on body
  links and backlinks outside the OKFKB lifecycle.
