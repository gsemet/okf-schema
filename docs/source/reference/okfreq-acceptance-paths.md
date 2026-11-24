# Acceptance paths and scenario markers

This page specifies the mode `strs_test_coverage_mode:
linked-swrs-and-acceptance-paths`: the `scenarios:` field, the `@accepts_req`
marker, the `#S<n>` fragment, the counters, the findings and the report fields.
To understand why it exists and how to choose between the two test verbs, read
[Why `okfreq` measures acceptance paths](../explanation/okfreq-acceptance-paths.md).

In this page, **the new mode** is `linked-swrs-and-acceptance-paths` and **the
old modes** are `linked-swrs` (the default) and
`linked-swrs-and-validation-test`. A **counting** marker is a marker that the
rules below accept: a marker that causes an error does not count.

Everything here is linkage. `okfreq` scans files for markers; it does not read
test results, and the report's `execution_evidence` stays `not_collected`.

## Markers and the fragment

Three marker keywords exist. They are configured under `markers` in `config.yml`
(see the [configuration reference](okfreq-configuration.md)); two kinds of
marker cannot share one keyword.

| Config key | Default keyword | Read in | Meaning |
|---|---|---|---|
| `markers.implements` | `@implements_req` | `source_dirs` | Implementation of a SwRS. |
| `markers.tests` | `@tests_req` | `test_dirs` | A test of a SwRS or a StRS, or of one of its scenarios. |
| `markers.accepts` | `@accepts_req` | `test_dirs` | The acceptance test of a StRS, or of one of its main paths. |

A test marker may carry a **fragment**: `#` glued to the requirement ID,
followed by `S` and digits, as in `@tests_req SwRS-CORE-001#S2` or
`@accepts_req StRS-CORE-001#S1`. Only `S<n>` is a fragment. Any other suffix
(`#path1`, `#s1`, `#S1a`, a lone `#`) is not a fragment: it is ignored and the
marker is read without fragment, as it was before this mode existed. `#S0` and
`#S01` are fragments that can name no declared id, so in the new mode they are
the unknown-fragment error. The fragment is not read on `@implements_req`.
Write one marker per line, with one ID and at most one fragment. A custom
`id_pattern` must not admit `#`.

### The two test verbs

| Verb | Put it on | Recommended for | Feeds |
|---|---|---|---|
| `@tests_req` | A SwRS transition (`SwRS-X#S<n>`) or a StRS main path (`StRS-X#S<n>`). | The cheaper tests, run on every pull or merge request. | the **tested** counter |
| `@accepts_req` | A StRS main path only (`StRS-X#S<n>`). | The tests closest to the final product, possibly costly and run in the main-branch pipeline; or any test when tests are cheap. | the **accepted** counter |

The "Recommended for" column is a recommendation, not a check: `okfreq` does not
look at where or how a test runs. See
{ref}`okfreq-execution-cost` for the reasoning.

## Mode comparison

| | `linked-swrs` | `linked-swrs-and-validation-test` | `linked-swrs-and-acceptance-paths` |
|---|---|---|---|
| SwRS is test-covered when | at least one `@tests_req SwRS-ID` (any suffix) | same | no `scenarios:`: at least one fragmentless `@tests_req`; with `scenarios:`: every declared `S<n>` has a `@tests_req SwRS-ID#S<n>` |
| StRS is covered when | it has a linked SwRS and all are covered | same, plus one `@tests_req StRS-ID` (any suffix) | same linked-SwRS rule (a SwRS with a justified `annotation_exemption` counts as `exempt`), plus **accepted** or a justified whole-StRS acceptance waiver |
| `@tests_req` on a StRS | no effect on coverage | the StRS validation test | the **tested** counter (per path, or fragmentless without `scenarios:`) |
| `@accepts_req` | counts toward nothing | counts toward nothing | the **accepted** counter (per path, or fragmentless without `scenarios:`); an error on a SwRS |
| `scenarios:` and `#S<n>` | accepted, nothing required | accepted, nothing required | declared paths and transitions, fragments mandatory when declared |
| Findings added | none | none | fragment errors, `W003`, `W004` |

