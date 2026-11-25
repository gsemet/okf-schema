# `okfreq` frontmatter reference

Every native or imported requirement is an OKF-compatible Markdown file. YAML
frontmatter identifies the requirement and records authored relationships. The
Markdown body remains useful for rationale, examples, constraints, and review
notes. Unknown properties are allowed and must be preserved.

## Common fields

| Field | Required | Ownership | Meaning |
|---|---:|---|---|
| `type` | yes | authored | Configured tier, such as `StRS` or `SwRS`. |
| `id` | yes | authored | Stable human-readable identifier. Never renumber an existing ID. |
| `uuid` | yes | authored | Globally unique identity. Native requirements receive a generated UUID; imported requirements must provide one. |
| `title` | yes | authored | Short human-readable name. |
| `description` | yes | authored | The requirement statement. It should describe observable, bounded behavior or intent. |
| `project` | yes | authored | Project or product owning the requirement. |
| `scope` | yes | authored | Scope used for ownership, allocation, and scan mapping. |
| `tier` | yes | authored | Tier label used by the requirements hierarchy. |
| `req_lifecycle` | yes | authored | One of `draft`, `proposed`, `approved`, `deprecated`, or `superseded`; see {ref}`okfreq-lifecycle-states`. The field name is `lifecycle.field` in `config.yml` (`req_lifecycle` by default, distinct from the OKF `status`), and the values are its `enum` in the base schema. |
| `origin` | yes | authored | Source of the requirement, such as `native`, `imported`, or a tool name. |
| `derives_from` | conditional | authored | IDs of higher-level requirements, with case-sensitive Markdown filename-stem navigation hints. Native `SwRS` requirements need at least one `StRS` ID. |
| `depends_on` | no | authored | Semantic prerequisite or dependency IDs. This is not generated coverage. |
| `superseded_by` | when `req_lifecycle: superseded` | authored | List of one or more requirement IDs that replace this requirement. Required and non-empty exactly when the lifecycle is `superseded`; written by `okfreq supersede`. A single ID written by earlier releases (`superseded_by: SwRS-new-001`) is still read as a one-item list. |
| `relates_to` | no | authored | List of requirement IDs related to this one laterally, at any level or scope, for example a sibling feature or a requirement from another release. It has no derivation, supersession or coverage meaning and no generated inverse. |
| `verification_method` | no | authored | Controlled method used to verify the requirement, for example `test`, `analysis`, `inspection`, or `demonstration`. |
| `verification_criteria` | no | authored | Optional pass criteria that make verification concrete. |
| `user_need` | StRS | authored | Stakeholder outcome preserved separately from the normative StRS behavior. `okfreq new strs` leaves an explicit placeholder when `--user-need` is omitted. |
| `scenarios` | no | authored | Ordered list of `{id: S<n>, title: ...}` entries declaring main paths (StRS) or transitions (SwRS); see {ref}`okfreq-declared-scenarios`. |
| `acceptance_exemption` | StRS | authored | Whole-StRS acceptance waiver boolean (`false` by default). Distinct from a SwRS `annotation_exemption`: satisfies StRS acceptance coverage and suppresses `W004` without fabricating accepted paths or waiving linked SwRS. |
| `acceptance_exemption_reason` | StRS | authored | Non-blank justification required when `acceptance_exemption` is `true`. Explain why automated acceptance testing is not feasible; remove both fields once acceptance tests exist. |
| `annotation_exemption` | SwRS | authored | Whether implementation and test marker coverage is intentionally exempted. New SwRS documents default to `false`. |
| `exemption_reason` | SwRS | authored | Conditional justification required when `annotation_exemption` is `true`. Explain why repository source/test coverage is not applicable and point to external justification or verification documents when available. |
| `external_id` | no | authored | Identifier of the corresponding requirement in an external system. It is not a local file reference. |
| `external_url` | no | authored | URI of the corresponding requirement in an external system. |
| `owner_email` | no | authored | Owner of this requirement when it differs from the configured one. Replaces `default_owner_email`. |
| `approved_by` | when `req_lifecycle: approved` | authored | Email of the owner who agreed to the current content. Recorded only on the owner's explicit agreement. |
| `approved_at` | when `req_lifecycle: approved` | authored | ISO 8601 datetime with an explicit UTC offset (`2026-10-28T09:00:00+01:00`) of that agreement, updated with every agreed change. A bare date is rejected. |

