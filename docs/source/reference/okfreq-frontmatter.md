# `okfreq` frontmatter reference

Every native or imported requirement is an OKF-compatible Markdown file. YAML
frontmatter identifies the requirement and records authored relationships. The
Markdown body remains useful for rationale, examples, constraints, and review
notes. Unknown properties are allowed and must be preserved.

## Common fields

| Field | Required | Ownership | Meaning |
|---|---:|---|---|
| `type` | yes | authored | Configured hierarchy level, such as `StRS` or `SwRS`. |
| `id` | yes | authored | Stable human-readable identifier. Never renumber an existing ID. |
| `uuid` | yes | authored | Globally unique identity. Native requirements receive a generated UUID; imported requirements must provide one. |
| `title` | yes | authored | Short human-readable name. |
| `description` | yes | authored | The requirement statement. It should describe observable, bounded behavior or intent. |
| `project` | yes | authored | Project or product owning the requirement. |
| `scope` | yes | authored | Scope used for ownership, allocation, and scan mapping. |
| `tier` | yes | authored | Level label used by the requirements hierarchy. |
| `lifecycle` | yes | authored | One of `draft`, `proposed`, `approved`, `deprecated`, or `superseded`. |
| `origin` | yes | authored | Source of the requirement, such as `native`, `imported`, or a tool name. |
| `derives_from` | conditional | authored | IDs of higher-level requirements. Native `SwRS` requirements need at least one `StRS` ID. |
| `depends_on` | no | authored | Semantic prerequisite or dependency IDs. This is not generated coverage. |
| `verification_method` | no | authored | Controlled method used to verify the requirement, for example `test`, `analysis`, `inspection`, or `demonstration`. |
| `verification_criteria` | no | authored | Optional pass criteria that make verification concrete. |
| `user_need` | StRS | authored | Stakeholder outcome preserved separately from the normative StRS behavior. `okfreq new strs` leaves an explicit placeholder when `--user-need` is omitted. |
| `annotation_exemption` | SwRS | authored | Whether implementation and test marker coverage is intentionally exempted. New SwRS documents default to `false`. |
| `exemption_reason` | SwRS | authored | Conditional justification required when `annotation_exemption` is `true`. Explain why repository source/test coverage is not applicable and point to external justification or verification documents when available. |
| `external_id` | no | authored | Identifier of the corresponding requirement in an external system. |
| `external_url` | no | authored | URI of the corresponding requirement in an external system. |

## Tier-specific Markdown bodies

`okfreq new` deliberately emits different authoring scaffolds for the two
default levels. Angle-bracket text is an unfinished gap and should remain
visible until it is replaced with evidence-based content.

An StRS preserves stakeholder intent without prescribing software design:

```markdown
## EARS Expression

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
## EARS Expression

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

## Generated and externally maintained fields

| Field | Ownership | Meaning |
|---|---|---|
| `derived_by` | generated | Reverse links computed from other requirements’ `derives_from` fields. Do not author this as the source of truth. |
| `implemented_in_files` | generated or external tool | SwRS-only source files containing implementation markers. It is optional and must never be invented. |
| `tested_in_files` | generated or external tool | SwRS-only test files containing test markers. It is optional and must never be invented. |

The schema is selected from the `type` value. Common fields are defined in
`tiers/_schema/base.schema.yaml`; `type: StRS` is validated by
`tiers/_schema/strs.schema.yaml`, and `type: SwRS` by
`tiers/_schema/swrs.schema.yaml`. StRS intentionally has no implementation or
test coverage fields, because source and test markers apply only to leaf SwRS
requirements.

`okfreq update-coverage` may update only the coverage fields it owns. It writes
atomically and supports preview modes. Reports, indexes, and scope indexes are
also generated artifacts and should be regenerated rather than manually edited.

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
references, unknown IDs, repeated same-file markers, non-leaf references, and
scan warnings. Projects may configure other levels; implementation markers on
non-leaf levels do not count as leaf coverage.

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

For a new hierarchy level, add a level entry to `config.yml` with its folder,
ID prefix, and allowed parent levels. Keep the same directional convention:
`derives_from` is authored and `derived_by` is computed. For new lifecycle
values or transition policies, update the configuration and validation policy
explicitly; do not silently reinterpret existing lifecycle states.

See the [requirements traceability tutorial](../tutorials/okfreq-traceability.md)
for examples and the [build requirement base guide](../how-to/okfreq-build-requirement-base.md)
for the setup workflow.