The old modes accept `scenarios:` and `@accepts_req` and require and count
nothing new, so a project can adopt the vocabulary first. Only the schema of the
bundle refuses what it refuses.

## Combination table

Every row states the result for one marker. A marker on a tier that a project
added (see "Extending tiers and fields" in the
[configuration reference](okfreq-configuration.md)) keeps its earlier handling:
no fragment check and no new finding.

### Old modes

| Marker | On | Result |
|---|---|---|
| `@implements_req ID`, any suffix | SwRS | Implementation link; suffix ignored. |
| `@implements_req ID` | StRS | Non-leaf evidence; never source coverage. |
| `@tests_req ID`, with or without any suffix, even `#S9` | SwRS | Test link; the suffix is ignored. |
| `@tests_req ID`, with or without any suffix | StRS | `linked-swrs`: collected, no effect on coverage. `linked-swrs-and-validation-test`: the StRS validation test. |
| `@accepts_req ID`, any suffix | StRS or SwRS | Counts toward nothing, silently. |
| any marker, unknown ID | any | Listed in `missing_ids`, as every marker. |

### New mode

| Marker | On | Target declares `scenarios:` | Fragment | Result |
|---|---|---|---|---|
| `@tests_req` | StRS | yes | declared `#S<n>` | path `S<n>` **tested** |
| `@accepts_req` | StRS | yes | declared `#S<n>` | path `S<n>` **accepted** |
| `@tests_req` or `@accepts_req` | StRS | yes | undeclared `#S<n>` | **error**, does not count |
| `@tests_req` or `@accepts_req` | StRS | no | any `#S<n>` | **error**, does not count |
| `@tests_req` | StRS | yes | none, or another suffix | **error**, does not count |
| `@accepts_req` | StRS | yes | none, or another suffix | **error**, does not count |
| `@tests_req` | StRS | no | none, or another suffix | counts: the StRS is **tested** |
| `@accepts_req` | StRS | no | none, or another suffix | counts: the StRS is **accepted** |
| `@tests_req` | SwRS | yes | declared `#S<n>` | transition `S<n>` tested |
| `@tests_req` | SwRS | yes | undeclared `#S<n>` | **error**, does not count |
| `@tests_req` | SwRS | no | any `#S<n>` | **error**, does not count |
| `@tests_req` | SwRS | yes | none, or another suffix | **error**, does not count |
| `@tests_req` | SwRS | no | none, or another suffix | covers the whole SwRS, as before |
| `@accepts_req` | SwRS | any | any | **error**, from the SwRS schema |
| `@implements_req` | SwRS | any | not read | unchanged |
| `@implements_req` | StRS | any | not read | unchanged: non-leaf evidence |

A marker on an unknown ID goes to `missing_ids`, as every marker does.

## Declaring `scenarios:`

`scenarios:` is one authored frontmatter field, shared by both tiers: on a StRS
it lists the main paths, on a SwRS its transition scenarios. See
{ref}`okfreq-declared-scenarios` for the shape, the id rules and how to derive
the entries from existing headings.

```yaml
scenarios:
  - id: S1
    title: Export every row
  - id: S2
    title: Export a filtered selection
```

In the new mode `okfreq validate` also checks, in code, that it is a list of
mappings with an `id` matching `S<n>` (`n` from 1, no leading zero), unique ids
and a non-empty `title`. The bundle's own JSON Schema, which refuses a `kind`,
an id such as `P1`, an empty title and an empty list, applies in every mode.

## Acceptance waiver for a whole StRS

A StRS that cannot be accepted by an automated test can carry an authored,
justified waiver, a pair of frontmatter fields on the StRS:

```yaml
acceptance_exemption: true
acceptance_exemption_reason: >-
  The path is an interactive review by a person; no deterministic command
  can accept it. Reviewed in the monthly maintainer session.
```