(okfreq-lifecycle-states)=

## Lifecycle states

The lifecycle says how freely a requirement may change. Only people change it,
through the commands below or an explicit edit; okfreq never infers it.

| State | Meaning | Change rule |
|---|---|---|
| `draft` | A requirement proposal, not implemented yet. | Free. `okfreq retire` can delete it for good. A project whose requirements are delivered with the code they describe should not keep drafts on its default branch: create them with `okfreq new --lifecycle proposed` in the change that implements them. |
| `proposed` | Implemented and in force, but not frozen. | Changes through the project's usual plan and review, with no explicit owner agreement. |
| `approved` | Frozen by its owner. | Any significant change (normative statement, scenarios, verification criteria, deprecation or supersession) needs the owner's explicit, justified agreement, recorded in `approved_by` and `approved_at`. Editorial fixes that keep the meaning are free. **Exception:** adding `scenarios:` to frontmatter from existing body headings without editing the body or any other authored field does not change meaning and needs no re-approval, provided it is logged in `tiers/log.md`. Allowed only where `approval_lock` is true for the tier and scope. |
| `deprecated` | No longer in force, without replacement (`okfreq archive`). | Kept for history; its ID is never reused. |
| `superseded` | Replaced by the requirements in `superseded_by` (`okfreq supersede`). | Kept for history. |

Which requirements can be frozen, and by whom, is set per tier and per scope in
`config.yml` ({ref}`okfreq-ownership-and-approval`):
by default StRS can be approved and SwRS cannot. `okfreq validate` fails on an
`approved` requirement whose tier and scope are not lockable, or that lacks
`approved_by` or `approved_at`.

A coding agent never approves a requirement, and never changes an approved one, on
its own decision (with the single exception of a frontmatter-only edit that adds
`scenarios:` from existing body headings and is recorded in `tiers/log.md`; any
edit to an approved body still follows the normal owner-review rule). The owner's agreement is usually given during planning, where
the agent cannot see it. So when its task changes an approved requirement, the
agent proceeds as if the owner agreed: it records the owner's email in
`approved_by` and the current date and time with its offset in `approved_at`, names
the requirement in the pull or merge request, and requests the owner's review of the
file. A review rule such as `CODEOWNERS` then blocks the merge until the owner
approves. `okfreq update-coverage` then writes the generated `status` and
`verified` fields that plain OKF consumers read:

```yaml
req_lifecycle: approved
status: stable                                   # generated from req_lifecycle
default_owner_email: product-owner@example.org   # generated from config.yml
approved_by: product-owner@example.org
approved_at: 2026-10-28T09:00:00+01:00
verified:                                        # generated from the approval
  by: human:product-owner@example.org
  at: 2026-10-28T09:00:00+01:00
```

(okfreq-okf-projection)=

## Native OKF projection

The `tiers/` folder is a plain OKF v0.2 bundle. okfreq keeps its own vocabulary
and generates, as the schemas declare, the fields a consumer that knows only OKF
reads:

| okfreq field | OKF field | Declared by |
|---|---|---|
| `req_lifecycle` | `status` (section 5.4) | `x-okf-status-projection` on the lifecycle property |
| `approved_by`, `approved_at` | `verified` (section 5.2), by a `human:` actor | built in, when `verified` is in `generated_fields` |
| `derives_from`, `derived_by`, `depends_on`, `superseded_by`, `supersedes`, `relates_to` | Markdown links in the body (section 6.1) | `link-projection` in each field's `x-okf-link` |

| `req_lifecycle` | `status` | Read as |
|---|---|---|
| `draft` | `draft` | work in progress |
| `proposed`, `approved` | `stable` | current |
| `deprecated`, `superseded` | `deprecated` | retired |

The relations become one generated section at the end of the body, one group per
annotated field in schema order, one relative link per value with the target
title. A value that does not resolve stays as code, so no broken link is written:

```markdown
<!-- okf:links:start -->
### Links

<!-- Generated from the frontmatter relations; edit them instead. -->

- Derives from:
  - [StRS-demo-001](../../strs/core/StRS-demo-001.md): Export portable reports
<!-- okf:links:end -->
```

