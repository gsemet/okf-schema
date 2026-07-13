---
name: okfkb-gardening
description: 'Autonomously refresh and consolidate an OKFKB knowledge base in one zero-prompt run: repair graph maintenance issues, reconcile Finding contradictions and supersession, update or promote semantic knowledge, create open investigations and operational/planning documents when justified, detect stale knowledge, and validate using project-prescribed checks. Use only when the user explicitly asks to garden, refresh, consolidate, or maintain an OKFKB knowledge base.'
metadata:
  keywords: [okfkb, gardening, consolidation, maintenance, contradictions, promotion, obsolescence, knowledge-base]
  url: https://github.com/gsemet/okf-schema
---

# OKFKB gardening

Perform a complete recurring maintenance pass without pausing for questions.
The user supplies only the intent to garden and, optionally, a KB path. Infer
the rest from the repository, its rules, schemas, and evidence.

This skill is **explicit-invocation only**. Do not launch a full gardening pass
proactively during unrelated work.

## Non-negotiable boundaries

- Never edit or delete a Finding's body or claim. Only append schema-valid
  lifecycle metadata.
- Never create, edit, activate, deprecate, or supersede a Principle. Put
  potential Principles in the final chat report as proposals with evidence.
- Never discard or overwrite unrelated user changes.
- Never invent fields or statuses. The bundle's `_schema/` files and local rules
  are authoritative.
- Do not ask questions mid-run. Resolve conservatively, defer uncertain actions,
  and report them at the end.
- Do not write a maintenance report file. Add `log.md` entries only for
  significant semantic changes.

## Phase 1 — Discover rules and scope

1. Resolve the KB root from an explicit path or workspace signals (`_schema/`,
   `index.md`, and tier directories). If no unique root can be found, stop and
   report the ambiguity; do not guess across multiple bundles.
2. Read the nearest `AGENTS.md` and every linked KB guideline relevant to the
   bundle.
3. Read the task runner and scripts needed to discover required index, lint,
   validation, and test commands. Commands may be `just`, `make`, or project
   shell scripts; do not hardcode a universal sequence.
4. Read the local schemas and record allowed types, fields, statuses, and
   relationship names.
5. Inspect repository status so pre-existing work can be distinguished from
   gardening changes.

## Phase 2 — Establish the baseline

Run the project-prescribed non-destructive validation checks. Record baseline
errors and warnings. If the KB is too malformed to inspect safely, limit the run
to structural repair and report that semantic consolidation was skipped.

Read frontmatter before bodies. Build an inventory of:

- active, contradicted, and superseded Findings;
- open Hypotheses and active Experiments;
- active/deprecated Concepts, Structures, and Playbooks;
- Outcomes by status;
- Principles for conflict detection only;
- links, backlinks, provenance, contradiction, and supersession edges.

## Phase 3 — Repair graph mechanics

1. Detect broken frontmatter and Markdown links.
2. Use git history to identify confident renames or moves. Apply only unambiguous
   repairs; defer uncertain targets.
3. Propagate valid supersession redirects using project tooling when available.
4. Refresh generated links, backlinks, and indexes according to project rules.
5. Preserve YAML comments and unknown extension fields.

## Phase 4 — Consolidate Findings

Cluster related Findings by claim, scope, context, tags, and graph edges. For
each cluster:

1. Detect genuine contradiction only after considering version, environment,
   configuration, and tested scope.
2. Distinguish contradiction from supersession.
3. Append reciprocal lifecycle metadata using local schema fields.
4. If disagreement remains unresolved, create or update a Hypothesis and a
   focused Experiment when a reproducible test can settle it.
5. If evidence converges into reusable understanding, create or update the
   appropriate Concept or Structure. Promotion is qualitative agent judgment,
   not a fixed Finding count. Preserve provenance through schema-valid fields.

When useful, delegate independent evidence clusters or link-coherence pairs to
small read-only subagents with bounded concurrency. The gardening agent remains
responsible for checking their conclusions against schemas and source evidence.

## Phase 5 — Refresh living layers

Review active Concepts, Structures, Playbooks, and Outcomes against current
evidence:

- update Concepts and Structures in place when evidence refines the same idea;
- retain and extend provenance links;
- deprecate stale semantic documents rather than deleting them;
- create or update Playbooks for evidence-backed repeatable workflows;
- supersede obsolete Playbooks when history remains useful;
- create or update Outcomes for concrete deliverables justified by the KB;
- do not mark an Outcome complete without evidence;
- flag stale or conflicting Principles but do not mutate them.

For every potential Principle, collect proposed wording, rationale, supporting
Finding IDs, and the human decision needed. Include it only in the final report.

## Phase 6 — Record significant events

Add a concise dated `log.md` entry only when the run made a semantic change:

- confirmed contradiction or supersession;
- Concept or Structure promotion, deprecation, or material revision;
- creation of a Hypothesis, Experiment, Playbook, or Outcome that changes the
  KB's current understanding or work;
- a human-approved Principle change already present before this run.

Do not log formatting, index refreshes, link-only repairs, validation runs, or
no-op gardening.

## Phase 7 — Validate and repair

Run the complete validation sequence discovered from `AGENTS.md` and project
rules. If checks fail because of gardening changes:

1. diagnose and repair the root cause;
2. rerun the smallest relevant check, then the complete required sequence;
3. make at most three focused repair attempts for the same failure;
4. if unresolved, preserve the diff and clearly report remaining failures.

Do not claim success when checks fail. Do not revert unrelated pre-existing
changes.

## Final chat report

Present one concise report after the run:

1. **Scope and validation** — KB root, prescribed checks, baseline and final
   results.
2. **Mechanical repairs** — broken links, redirects, indexes, and deferred
   ambiguities.
3. **Finding lifecycle** — contradictions and supersession applied.
4. **Consolidation** — semantic documents created, updated, or deprecated, with
   supporting evidence.
5. **Open investigations** — Hypotheses and Experiments created or still needed.
6. **Operations and planning** — Playbooks and Outcomes changed.
7. **Principle proposals** — recommendations requiring explicit human agreement.
8. **Unresolved issues** — uncertain judgments and validation failures.

If a section has no entries, say `None`; do not fabricate activity.