- It is authored metadata: `update-coverage` preserves it and never generates it.
  A waiver is effective only in the new mode, when the flag is `true` and the
  reason is non-blank. A missing or false flag is not a waiver. With the flag
  `true`, the schema requires the reason, and in the new mode a whitespace-only
  reason is also refused.
- It waives the **whole StRS**, not one `scenarios:` entry. In the new mode, the
  StRS is `covered` when its linked-SwRS condition holds, with `accepted` false.
- It is not acceptance evidence. It creates no marker and changes neither
  `accepted` nor any path count. It does not relax the linked-SwRS rule,
  fragment errors, scenario declarations or `W003`. It suppresses `W004` only.
- The reason explains why automated acceptance is not possible. It does not
  assert that acceptance happened. Being slow or expensive alone is not a
  reason: use `@accepts_req` on the costly test and `@tests_req` on a cheaper one.
- The project owner reviews the waiver under the project's approval rules,
  removes it when no longer justified, and does not use it to hide an
  acceptance test that can be written. `okfreq` does not collect or verify that
  review, and a waiver does not give approval to edit an approved requirement.
- The StRS waiver is distinct from a SwRS's `annotation_exemption` and
  `exemption_reason`. A StRS waiver neither exempts nor fabricates evidence for
  any SwRS; a SwRS exemption does not waive its parent's acceptance. In the new
  mode a linked SwRS with its own non-blank `exemption_reason` satisfies its
  parent's linked-SwRS condition and is reported `exempt`, not `covered`.

## Counters and coverage

In the new mode, for a StRS that **declares** `scenarios:`:

- `total` is the number of declared paths;
- `tested` is the number of declared paths with at least one counting
  `@tests_req StRS-ID#S<n>`;
- `accepted` is the number of declared paths with at least one counting
  `@accepts_req StRS-ID#S<n>`.

The StRS is **tested** when `tested == total` and **accepted** when
`accepted == total`. The two counters are independent. For a StRS that declares
**no** `scenarios:`, `paths` is `{total: 0, tested: 0, accepted: 0}`; it is
tested when a fragmentless `@tests_req` counts and accepted when a fragmentless
`@accepts_req` counts.

The StRS `status` is `covered` when it has at least one linked SwRS, each either
test-covered or individually exempted with a non-blank reason, **and** it is
accepted or has a justified waiver. "Tested" does not change the status.

A SwRS that declares transitions is test-covered only when every declared
`S<n>` has a counting `@tests_req SwRS-ID#S<n>`; without `scenarios:` any
fragmentless `@tests_req SwRS-ID` covers it, as before. Source coverage is
unchanged.

### Generated fields

`accepted_in_files` is a supported generated field, and `okfreq init` lists it
in `generated_fields`. In the new mode `okfreq update-coverage` writes, each only
when it is listed in `generated_fields`:

- on a SwRS, `tested_in_files`: the files of its counting `@tests_req` markers
  only (fragmentless when it declares no transitions, with a declared `#S<n>`
  when it does); a rejected marker's file is not listed;
- on a StRS, `tested_in_files` (counting `@tests_req`) and `accepted_in_files`
  (counting `@accepts_req`), both sorted.

A field not listed in `generated_fields` is left untouched: an existing value
stays, none is added. In the old modes `update-coverage` removes
`tested_in_files` and `accepted_in_files` from a StRS whatever `generated_fields`
says. Neither field is ever authored.

## Findings

In the new mode `okfreq validate` and `okfreq lint` run the marker scan. Errors
carry no code, make both commands exit with status 1, and appear in the
`diagnostics.errors` of the requirement they name in the report. The warnings
`W003` and `W004` are printed as `W00n <file>: ...`, with or without `--prose`,
and never change the exit code. The messages quote the configured keywords; the
defaults are shown.