Removing a `link-projection` label removes its group from every section on the
next `okfreq lint` or `update-coverage`; renaming it renames the group. Links that
leave the bundle (`project-relative`, such as `implemented_in_files`) cannot be
projected: `okfreq validate` rejects such a label, a status mapping to a value
outside `draft | stable | deprecated` or missing a lifecycle value, and a `status`
that disagrees with the lifecycle. `okfreq lint --check` and
`okfreq update-coverage --check` fail on a stale section, `status` or `verified`.

(okfreq-declared-scenarios)=

## Declared scenarios

The optional authored `scenarios` frontmatter field declares the addressable
scenarios of a requirement as a non-empty list of `{id, title}` objects:

```yaml
scenarios:
  - id: S1
    title: Export CSV report
  - id: S2
    title: Reject unsupported format
```

- **IDs:** each `id` must match `^S[1-9][0-9]*$` (`S1`, `S2`, …) and be unique
  within the requirement. Never reuse a retired `S<n>` ID when reordering or
  removing scenarios: keeping IDs stable prevents existing test markers from
  silently pointing at a different scenario.
- **StRS vs. SwRS meaning:** on an `StRS`, `scenarios:` lists the stakeholder's
  **main paths** (typically matching `#### Path S<n>: <title>` headings under
  `### Main paths`). On an `SwRS`, `scenarios:` lists the software requirement's
  **transitions** (typically matching `### Scenario S<n>: <title>` headings).
- **Authoring guidance:** keep `scenarios:` IDs and titles aligned with the
  corresponding body headings so humans and agents can cross-reference them
  immediately. When migrating an existing `approved` requirement, you may add
  `scenarios:` to its frontmatter from existing body headings without editing
  the body or re-approving, provided you log the change in `tiers/log.md`.
- **Marker enforcement:** in `linked-swrs-and-acceptance-paths` mode, once a
  requirement declares `scenarios:`, every `@tests_req` or `@accepts_req`
  marker targeting it must carry a declared `#S<n>` fragment. See
  [Acceptance paths and scenario markers](okfreq-acceptance-paths.md).

## Tier-specific Markdown bodies

`okfreq new` deliberately emits different authoring scaffolds for the two
default tiers. Angle-bracket text is an unfinished gap and should remain
visible until it is replaced with evidence-based content. The first Markdown
heading repeats the frontmatter `title`; update both together when renaming
a requirement. EARS describes the statement format, not the document title.

An StRS preserves stakeholder intent without prescribing software design (in
`linked-swrs-and-acceptance-paths` mode, `okfreq new strs` also adds
`### Main paths` and pre-fills `scenarios:`):

```markdown
---
# ...
scenarios:
  - id: S1
    title: <main path title>
---

## Export portable reports

### Normative behavior

<stakeholder-observable SHALL statement>

### Main paths

#### Path S1: <main path title>

1. <first step the stakeholder observes>
2. <next step, up to the observable outcome>

### Preserved stakeholder intent

## User Need

<stakeholder need in the stakeholder's language>

### Rationale and constraints

- <known constraint, exclusion, or rationale>
```

An SwRS describes software behavior that implementation and tests can observe
(in `linked-swrs-and-acceptance-paths` mode, `okfreq new swrs` names the
headings `Scenario S1:` / `Scenario S2:` and pre-fills `scenarios:`):

```markdown
---
# ...
scenarios:
  - id: S1
    title: <nominal behavior>
  - id: S2
    title: <boundary or failure behavior>
---

## Write CSV output

### Normative behavior

<observable, bounded software SHALL response>

### Scenario S1: <nominal behavior>

- GIVEN <precondition and relevant inputs>
- WHEN <trigger or action>
- THEN <single observable, verifiable outcome>

### Scenario S2: <boundary or failure behavior>

- GIVEN <boundary precondition or failure>
- WHEN <trigger or action>
- THEN <observable recovery, rejection, or boundary outcome>

### Verification notes

- Method: <test, inspection, analysis, or demonstration>
- Criteria: <objective pass condition>
```

StRS documents do not receive SwRS scenarios or verification notes. SwRS
documents do not receive `User Need` or stakeholder rationale/constraints.

### Annotation exemptions

