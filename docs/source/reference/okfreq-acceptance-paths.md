# Acceptance paths and scenario markers

The `linked-swrs-and-acceptance-paths` mode uses declared `scenarios:` on StRS
for main paths and on SwRS for transition scenarios. See
{ref}`okfreq-declared-scenarios` for authoring.

| Marker | Meaning | Recommended placement |
|---|---|---|
| `@implements_req SwRS-ID` | Implementation | Source code |
| `@tests_req ID#S1` | Test of a declared SwRS transition or StRS path | A cheap test on every pull or merge request |
| `@accepts_req StRS-ID#S1` | Acceptance test of a declared StRS path | The test closest to the final product, possibly in the main-branch pipeline |

Placement by cost is guidance, not a check. When tests are cheap, mark them
directly with `@accepts_req`. Set the three distinct keywords with
`markers.implements`, `markers.tests` and `markers.accepts`. The custom
`id_pattern` must not admit `#`.

## Mode comparison

| Mode | SwRS | StRS |
|---|---|---|
| `linked-swrs` | At least one test marker | At least one linked SwRS, all linked SwRS covered |
| `linked-swrs-and-validation-test` | At least one test marker | The linked-SwRS rule and a direct `@tests_req` |
| `linked-swrs-and-acceptance-paths` | Every declared transition has a test; without declarations, one test | The linked-SwRS rule and acceptance of every declared path, or one acceptance marker if none is declared, unless a justified acceptance waiver applies |

In the first two modes a suffix is ignored and acceptance markers do not count.
The following table applies in the new mode:

| Marker and target | Declared scenarios | No scenarios |
|---|---|---|
| `@implements_req SwRS` | Implementation; suffix ignored | Implementation; suffix ignored |
| `@implements_req StRS` | Non-leaf marker | Non-leaf marker |
| `@tests_req SwRS#S1` | Tests S1 if declared; otherwise error | Unknown-fragment error |
| `@tests_req StRS#S1` | Tests S1 if declared; otherwise error | Unknown-fragment error |
| `@accepts_req StRS#S1` | Accepts S1 if declared; otherwise error | Unknown-fragment error |
| Fragmentless `@tests_req` on SwRS or StRS | Error; does not count | Tests the requirement |
| Fragmentless `@accepts_req` on StRS | Error; does not count | Accepts the requirement |
| `@accepts_req` on SwRS | Schema error | Schema error |

Only a glued `#S` followed by digits and ending at a non-identifier character
is a fragment. `#S0` and `#S01` cannot name a declared ID and are errors;
`#path1`, `#s1`, `#S1a` and `#` are treated as fragmentless. Additional
project-defined tiers retain their previous marker handling.

The table treats an unrelated suffix as fragmentless. In the two old modes,
any suffix on `@tests_req` is ignored, `@tests_req` retains its existing
whole-requirement meaning, `@implements_req` keeps its existing leaf/non-leaf
handling, and `@accepts_req` counts nowhere and raises no new marker finding.
In the new mode, an undeclared `#S<n>` is an error whether or not any scenarios
were declared; a declared fragment is meaningful only on the matching tier and
verb shown above. Implementation markers ignore fragments in every mode.

## Worked examples

These fragments apply to an initialized bundle with a stakeholder requirement
`StRS-default-001`, its linked `SwRS-default-001`, and the new mode. Each YAML
block gives the authored `scenarios` values by tier; an omitted key means the
field is absent. Markers are in a configured test file. The result is a JSON
excerpt, not an execution result.

### Independent testing and acceptance

```{code-block} yaml
:caption: Example 1 frontmatter

strs:
  - {id: S1, title: Prepare}
  - {id: S2, title: Review}
  - {id: S3, title: Export}
swrs:
  - {id: S1, title: Write}
```

```{code-block} python
:caption: Example 1 markers

# @tests_req SwRS-default-001#S1
# @tests_req StRS-default-001#S1
# @tests_req StRS-default-001#S2
# @accepts_req StRS-default-001#S3
```

```{code-block} json
:caption: Example 1 result

{"status": "missing", "paths": {"total": 3, "tested": 2, "accepted": 1}, "tested": false, "accepted": false}
```

```{code-block} text
:caption: Example 1 row

| default | StRS | StRS-default-001 | Export | ❌ missing | 2/3 | 1/3 |
```

S3 is accepted but not tested; S1 and S2 are tested but not accepted.

### A missing software transition

```{code-block} yaml
:caption: Example 2 frontmatter

strs:
  - {id: S1, title: Export}
swrs:
  - {id: S1, title: Write}
  - {id: S2, title: Reject}
```

```{code-block} python
:caption: Example 2 markers

# @tests_req SwRS-default-001#S1
# @accepts_req StRS-default-001#S1
```