| Finding | Message | How to fix |
|---|---|---|
| Fragment missing | `<file>:<line>: @tests_req SwRS-X has no scenario fragment; SwRS-X declares scenarios S1, S2: write @tests_req SwRS-X#S<n> (this marker does not count)`. The same text for `@tests_req` and `@accepts_req` on a StRS that declares paths. | Name the scenario the test really exercises: `@tests_req SwRS-X#S1`. If the test exercises none, remove the marker. |
| Unknown fragment | `<file>:<line>: @accepts_req StRS-X#S4 names no declared scenario of StRS-X (declared: S1, S2)`; when none is declared it ends `(StRS-X declares no scenarios:)`. | Fix the fragment, or declare the scenario in `scenarios:` first. Ids are never reused. |
| `@accepts_req` on a SwRS | `<test file>:<line>: @accepts_req SwRS-X: Never present. @accepts_req names a StRS main path; mark a SwRS test with @tests_req <SwRS-ID>#S<n>.` | Use `@tests_req SwRS-X#S<n>` on a SwRS, and put `@accepts_req` on the StRS. |
| Malformed `scenarios:` | `<file>: scenarios: <problem> (each entry is {id: S<n>, title: <text>}, ids unique)` | Make each entry `{id: S<n>, title: <text>}` with unique ids. |
| Bundle schema older than 0.18.0 | `<swrs.schema.yaml path>: accepted_in_files is not refused; mode linked-swrs-and-acceptance-paths needs the okf-schema 0.18.0 declaration: update the bundle schema by adding under properties:` followed by the declaration. | Add the declaration below to `tiers/_schema/swrs.schema.yaml`, under `properties:`. `okfreq init` never replaces existing schemas. |
| `W003` | `W003 <file>: StRS-X declares no scenarios: ...` names the StRS and its file, quotes the headings of its body, gives a `scenarios:` block to paste, says to edit the frontmatter only (and to log it in `tiers/log.md` on an approved StRS) and ends with the link to {ref}`okfreq-declared-scenarios`. One per live StRS with no `scenarios:`. | Paste the block, adjust titles and ids, align the body headings. |
| `W004` | `W004 <file>: StRS-X has no acceptance test: no @accepts_req marker that counts names it. ...` ending with the link to {ref}`okfreq-execution-cost`. One per live StRS on which no `@accepts_req` counts, unless it has a justified waiver. | Mark the test closest to the final product with `@accepts_req StRS-X#S<n>`, or, if it cannot be automated, document a justified waiver. |

"Live" means any lifecycle except `deprecated` and `superseded`, `draft`
included. A StRS with a single counting `@accepts_req`, even `accepted 1/3`, gets
no `W004`. `W003` and `W004` are independent: a non-waived live StRS with no
`scenarios:` and no acceptance test gets both, and a waived one still gets
`W003`. A SwRS with `### Scenario` headings and no `scenarios:` gets no finding.

The `W003` block understands legacy headings (`Path 1: Title`, `Scenario: Title`)
and explicit-id headings (`Path S2: Title`, `Scenario S2: Title`). It takes the
title after the prefix, keeps explicit ids, and assigns unique ids to the other
headings without colliding. With no heading it suggests one placeholder entry,
`- id: S1` and `title: <main path title>`.

The declaration that a pre-0.18.0 `swrs.schema.yaml` needs, under `properties:`:

```yaml
accepted_in_files:
  type: array
  maxItems: 0
  description: Never present. @accepts_req names a StRS main path; mark a SwRS test
    with @tests_req <SwRS-ID>#S<n>.
```

## Report fields

`format_version` is `2` in every mode. In the old modes the report keeps its
shape; the fields below exist in the new mode only. Generate it with
`okfreq generate-report`.

Per StRS, `stakeholder_test_coverage` gains:

| Field | Meaning |
|---|---|
| `paths` | `{total, tested, accepted}`: declared paths and the counters. |
| `tested`, `accepted` | Booleans: every path tested or accepted (or, without `scenarios:`, a counting fragmentless marker). |
| `tests` | `status` (`defined` or `missing`), `files` and `count` of the counting `@tests_req` markers on the StRS (its `tested_in_files`). |
| `acceptance_tests` | The same, for the counting `@accepts_req` markers (its `accepted_in_files`). |
| `validation_tests` | Kept for compatibility. In the new mode it has the same files and status as `acceptance_tests`. |
| `acceptance_exemption` | Present only with a justified waiver: `{"reason": "<authored reason>"}`. |