`annotation_exemption` is a boolean policy decision for a `SwRS` requirement;
it is not evidence that the requirement has been implemented or tested. Keep it
`false` unless repository-level source and test markers genuinely cannot apply.
When it is `true`, `exemption_reason` must be a non-empty, authored
justification. State what makes normal coverage impossible or inappropriate,
what evidence is used instead, and include a path or URL to an external
justification, verification report, safety case, certification record, or other
reviewable document when one exists.

```yaml
annotation_exemption: true
exemption_reason: >-
  Hardware-in-the-loop evidence is maintained outside this repository. See
  https://requirements.example.test/verification/REQ-4821 and report HIL-2026-04.
```

The schema requires `exemption_reason` whenever `annotation_exemption` is
`true`, and `okfreq validate`/`okfreq lint` reject an exemption without that
justification. The reason does not make test execution available to the report;
it records why repository marker coverage is intentionally excluded. See the
**Generated and externally maintained fields** section above for the distinction
between authored exemption metadata and generated coverage.

## Supersession and related requirements

A superseded requirement keeps its document, ID and UUID and names its
replacements. `okfreq supersede` writes both fields in one step:

```bash
okfreq supersede SwRS-export-001 SwRS-export-010 SwRS-export-011 --path requirements --yes
okfreq update-coverage requirements
```

```yaml
# SwRS-export-001.md (authored)
req_lifecycle: superseded
superseded_by:
  - SwRS-export-010
  - SwRS-export-011
# SwRS-export-010.md and SwRS-export-011.md (generated)
supersedes:
  - SwRS-export-001
```

`okfreq validate` and `okfreq lint` fail, naming the file, when:

- `req_lifecycle` is `superseded` and `superseded_by` is absent or empty;
- `superseded_by` is set while the lifecycle is anything else (clear it, or
  restore `superseded`);
- a `superseded_by` or `relates_to` target is unknown, is the requirement itself
  or is listed twice, or the field is not a list of IDs;
- `superseded_by` forms a cycle (`A -> B -> A`). Chains (`A` replaced by `B`,
  `B` replaced by `C`) are allowed.

`relates_to` is deliberately one-directional and undirected in meaning: declare
it on one side, and read it from both. No inverse field is generated, because a
stored inverse doubles every edit and can go stale; `okfreq graph --json` shows the
authored side only. Use `depends_on` for a prerequisite and `derives_from` for
hierarchy; `relates_to` states only that two requirements concern each other.

### Existing bundles

The scalar form `superseded_by: SwRS-new-001` stays valid input. Validation
passes and adds the informational finding `I2` suggesting the list form; nothing
is rewritten for you. Convert by editing the field to `[SwRS-new-001]` or by
running `okfreq supersede OLD NEW --yes` again. A requirement already marked
`superseded` without `superseded_by` now fails validation: add the replacement.
To maintain `supersedes`, add it to `generated_fields` in `config.yml`; bundles
that list the fields explicitly keep their current set until you do.

## Generated and externally maintained fields

| Field | Ownership | Meaning |
|---|---|---|
| `derived_by` | generated | Reverse links computed from other requirements’ `derives_from` fields. Do not author this as the source of truth. |
| `supersedes` | generated | Reverse links computed from other requirements’ `superseded_by` fields: the requirements this one replaces. Written by `okfreq update-coverage` when `supersedes` is in `generated_fields`, only where it has a value (or the field is already present). Do not author it. |
| `implemented_in_files` | generated or external tool | SwRS-only project-relative source paths containing implementation markers. It is optional and must never be invented. |
| `tested_in_files` | generated or external tool | Project-relative test paths containing counting `@tests_req` markers (SwRS in every mode; also StRS in `linked-swrs-and-acceptance-paths` mode). It is optional and must never be invented. |
| `accepted_in_files` | generated or external tool | StRS-only project-relative acceptance-test paths containing counting `@accepts_req` markers in `linked-swrs-and-acceptance-paths` mode (refused on SwRS by `swrs.schema.yaml`). Removed from StRS in older modes. |
| `default_owner_email` | generated | Owner resolved from `config.yml` for the requirement's tier and scope. Written by `okfreq update-coverage` when `default_owner_email` is in `generated_fields`, removed when no owner applies. An authored `owner_email` replaces it. |
| `status` | generated | OKF lifecycle mapped from `req_lifecycle` by `x-okf-status-projection`; see {ref}`okfreq-okf-projection`. Written by `okfreq new`, `archive`, `supersede`, `update-coverage` and `lint` when `status` is in `generated_fields`. |
| `verified` | generated | OKF trust event `{by: human:<approved_by>, at: <approved_at>}`, removed when the approval is incomplete. Written when `verified` is in `generated_fields`. |
| Links section | generated | Body section between `<!-- okf:links:start -->` and `<!-- okf:links:end -->`, one group per `link-projection` field. |

