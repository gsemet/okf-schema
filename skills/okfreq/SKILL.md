---
name: okfreq
description: 'Understand, set up, author, implement, and maintain an okfreq requirements base that connects stakeholder intent to observable software behavior, source code, tests, and traceability reports. Use when the user mentions okfreq, living requirements, StRS or SwRS authoring, requirement derivation, implementation or test markers, requirement coverage, or requirements lifecycle; route explicit brownfield audits to okfreq-gardening.'
metadata:
  keywords: [okfreq, requirements, living-requirements, traceability, StRS, SwRS, implementation-markers, test-markers, coverage]
  url: https://github.com/gsemet/okf-schema
---

# okfreq

Use `okfreq` to maintain a living requirements specification beside the code.
Its goal is to keep stakeholder intent connected to observable software
behavior, implementation, tests, and reviewable gap reports as the project
changes. Teach that model, identify the user's intent, then use the smallest
appropriate workflow.

This skill explains the **requirements and traceability lifecycle**. Use the
`okf-schema` skill for generic OKF conformance, schemas, frontmatter mechanics,
or implementation details of the underlying tool.

## Installation

Install or upgrade the Python CLI tool with `uv`:

```bash
uv tool install okf-schema
uv tool upgrade okf-schema
```

This tool installation exposes the `okf-schema`, `okfkb`, and `okfreq` console
commands. It is separate from installing agent skill folders: use
`okfreq install-skills` to copy the packaged `okfreq` skill family into an
agent's skills directory.

## Start with project rules

1. Locate the requirements bundle. Prefer an explicit path, then a top-level
   `requirements/`, then `.agents/requirements/`, and finally
   `.github/requirements/`. The bundle root is the directory that owns
   `config.yml`; its requirement documents and schemas normally live in
   `tiers/`.
2. Read the nearest `AGENTS.md` and any requirements guideline it registers.
3. Prefer the bundle's own
   `<bundle>/guidelines/requirements.guidelines.md`. This in-project guideline
   is authoritative because it can define local paths, scopes, commands, and
   review rules.
4. If that file is absent, read
   [the bundled requirements guideline](references/requirements.guidelines.md)
   as the baseline. Resolve project-specific paths, scopes, and quality commands
   from `config.yml`, `AGENTS.md`, and the project itself rather than assuming
   that example names apply universally.
5. Before changing requirements, read `config.yml` and every schema under
   `tiers/_schema/`. Local configuration and schemas define the actual levels,
   hierarchy, IDs, lifecycle values, markers, scopes, and allowed fields.

## The goal of okfreq

`okfreq` demonstrates an agent-friendly way to keep production-level,
structured living requirements that stay aligned with code and tests and expose
traceability gaps. It does not pretend that generated files are the ultimate
source of stakeholder truth.

Treat the requirements base as a maintained, reviewable representation of what
the implemented system is expected to do. Compare it with the original intent,
then explicitly accept or adapt it as implementation teaches the team more.
Requirements may evolve; silent drift must not.

A useful requirement states one agreed behavior or constraint precisely enough
that a developer can implement it and a tester can decide whether it is
satisfied. It is not an issue title, design choice, code comment, or task.

## Core model

- **StRS captures stakeholder intent.** It states a stakeholder-observable goal
  or use case and preserves the underlying user need without prescribing the
  implementation.
- **SwRS captures observable software behavior.** It refines one or more StRS
  requirements into bounded behavior that code can implement and tests can
  observe.
- **Authored derivation points upward.** Author `derives_from`; let `okfreq`
  compute reverse `derived_by` links.
- **Leaf requirements connect to evidence.** Place `@implements_req <ID>` near
   the relevant production behavior and `@tests_req <ID>` once in each relevant
   test file. StRS never receives implementation markers; in the stricter
   `linked-swrs-and-validation-test` mode, a direct `@tests_req <StRS-ID>` marker
   defines a stakeholder validation test.
- **Markers are links, not proof.** A test marker says where verification lives,
  not whether the test ran or passed. Run the project's real test suite.