The waiver never changes `accepted`, `acceptance_tests`, `validation_tests` or
`paths.accepted`; actual markers alone determine those. A linked SwRS with its
own justified annotation exemption has `linked_swrs[].status` `exempt`.

Two differences are worth stating, because the same words mean different things:

- `stakeholder_test_coverage.tests` of a StRS lists its `@tests_req` files,
  while the StRS record's own `tests` (the `tests` of the requirement entry)
  follows `validation_tests`, that is the `@accepts_req` files in the new mode.
- `marker_coverage.tested` is a **link count**: the number of leaf IDs with at
  least one counting `@tests_req`. `totals.tested` is the **test-covered**
  count. A SwRS that declares S1 and S2 and has a counting marker on S1 only is
  counted in `marker_coverage.tested`, is listed in
  `marker_coverage.missing_tests` and is not in `totals.tested`.

In the new mode, `marker_coverage`, `legacy.marker_coverage` and each SwRS's
`tests.files` hold only counting markers; `validation_tests` there maps each StRS
to its `acceptance_tests` files. The rejected markers appear only in the errors.
`okfreq trace --json` is different: its `validation_tests` keeps the raw
`@tests_req` files on a StRS in every mode, and it adds `accepted` and
`scenario_markers` (one entry per marker, fragment and file, with its first
line).

Per SwRS that declares transitions, `transitions` is
`{"tested": ["S1"], "missing": ["S2"]}`. The aggregate
`stakeholder_test_coverage.paths` sums `total`, `tested` and `accepted` over all
StRS, a waived StRS included, counting only actual accepted paths.

The Markdown summary gains `- StRS paths: tested <t>/<n>, accepted <a>/<n>`,
the "By stakeholder requirement" table gains `Tested` and `Accepted` columns
(`2/3`, with ✅ when complete; `✅ no paths` or `❌ no paths` for a StRS
without paths), and the "By software requirement" table gains
`Missing transitions` (`S2, S3`, or `—`). A waived StRS's `Accepted` cell says
`exempt` instead of claiming acceptance.

## Worked examples

The three examples start from `okfreq init requirements` with this change in
`requirements/config.yml`, and the default `default` scope, whose sources are in
`src` and tests in `tests`:

```{code-block} yaml
:caption: Setup: mode in requirements/config.yml

strs_test_coverage_mode: linked-swrs-and-acceptance-paths
```

### Example 1: three paths, tested 2/3, accepted 1/3

A StRS declares three paths. Two have a cheap `@tests_req` test; a third has
only an `@accepts_req` test, so it is accepted and not tested. The StRS is not
covered, since only one of three paths is accepted.

```{code-block} yaml
:caption: Example 1: frontmatter of StRS-default-001

---
type: StRS
id: StRS-default-001
uuid: 5b0e2a54-6c52-4e0a-9d5e-6f1a3c1b9a01
title: Export portable reports
description: When report export is requested, the reporting capability SHALL make a portable report available.
project: demo
scope: default
req_lifecycle: proposed
status: stable
origin: native
tier: StRS
derives_from: []
user_need: Users need a portable report for offline review.
scenarios:
  - id: S1
    title: Export every row
  - id: S2
    title: Export a filtered selection
  - id: S3
    title: Export an empty selection
---
```

Its one linked SwRS is fully covered, which keeps the example about the paths:

```{code-block} yaml
:caption: Example 1: frontmatter of SwRS-default-001

---
type: SwRS
id: SwRS-default-001
uuid: 8c1f0c1e-3d7a-4a43-8a5f-2d6f9b7a1c02
title: Write CSV output
description: When export is requested, the service SHALL write the selected rows as UTF-8 CSV.
project: demo
scope: default
req_lifecycle: proposed
status: stable
origin: native
tier: SwRS
derives_from:
  - StRS-default-001
annotation_exemption: false
---
```