The schema is selected from the `type` value. Common fields are defined in
`tiers/_schema/base.schema.yaml`; `type: StRS` is validated by
`tiers/_schema/strs.schema.yaml`, and `type: SwRS` by
`tiers/_schema/swrs.schema.yaml`. StRS never carries `implemented_in_files`;
in `linked-swrs-and-acceptance-paths` mode it carries generated
`tested_in_files` and `accepted_in_files`, whereas in older modes
`update-coverage` removes both from StRS.

`okfreq update-coverage` may update only the coverage fields it owns. It writes
atomically and supports preview modes. Reports, indexes, and scope indexes are
also generated artifacts and should be regenerated rather than manually edited.

### File-link annotations

These fields apply the generic `okf-schema` contract; `okfreq` does not own a
separate file-link type or resolution engine. New requirement scaffolds contain
the annotations below. Existing requirement schemas and documents are not
migrated or rewritten.

Requirement values are strings, so a consumer needs schema metadata to know
which values it can open as files. For example, this `SwRS` frontmatter records
the implementation file, its test, its parent requirement, and an external
tracker ID without changing any of their YAML types:

```yaml
---
type: SwRS
id: SwRS-demo-001
derives_from:
  - StRS-demo-001
implemented_in_files:
  - src/report/export.py
tested_in_files:
  - tests/test_export.py
external_id: DOORS-4821
---
```

The generated schema tells the consumer how to interpret each value:

```yaml
implemented_in_files:
  type: array
  items:
    type: string
    x-okf-link:
      resolution: project-relative
      syntax: plain
      basename_marker: '@implements_req'
      id_marker: id
      show_line_number: true
tested_in_files:
  type: array
  items:
    type: string
    x-okf-link:
      resolution: project-relative
      syntax: plain
      basename_marker: '@tests_req'
      id_marker: id
      show_line_number: true
derives_from:
  type: array
  items:
    type: string
    x-okf-link:
      resolution: filename-stem
      syntax: plain
      id_marker: id
      tooltip_shows_fields: [description]
      preview_shows_fields: [description]
```

`superseded_by`, `supersedes` and `relates_to` use the same array-of-strings
definition as `derives_from`, each with the `filename-stem` annotation shown
above. The scaffold written by `okfreq init` contains them. An existing project's
`tiers/_schema/base.schema.yaml` is never rewritten: copy the three property
blocks from a freshly initialized bundle when you want editor navigation for
them, after converting any scalar `superseded_by` to a list (the array schema
rejects a scalar).

With a project containing `src/report/export.py`, `tests/test_export.py`, and
a requirement file named `StRS-demo-001.md`, the first two values resolve to
exact project-relative files and `StRS-demo-001` navigates by Markdown
filename stem. `DOORS-4821` remains an external identifier. The file-link
annotations guide navigation; they do not replace the existing requirement-ID
validation or prove that a source file implements the requirement. For source
and test evidence, `basename_marker` names the marker prefix to search in the
resolved file, while `id_marker: id` tells a consumer to use the requirement's
`id` value. The consumer can therefore find `@implements_req <id>` or
`@tests_req <id>` and open directly at that line. A basename is a filename
without its extension; these hints are advisory `x-okf-link` metadata and are
not checked by `okfreq --check-links`. `tooltip_shows_fields` and
`preview_shows_fields` tell a consumer which linked frontmatter fields are useful
in a hover or preview, while `show_line_number` requests line-aware source/test
navigation. The CLI validates targets but does not render those UI elements.

Link checking is opt-in:

```bash
okfreq validate . --check-links --project-root .
okfreq lint . --check-links --project-root .
```

The `okf-schema` repository applies these annotations to its own `requirements/`
bundle. For example, `SwRS-OKFSCHEMA-CORE-007` derives from
`StRS-OKFSCHEMA-CORE-003`; its generated implementation evidence points to
`src/okf_schema/file_links.py`, and its test evidence points to
`tests/test_file_links.py`. From the repository root, check those targets with:

