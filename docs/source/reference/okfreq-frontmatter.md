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
| `lifecycle` | yes | authored | One of `draft`, `proposed`, `approved`, `deprecated`, or `superseded`; see {ref}`okfreq-lifecycle-states`. The field name is `lifecycle.field` in `config.yml`, and the values are its `enum` in the base schema. |
| `origin` | yes | authored | Source of the requirement, such as `native`, `imported`, or a tool name. |
| `derives_from` | conditional | authored | IDs of higher-level requirements, with case-sensitive Markdown filename-stem navigation hints. Native `SwRS` requirements need at least one `StRS` ID. |
| `depends_on` | no | authored | Semantic prerequisite or dependency IDs. This is not generated coverage. |
| `superseded_by` | when `lifecycle: superseded` | authored | List of one or more requirement IDs that replace this requirement. Required and non-empty exactly when the lifecycle is `superseded`; written by `okfreq supersede`. A single ID written by earlier releases (`superseded_by: SwRS-new-001`) is still read as a one-item list. |
| `relates_to` | no | authored | List of requirement IDs related to this one laterally, at any level or scope, for example a sibling feature or a requirement from another release. It has no derivation, supersession or coverage meaning and no generated inverse. |
| `verification_method` | no | authored | Controlled method used to verify the requirement, for example `test`, `analysis`, `inspection`, or `demonstration`. |
| `verification_criteria` | no | authored | Optional pass criteria that make verification concrete. |
| `user_need` | StRS | authored | Stakeholder outcome preserved separately from the normative StRS behavior. `okfreq new strs` leaves an explicit placeholder when `--user-need` is omitted. |
| `annotation_exemption` | SwRS | authored | Whether implementation and test marker coverage is intentionally exempted. New SwRS documents default to `false`. |
| `exemption_reason` | SwRS | authored | Conditional justification required when `annotation_exemption` is `true`. Explain why repository source/test coverage is not applicable and point to external justification or verification documents when available. |
| `external_id` | no | authored | Identifier of the corresponding requirement in an external system. It is not a local file reference. |
| `external_url` | no | authored | URI of the corresponding requirement in an external system. |
| `owner_email` | no | authored | Owner of this requirement when it differs from the configured one. Replaces `default_owner_email`. |
| `approved_by` | when `lifecycle: approved` | authored | Email of the owner who agreed to the current content. Recorded only on the owner's explicit agreement. |
| `approved_on` | when `lifecycle: approved` | authored | ISO date (`YYYY-MM-DD`) of that agreement, updated with every agreed change. |

(okfreq-lifecycle-states)=

## Lifecycle states

The lifecycle says how freely a requirement may change. Only people change it,
through the commands below or an explicit edit; okfreq never infers it.

| State | Meaning | Change rule |
|---|---|---|
| `draft` | A requirement proposal, not implemented yet. | Free. `okfreq retire` can delete it for good. A project whose requirements are delivered with the code they describe should not keep drafts on its default branch: create them with `okfreq new --lifecycle proposed` in the change that implements them. |
| `proposed` | Implemented and in force, but not frozen. | Changes through the project's usual plan and review, with no explicit owner agreement. |
| `approved` | Frozen by its owner. | Any significant change (normative statement, scenarios, verification criteria, deprecation or supersession) needs the owner's explicit, justified agreement, recorded in `approved_by` and `approved_on`. Editorial fixes that keep the meaning are free. Allowed only where `approval_lock` is true for the tier and scope. |
| `deprecated` | No longer in force, without replacement (`okfreq archive`). | Kept for history; its ID is never reused. |
| `superseded` | Replaced by the requirements in `superseded_by` (`okfreq supersede`). | Kept for history. |

Which requirements can be frozen, and by whom, is set per tier and per scope in
`config.yml` ({ref}`okfreq-ownership-and-approval`):
by default StRS can be approved and SwRS cannot. `okfreq validate` fails on an
`approved` requirement whose tier and scope are not lockable, or that lacks
`approved_by` or `approved_on`.

A coding agent never approves a requirement, and never changes an approved one, on
its own decision. The owner's agreement is usually given during planning, where
the agent cannot see it. So when its task changes an approved requirement, the
agent proceeds as if the owner agreed: it records the owner's email in
`approved_by` and today's date in `approved_on`, names the requirement in the pull
or merge request, and requests the owner's review of the file. A review rule such
as `CODEOWNERS` then blocks the merge until the owner approves.

```yaml
lifecycle: approved
default_owner_email: product-owner@example.org   # generated from config.yml
approved_by: product-owner@example.org
approved_on: 2026-10-28
```

## Tier-specific Markdown bodies

`okfreq new` deliberately emits different authoring scaffolds for the two
default tiers. Angle-bracket text is an unfinished gap and should remain
visible until it is replaced with evidence-based content. The first Markdown
heading repeats the frontmatter `title`; update both together when renaming
a requirement. EARS describes the statement format, not the document title.

An StRS preserves stakeholder intent without prescribing software design:

```markdown
## Export portable reports

### Normative behavior

<stakeholder-observable SHALL statement>

### Preserved stakeholder intent

## User Need

<stakeholder need in the stakeholder's language>

### Rationale and constraints

- <known constraint, exclusion, or rationale>
```

An SwRS describes software behavior that implementation and tests can observe:

```markdown
## Write CSV output

### Normative behavior

<observable, bounded software SHALL response>

### Scenario: <nominal behavior>

- GIVEN <precondition and relevant inputs>
- WHEN <trigger or action>
- THEN <single observable, verifiable outcome>

### Scenario: <boundary or failure behavior>

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
lifecycle: superseded
superseded_by:
  - SwRS-export-010
  - SwRS-export-011
# SwRS-export-010.md and SwRS-export-011.md (generated)
supersedes:
  - SwRS-export-001
```

`okfreq validate` and `okfreq lint` fail, naming the file, when:

- `lifecycle` is `superseded` and `superseded_by` is absent or empty;
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
| `tested_in_files` | generated or external tool | SwRS-only project-relative test paths containing test markers. It is optional and must never be invented. |
| `default_owner_email` | generated | Owner resolved from `config.yml` for the requirement's tier and scope. Written by `okfreq update-coverage` when `default_owner_email` is in `generated_fields`, removed when no owner applies. An authored `owner_email` replaces it. |

The schema is selected from the `type` value. Common fields are defined in
`tiers/_schema/base.schema.yaml`; `type: StRS` is validated by
`tiers/_schema/strs.schema.yaml`, and `type: SwRS` by
`tiers/_schema/swrs.schema.yaml`. StRS intentionally has no implementation or
test coverage fields, because source and test markers apply only to leaf SwRS
requirements.

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
configured `strs_test_coverage_mode`. A direct `@tests_req StRS-ID` marker in a
test file counts as a defined validation test when the
`linked-swrs-and-validation-test` mode is selected.

## Marker fields

The default marker keywords are:

```text
# In source code:
@implements_req REQUIREMENT-ID

# In tests code:
@tests_req REQUIREMENT-ID
```

For example:

```python
# @implements_req SwRS-default-001
# @tests_req SwRS-default-001
```

The keywords and accepted ID pattern are configured in `config.yml`. `trace`
reports implementation references, test references, direct StRS validation-test
references, unknown IDs, non-leaf references, and
scan warnings. Projects may configure other tiers; implementation markers on
non-leaf tiers do not count as leaf coverage.

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