```{code-block} python
:caption: Example 1: tests/test_export.py

# @tests_req SwRS-default-001
# @tests_req StRS-default-001#S1
def test_export_every_row():
    ...


# @tests_req StRS-default-001#S2
def test_export_filtered_selection():
    ...
```

```{code-block} python
:caption: Example 1: tests/test_acceptance_export.py

# @accepts_req StRS-default-001#S3
def test_export_empty_selection_as_a_user_runs_it():
    ...
```

`okfreq generate-report` gives, for the StRS (`requirements[].stakeholder_test_coverage`):

```{code-block} json
:caption: Example 1: JSON excerpt

{
  "status": "missing",
  "mode": "linked-swrs-and-acceptance-paths",
  "linked_swrs": [{"id": "SwRS-default-001", "status": "covered"}],
  "validation_tests": {"status": "defined", "files": ["tests/test_acceptance_export.py"], "count": 1},
  "paths": {"total": 3, "tested": 2, "accepted": 1},
  "tested": false,
  "accepted": false,
  "tests": {"status": "defined", "files": ["tests/test_export.py"], "count": 1},
  "acceptance_tests": {"status": "defined", "files": ["tests/test_acceptance_export.py"], "count": 1}
}
```

```{code-block} markdown
:caption: Example 1: Markdown row

- StRS paths: tested 2/3, accepted 1/3

| Scope | Tier | ID | Name | Tests | Tested | Accepted |
| --- | --- | --- | --- | --- | --- | --- |
| default | StRS | StRS-default-001 | Export portable reports | ❌ missing | 2/3 | 1/3 |
```

Both columns are shown because the counters are independent: S1 and S2 are
tested but not accepted, S3 is accepted but not tested. `validation_tests` and
`acceptance_tests` list the same files. Accepting S1 and S2 with `@accepts_req`
markers would make the StRS covered.

### Example 2: a SwRS with a transition left untested