```bash
okfreq validate requirements --check-links --project-root . --prose
```

The StRS states why consumers need recognizable file references without changing
value types. The SwRS specifies the shared API, resolution modes, diagnostics,
and opt-in behavior; KB and requirements SwRS describe their applied conventions.
This is an explicitly maintained repository bundle, not an automatic migration
of other existing bundles.

If no project root is supplied, `okfreq` uses the containing Git root for
project-relative paths. It never infers an editor workspace or uses the current
working directory as a fallback. Missing exact targets and ambiguous filename
stems are `E10` errors. An unavailable root or inaccessible matching candidate is
reported as `W15` and skipped, because the CLI cannot infer which workspace the
author intended. `--check-links` does not check heading or block fragments in
wikilinks; it checks only the target file.

StRS documents do not have source coverage. The generated report gives StRS its
own stakeholder-test coverage record, computed from linked SwRS and the
configured `strs_test_coverage_mode`:

- `linked-swrs`: linked SwRS only.
- `linked-swrs-and-validation-test`: linked SwRS plus at least one direct
  `@tests_req StRS-ID` marker in a configured test file.
- `linked-swrs-and-acceptance-paths`: linked SwRS (each covered or individually
  exempt) plus counting `@accepts_req StRS-ID#S<n>` markers on every declared
  main path (or a justified whole-StRS acceptance waiver), with `@tests_req`
  tracked separately as the `tested` counter.

## Marker fields

The default marker keywords are:

```text
# In source code:
@implements_req REQUIREMENT-ID

# In tests code:
@tests_req REQUIREMENT-ID[#S<n>]
@accepts_req STRS-ID[#S<n>]
```

For example:

```python
# @implements_req SwRS-default-001
# @tests_req SwRS-default-001#S1
# @accepts_req StRS-default-001#S1
```

The keywords and accepted ID pattern are configured in `config.yml`. `trace`
reports implementation references, test references, acceptance references,
per-scenario marker hits (`scenario_markers`), direct StRS validation-test
references, unknown IDs, non-leaf references, and scan warnings. Projects may
configure other tiers; implementation markers on non-leaf tiers do not count as
leaf coverage. See [Acceptance paths and scenario markers](okfreq-acceptance-paths.md)
for the `#S<n>` fragment grammar and mode rules.

```{admonition} Markers are file-level references
:class: warning

`okfreq` parses markers at the file level. It does not provide language-specific
parsers, AST analysis, or special support for Python, Rust, TypeScript, C/C++,
or another programming language. A marker is therefore evidence that a file
references a requirement, not proof that a particular function, class, or test
case implements or verifies it. Use normal language tooling, code review, and
the test runner for those stronger checks.
```

```{admonition} Test results are not parsed
:class: warning

The current traceability report parses `@tests_req` markers, but it does not
read test-runner output or determine whether a referenced test passed, failed,
was skipped, or ran at all. Its SwRS test-link coverage and configured StRS
coverage are therefore linkage metrics only. In theory, true requirement
coverage requires successful validation tests, connected to the requirement and
executed in the relevant validation run. Until test-result ingestion is
implemented, treat the report's execution evidence as `not_collected`.

Read [What `okfreq` coverage really means](../explanation/okfreq-coverage-boundaries.md)
for the rationale, limitations, and evidence model behind this behavior.
```

## Extending the model

Project-specific properties such as `safety_goal`, `owner`, `review_board`,
`risk_class`, or a producer’s external reference can be added directly to the
frontmatter. The bundled schema uses `additionalProperties: true`, so these
properties remain interoperable and are preserved by round-trip editing.

For a new tier, add an entry under `tiers` in `config.yml` with its folder,
ID prefix, and allowed parent tiers. Keep the same directional convention:
`derives_from` is authored and `derived_by` is computed. For new lifecycle
values or transition policies, update the configuration and validation policy
explicitly; do not silently reinterpret existing lifecycle states.

See the [requirements traceability tutorial](../tutorials/okfreq-traceability.md)
for examples and the [build requirement base guide](../how-to/okfreq-build-requirement-base.md)
for the setup workflow.