- **Coverage and reports are generated views.** Keep implementation coverage,
  test-link coverage, structural health, and lifecycle counts separate; do not
  collapse them into a misleading success score.
- **Lifecycle is explicit.** Creating, formatting, linking, or testing a
  requirement never silently promotes it from `draft` to `proposed` or
  `approved`.

## Route the intent

| Intent | Action |
|---|---|
| Understand what belongs in requirements | Apply the core model and distinguish stakeholder outcomes from software behavior. |
| Set up a requirements base | Run `okfreq init <project>` and review the generated configuration, schemas, and local guideline before authoring. |
| Capture stakeholder intent | Create an StRS with a stakeholder-observable `SHALL` statement and a preserved `--user-need`. |
| Refine intent into software behavior | Create an SwRS with one bounded `SHALL` response and at least one valid StRS `--derives-from` parent. |
| Implement a software requirement | Change code and focused tests together, add source/test markers near the evidence, run tests, then refresh coverage explicitly. |
| Inspect gaps or change impact | Use `trace`, `graph`, `status`, validation, and reports without mutating authored content. |
| Audit or reconcile a brownfield bundle | Use `okfreq-gardening`, which extends this skill with an explicit maintenance workflow. |
| Troubleshoot generic OKF structure or schemas | Use `okf-schema`. |

If a named specialized skill is unavailable, apply this skill's model and the
local requirements guideline directly.

## Set up safely

`okfreq init <project>` creates a split bundle without overwriting existing
files:

```text
<bundle>/
├── config.yml
├── guidelines/
│   └── requirements.guidelines.md
└── tiers/
    ├── _schema/
    ├── index.md
    ├── log.md
    ├── strs/
    └── swrs/
```

The `guidelines/` and `tiers/` directories are siblings under the requirements
bundle. Confirm that the project-local guideline was installed, then review and
adapt it for the repository. If initialization preserves an existing guideline,
keep using that local file; do not replace it with this skill's fallback.

## Author and implement requirements

1. Create or confirm the stakeholder outcome first. An StRS needs one
   stakeholder-observable normative behavior, the stakeholder's user need, and
   any known rationale or constraints. Do not add software scenarios or source
   markers. Add a direct test marker only when the configured StRS coverage mode
   requires an explicit validation test.
2. Derive one or more SwRS requirements for independently observable software
   behaviors. Each SwRS needs a valid StRS parent, nominal and boundary/failure
   scenarios, and objective verification notes.
3. Replace every scaffold placeholder before review. A remaining angle-bracket
   placeholder is an explicit authoring gap, not text to delete merely to make
   prose checks quiet.
4. Implement the SwRS and focused tests. Put markers close to the behavior they
   identify, using the configured marker names and comment syntax appropriate
   for each file.
5. Preview generated changes with `okfreq update-coverage <bundle> --check` or
   `--diff`, then apply them intentionally. Never hand-edit generated coverage,
   reverse links, indexes, or reports.
6. Run the local guideline's validation commands and the project's test suite.
   At minimum, validate and lint with prose checks and inspect trace output.

## Universal guardrails

1. Preserve requirement IDs, UUIDs, authored fields, unknown metadata, YAML
   comments, Markdown bodies, and authored relationships.
2. Never invent stakeholder intent, evidence, verification results, approval,
   exemptions, or lifecycle transitions.
3. Never renumber an existing requirement. Allocate new identities through
   `okfreq new` under the configured ID policy.
4. Never treat generated `derived_by`, `implemented_in_files`, or
   `tested_in_files` as authored truth.
5. Keep `okfreq` requirements independent from `okfkb` knowledge documents.
   They may coexist and both use OKF-compatible Markdown, but they have distinct
   purposes and lifecycles.
6. Preserve unrelated work and report unresolved intent or hierarchy questions
   instead of guessing.

## Completion

Summarize requirements and evidence changed, generated fields refreshed,
lifecycle changes explicitly approved, validation and test results, and any
remaining gaps. Do not claim complete traceability when a non-exempt leaf lacks
source or test evidence, markers reference unknown IDs, or validation/tests
failed or did not run.