```{code-block} json
:caption: Example 2 result

{"status": "missing", "paths": {"total": 1, "tested": 0, "accepted": 1}, "tested": false, "accepted": true}
```

```{code-block} text
:caption: Example 2 row

| default | SwRS | SwRS-default-001 | Write | ❌ missing | ❌ missing | S2 |
```

The SwRS has tested `S1` and missing `S2`; its StRS is missing even though
its acceptance path is marked.

### No declared stakeholder paths

```{code-block} yaml
:caption: Example 3 frontmatter

swrs:
  - {id: S1, title: Write}
body: |
  ### Main paths

  #### Path 1: Export
```

```{code-block} python
:caption: Example 3 markers

# @tests_req SwRS-default-001#S1
# @tests_req StRS-default-001
```

```{code-block} json
:caption: Example 3 result

{"status": "missing", "paths": {"total": 0, "tested": 0, "accepted": 0}, "tested": true, "accepted": false}
```

```{code-block} text
:caption: Example 3 row

| default | StRS | StRS-default-001 | Export | ❌ missing | ✅ no paths | ❌ no paths |
```

`W003` quotes `#### Path 1: Export` and suggests `scenarios: [{id: S1, title:
Export}]`; `W004` reports the missing acceptance marker. The fragmentless
test still counts for the requirement.

## Findings

Fix a missing fragment by naming the specific declared scenario; fix an
unknown fragment by using a declared ID. `@accepts_req` is only for StRS;
use `@tests_req` on SwRS. A live StRS without scenarios produces `W003` with
headings and a suggested frontmatter block. A live StRS without any counting
acceptance marker produces `W004`; one marker suppresses it even if other
paths remain unaccepted.

(okfreq-acceptance-waivers)=
## Acceptance waivers

In the new mode, record an owner-approved waiver for the **whole StRS**, not
for an individual path, in the requirement's authored frontmatter:

```yaml
acceptance_exemption: true
acceptance_exemption_reason: >-
  This interactive agent workflow requires human review and cannot be
  exercised by the project's deterministic acceptance tests.
```

`acceptance_exemption` is an optional boolean; when true,
`acceptance_exemption_reason` must be a non-empty, non-whitespace string.
Validation reports a missing or blank reason as an error. Both fields are
authored, not generated: `update-coverage` does not write or remove them.
Remove the waiver when the reason no longer applies. An owner should review
the decision under the project's approval rules; okfreq does not collect or
verify that approval.

A justified waiver suppresses `W004` and removes the acceptance condition
from the StRS coverage status. It does **not** suppress `W003`, mark any path
accepted or increase the accepted path count. JSON
`stakeholder_test_coverage.acceptance_exemption.reason` records the reason;
`accepted` and `paths.accepted` continue to describe actual counting markers.
Markdown labels the acceptance column `exempt`. Existing acceptance markers
still count normally. The StRS can be covered only if it has linked SwRS and
each is test-covered or has its own justified annotation exemption.

This waiver is distinct from a SwRS's `annotation_exemption: true` and
`exemption_reason`, which exempts that SwRS from its source and test marker
coverage. In the new mode, a justified exempt SwRS is identified as `exempt`
in the StRS report's `linked_swrs` rather than falsely labelled covered, and
does not block its parent's linked-SwRS condition. A stakeholder waiver does
not automatically exempt its linked SwRS, nor does a software waiver waive
stakeholder acceptance. See the [frontmatter reference](okfreq-frontmatter.md)
for the SwRS fields and {ref}`okfreq-waiver-rationale`.

Old bundle schemas are preserved by `okfreq init`. Before enabling the new
mode, add the following under the SwRS tier schema's `properties`:

```yaml
accepted_in_files:
  type: array
  maxItems: 0
  description: Never present. @accepts_req names a StRS main path; mark a SwRS test
    with @tests_req <SwRS-ID>#S<n>.
```

## Reports

Report format version 2 adds per-StRS `paths: {total, tested, accepted}`, the
two completion booleans, `tests` and `acceptance_tests` inside
`stakeholder_test_coverage`, and tested/missing `transitions` on SwRS with
declarations. The aggregate contains summed path totals. Markdown adds tested
and accepted columns and missing transitions.

In the new mode, the StRS `stakeholder_test_coverage.tests` contains counting
`@tests_req` files; the StRS record's own `tests` follows `validation_tests`,
which matches `acceptance_tests` and contains counting `@accepts_req` files.
By contrast, `trace --json` retains raw direct `@tests_req` files in its
`validation_tests`. `marker_coverage.tested` counts leaf IDs with at least one
counting test link, while `totals.tested` counts fully test-covered leaves.
Neither establishes that a test ran.