A SwRS declares two transitions and only `S1` has a test. The SwRS is not
test-covered, so neither is its StRS. It derives from the StRS of Example 1
(use that frontmatter, without Example 1's other files).

```{code-block} yaml
:caption: Example 2: frontmatter of SwRS-default-002

---
type: SwRS
id: SwRS-default-002
uuid: 3e9a7d42-0b1c-4f5e-9c3d-7a8b6c5d4e03
title: Write CSV rows
description: When export is requested, the service SHALL write each selected row as one UTF-8 CSV line.
project: demo
scope: default
req_lifecycle: proposed
status: stable
origin: native
tier: SwRS
derives_from:
  - StRS-default-001
annotation_exemption: false
scenarios:
  - id: S1
    title: Write the selected rows
  - id: S2
    title: Write an empty selection
---
```

```{code-block} python
:caption: Example 2: tests/test_csv.py

# @tests_req SwRS-default-002#S1
def test_write_selected_rows():
    ...
```

```{code-block} json
:caption: Example 2: JSON excerpt

{
  "id": "SwRS-default-002",
  "tests": {"status": "missing", "files": ["tests/test_csv.py"], "count": 1},
  "transitions": {"tested": ["S1"], "missing": ["S2"]}
}
```

```{code-block} markdown
:caption: Example 2: Markdown row

| Scope | Tier | ID | Name | Source | Tests | Missing transitions |
| --- | --- | --- | --- | --- | --- | --- |
| default | SwRS | SwRS-default-002 | Write CSV rows | ❌ missing | ❌ missing | S2 |
```

The record is excerpted from `requirements[]`. Source is `❌ missing` only because
this example has no `@implements_req` marker. The StRS's `linked_swrs` lists
`SwRS-default-002` as `missing`, so the StRS is not covered whatever its paths
say. `marker_coverage.tested` counts the SwRS (a link count) and
`marker_coverage.missing_tests` lists it, while `totals.tested` does not count it.

### Example 3: a StRS with no `scenarios:`

A fragmentless `@tests_req` counts when the StRS declares no paths, so it is
tested. With no acceptance marker it is not accepted. `okfreq validate` prints
`W003`, which asks an agent to declare the paths, and `W004`, because no
acceptance test exists.

```{code-block} markdown
:caption: Example 3: StRS-default-003 (frontmatter and body)

---
type: StRS
id: StRS-default-003
uuid: c4d2b8f6-1a3e-4b7c-8d9e-0f1a2b3c4d05
title: Review a report offline
description: When a report is exported, the reporting capability SHALL make it reviewable without the application.
project: demo
scope: default
req_lifecycle: proposed
status: stable
origin: native
tier: StRS
derives_from: []
user_need: Reviewers need to read a report without the application.
---

## Review a report offline

### Normative behavior

When a report is exported, the reporting capability SHALL make it reviewable without the application.

### Main paths

#### Path 1: Open the exported report

1. The reviewer opens the exported file.
2. The report is readable.

#### Path 2: Comment on a line

1. The reviewer adds a comment to one line.
2. The comment is saved in the file.
```

```{code-block} python
:caption: Example 3: tests/test_review.py

# @tests_req StRS-default-003
def test_review_an_exported_report():
    ...
```

```{code-block} text
:caption: Example 3: okfreq validate output (W003 and W004)

W003 requirements/tiers/strs/StRS-default-003.md: StRS-default-003 declares no scenarios:. Headings found in the body: "#### Path 1: Open the exported report"; "#### Path 2: Comment on a line". Add this block to the frontmatter, editing the frontmatter only (on an approved requirement, log the change in the bundle's tiers/log.md):
scenarios:
- id: S1
  title: Open the exported report
- id: S2
  title: Comment on a line
https://okf-schema.readthedocs.io/en/stable/reference/okfreq-frontmatter.html#okfreq-declared-scenarios
W004 requirements/tiers/strs/StRS-default-003.md: StRS-default-003 has no acceptance test: no @accepts_req marker that counts names it. Mark the test closest to the final product that walks each main path with @accepts_req StRS-default-003#S<n> (@accepts_req StRS-default-003 while it declares no scenarios:). That test may be costly and run in the main-branch pipeline, beside cheaper @tests_req tests run on every pull or merge request. See https://okf-schema.readthedocs.io/en/stable/explanation/okfreq-acceptance-paths.html#okfreq-execution-cost
```

```{code-block} json
:caption: Example 3: JSON excerpt

{
  "status": "missing",
  "mode": "linked-swrs-and-acceptance-paths",
  "linked_swrs": [],
  "validation_tests": {"status": "missing", "files": [], "count": 0},
  "paths": {"total": 0, "tested": 0, "accepted": 0},
  "tested": true,
  "accepted": false,
  "tests": {"status": "defined", "files": ["tests/test_review.py"], "count": 1},
  "acceptance_tests": {"status": "missing", "files": [], "count": 0}
}
```

```{code-block} markdown
:caption: Example 3: Markdown row

| Scope | Tier | ID | Name | Tests | Tested | Accepted |
| --- | --- | --- | --- | --- | --- | --- |
| default | StRS | StRS-default-003 | Review a report offline | ❌ missing | ✅ no paths | ❌ no paths |
```

Both warnings stay until the author acts: declare the paths (then the marker
needs `#S1` or `#S2`, and the fragmentless one becomes an error), and add an
`@accepts_req` marker to the acceptance test, or document a justified waiver.
`W003` still appears with a waiver; `W004` does not.

## Limits

- Markers are file-level references. A marker says that a file names the
  requirement or path, not that a function verifies it.
- Counters are linkage. `okfreq` does not read test results and does not check
  where or how a test runs.
- Ids are never reused, even after a scenario is removed. This is guidance;
  `okfreq` does not check it, nor that `scenarios:` titles equal the headings of
  the body.

See also the [frontmatter reference](okfreq-frontmatter.md), the
[configuration reference](okfreq-configuration.md) and the
[CLI reference](okfreq-cli.md).
