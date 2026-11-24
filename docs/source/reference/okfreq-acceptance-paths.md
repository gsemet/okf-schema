(okfreq-acceptance-paths-reference)=

# Acceptance paths and scenario markers

This page is the exact contract of the `strs_test_coverage_mode` value
`linked-swrs-and-acceptance-paths`: the markers, the `#S<n>` fragment, what each
marker counts for, the findings, and the report fields. For why it works this way
and how to choose between the two test verbs, read
[Why okfreq measures acceptance paths](../explanation/okfreq-acceptance-paths.md).
The `scenarios:` field itself is described in {ref}`okfreq-declared-scenarios`.

"The new mode" below means `strs_test_coverage_mode:
linked-swrs-and-acceptance-paths`; "the old modes" are `linked-swrs` (the default)
and `linked-swrs-and-validation-test`. A **counting** marker is one that the new
mode accepts: a rejected marker is reported as an error and counts toward nothing.

## The markers

Three marker kinds, each with its key under `markers` in `config.yml`. The two test
markers are read only in a scope's `test_dirs`; the implementation marker only in
its `source_dirs`.

| Config key | Default keyword | Meaning |
|---|---|---|
| `markers.implements` | `@implements_req` | implementation of a SwRS |
| `markers.tests` | `@tests_req` | test of a SwRS or a StRS, or of one of its scenarios |
| `markers.accepts` | `@accepts_req` | acceptance test of a StRS, or of one of its main paths |

`okfreq init` writes the three keys. A `config.yml` written before 0.18.0, with only
`implements` and `tests`, gets `accepts: '@accepts_req'` by default. Two kinds
configured with the same keyword are refused (`markers.tests and markers.accepts
use the same keyword …`): the kind of a marker would be ambiguous.

### Which verb for which test

| Verb | Target | Recommended for |
|---|---|---|
| `@tests_req <ID>#S<n>` | a SwRS transition or a StRS main path | the cheaper tests run on every pull or merge request |
| `@accepts_req <StRS-ID>#S<n>` | a StRS main path only | the test closest to the final product, which may be costly and run in the main-branch pipeline; or any test of the path when the tests are cheap |

The right column is a recommendation, not a check: okfreq does not know where or
how a test runs. It only reads the markers. See
{ref}`okfreq-execution-cost`.

## The fragment

A test marker names one scenario of its requirement with a fragment glued to the
ID: `#` followed by `S` and digits, ending before any letter, digit, `_` or `-`.

```text
@tests_req SwRS-CORE-001#S2      fragment S2
@accepts_req StRS-CORE-001#S1    fragment S1
@tests_req SwRS-CORE-001#path1   no fragment: the suffix is ignored
@tests_req SwRS-CORE-001#S1a     no fragment: the suffix is ignored
@tests_req SwRS-CORE-001#S0      fragment S0, which no scenario can declare
```

Any other suffix (`#path1`, `#s1`, `#S1a`, a lone `#`) is not a fragment: the
marker is read without fragment, as before 0.18.0. `#S0` and `#S01` are fragments
that name no declarable id, so in the new mode they are the unknown-fragment
error. `@implements_req` never carries a fragment. Write one marker per line; a
test that walks two paths carries two lines. A custom `markers.id_pattern` must
not admit `#`, or the fragment becomes part of the ID.

## Mode comparison

| | `linked-swrs` (default) | `linked-swrs-and-validation-test` | `linked-swrs-and-acceptance-paths` |
|---|---|---|---|
| SwRS test-covered when | at least one `@tests_req SwRS-X` | same | every declared transition has a `@tests_req SwRS-X#S<n>`; without `scenarios:`, at least one `@tests_req SwRS-X` |
| StRS covered when | it derives at least one SwRS and every linked SwRS is test-covered | the same, and at least one `@tests_req StRS-X` | the same linked-SwRS rule, and the StRS is **accepted** |
| `@tests_req` on a StRS | counts toward nothing | the StRS's validation test | marks a main path (or the StRS) **tested**; reported, never required |
| `@accepts_req` on a StRS | counts toward nothing | counts toward nothing | marks a main path (or the StRS) **accepted** |
| `#S<n>` fragment | ignored | ignored | mandatory on a requirement that declares `scenarios:`; checked against them |
| `scenarios:` | accepted, not checked by code | same | checked; drives the counters |
| Findings | none of the below | none of the below | errors below, `W003`, `W004` |

In every mode, `okfreq trace` counts `@accepts_req` markers, an `@accepts_req` on an
unknown ID is listed in `missing_ids`, and `okfreq retire` refuses a draft that an
`@accepts_req` marker still names.

## Every combination

The old modes behave as before 0.18.0: `@accepts_req` counts toward nothing, a
suffix on any marker is ignored, `@tests_req StRS-X` (with or without suffix) is the
validation test of `linked-swrs-and-validation-test`, and no new finding is
reported. The only refusal is the one of the bundle's own JSON Schema on a
malformed `scenarios:` (a `kind` key, an id that is not `S<n>`, an empty title or
an empty list).

In the new mode one fragment rule applies to every test marker: when the targeted
requirement declares `scenarios:`, the marker must carry one of its declared
`#S<n>`; when it declares none, a fragmentless marker counts for the whole
requirement and any `#S<n>` is an error. "Fragmentless" includes a marker whose
suffix is not a fragment.

| Marker | Target declares `scenarios:` | Target declares none |
|---|---|---|
| `@tests_req StRS-X#S<n>`, `S<n>` declared | path `S<n>` **tested** | — |
| `@accepts_req StRS-X#S<n>`, `S<n>` declared | path `S<n>` **accepted** | — |
| `@tests_req` or `@accepts_req StRS-X#S<n>`, `S<n>` not declared | **error**, does not count | **error**, does not count |
| `@tests_req StRS-X` fragmentless | **error**, does not count | counts: StRS **tested** |
| `@accepts_req StRS-X` fragmentless | **error**, does not count | counts: StRS **accepted** |
| `@tests_req SwRS-X#S<n>`, `S<n>` declared | transition `S<n>` tested | — |
| `@tests_req SwRS-X#S<n>`, `S<n>` not declared | **error**, does not count | **error**, does not count |
| `@tests_req SwRS-X` fragmentless | **error**, does not count | covers the whole SwRS, as in the old modes |
| `@accepts_req SwRS-X`, any suffix | **error**, from the SwRS schema | same |
| `@implements_req SwRS-X` | unchanged | unchanged |

These rules apply to StRS and SwRS targets. A marker on a tier a project adds keeps
the old handling, with no fragment check and no finding: a `@tests_req` on a parent
tier is listed in `non_leaf`, on a leaf tier it counts as before, and an
`@accepts_req` on it counts toward nothing.

A StRS is **tested** when every declared path has a counting `@tests_req …#S<n>`,
and **accepted** when every declared path has a counting `@accepts_req …#S<n>`.
The two counters are independent: a path with only `@accepts_req` is accepted and
not tested. A StRS without `scenarios:` is tested, or accepted, by one counting
fragmentless marker of that verb. Its `status` is `covered` when it derives at least
one SwRS, every linked SwRS is test-covered, and it is accepted; "tested" is
reported beside it and never changes the status.

## Worked examples

Each example starts from `okfreq init` in an empty project, with
`strs_test_coverage_mode: linked-swrs-and-acceptance-paths` in
`.agents/requirements/config.yml`, then `okfreq new` for each requirement (scope
`default`) and its `scenarios:` as shown. The excerpts are what `okfreq
generate-report` and `okfreq validate` print for these files; a test of this
repository builds each example from this page and compares.

### 1. Tested 2/3, accepted 1/3

A StRS declares three main paths. Cheap tests walk the first two; one acceptance
test walks the third. Its SwRS declares no transitions, so one fragmentless test
covers it.

```{code-block} yaml
:caption: Example 1: frontmatter of StRS-default-001

id: StRS-default-001
type: StRS
title: Export a report
description: Users SHALL export a report of the rows they select.
scenarios:
  - id: S1
    title: Export the selected rows
  - id: S2
    title: Export an empty selection
  - id: S3
    title: Open the exported report in a spreadsheet
```

```{code-block} yaml
:caption: Example 1: frontmatter of SwRS-default-001

id: SwRS-default-001
type: SwRS
title: Write CSV rows
description: The tool SHALL write each selected row as one CSV line.
derives_from: [StRS-default-001]
```

```{code-block} python
:caption: Example 1: tests/test_export.py

# @tests_req SwRS-default-001
def test_write_rows(): ...


# @tests_req StRS-default-001#S1
def test_export_selected_rows(): ...


# @tests_req StRS-default-001#S2
def test_export_empty_selection(): ...
```

```{code-block} python
:caption: Example 1: tests/test_acceptance_export.py

# @accepts_req StRS-default-001#S3
def test_open_the_exported_report_in_a_spreadsheet(): ...
```

Path `S3` is accepted and not tested, `S1` and `S2` are tested and not accepted: the
counters are independent. The StRS is neither tested (2/3) nor accepted (1/3), so it
is not covered, although its linked SwRS is.

```{code-block} json
:caption: Example 1: report JSON excerpt

{
  "stakeholder_test_coverage": {
    "covered": 0,
    "paths": {"total": 3, "tested": 2, "accepted": 1}
  },
  "requirements": [
    {
      "id": "StRS-default-001",
      "tests": {"files": ["tests/test_acceptance_export.py"], "count": 1},
      "stakeholder_test_coverage": {
        "status": "missing",
        "linked_swrs": [{"id": "SwRS-default-001", "status": "covered"}],
        "paths": {"total": 3, "tested": 2, "accepted": 1},
        "tested": false,
        "accepted": false,
        "tests": {"status": "defined", "files": ["tests/test_export.py"], "count": 1},
        "acceptance_tests": {
          "status": "defined",
          "files": ["tests/test_acceptance_export.py"],
          "count": 1
        },
        "validation_tests": {
          "status": "defined",
          "files": ["tests/test_acceptance_export.py"],
          "count": 1
        }
      }
    }
  ]
}
```

```{code-block} markdown
:caption: Example 1: Markdown report rows

- StRS paths: tested 2/3, accepted 1/3

| Scope | Tier | ID | Name | Tests | Tested | Accepted |
| --- | --- | --- | --- | --- | --- | --- |
| default | StRS | StRS-default-001 | Export a report | ❌ missing | 2/3 | 1/3 |
```

```{code-block} text
:caption: Example 1: okfreq validate output

2 requirements, 0 errors, 0 warnings
```

### 2. A SwRS transition without a test

The SwRS declares two transitions and only `S1` has a test. The StRS is accepted,
but it is not covered, because its linked SwRS is not.

```{code-block} yaml
:caption: Example 2: frontmatter of StRS-default-001

id: StRS-default-001
type: StRS
title: Export a report
description: Users SHALL export a report of the rows they select.
scenarios:
  - id: S1
    title: Export the selected rows
```

```{code-block} yaml
:caption: Example 2: frontmatter of SwRS-default-001

id: SwRS-default-001
type: SwRS
title: Write CSV rows
description: The tool SHALL write each selected row as one CSV line.
derives_from: [StRS-default-001]
scenarios:
  - id: S1
    title: Write the selected rows
  - id: S2
    title: Write an empty selection
```

```{code-block} python
:caption: Example 2: tests/test_csv.py

# @tests_req SwRS-default-001#S1
def test_write_selected_rows(): ...
```

```{code-block} python
:caption: Example 2: tests/test_acceptance_export.py

# @accepts_req StRS-default-001#S1
def test_export_the_selected_rows(): ...
```

The SwRS is listed in `missing_tests` and is not test-covered (`totals.tested` is
0), while `marker_coverage.tested`, a count of requirements with at least one
counting test marker, is 1.

```{code-block} json
:caption: Example 2: report JSON excerpt

{
  "totals": {"tested": 0},
  "marker_coverage": {"tested": 1, "missing_tests": ["SwRS-default-001"]},
  "stakeholder_test_coverage": {
    "covered": 0,
    "paths": {"total": 1, "tested": 0, "accepted": 1}
  },
  "requirements": [
    {
      "id": "StRS-default-001",
      "stakeholder_test_coverage": {
        "status": "missing",
        "linked_swrs": [{"id": "SwRS-default-001", "status": "missing"}],
        "paths": {"total": 1, "tested": 0, "accepted": 1},
        "tested": false,
        "accepted": true
      }
    },
    {
      "id": "SwRS-default-001",
      "tests": {"status": "missing", "files": ["tests/test_csv.py"], "count": 1},
      "transitions": {"tested": ["S1"], "missing": ["S2"]}
    }
  ]
}
```

```{code-block} markdown
:caption: Example 2: Markdown report rows

- StRS paths: tested 0/1, accepted 1/1

| Scope | Tier | ID | Name | Tests | Tested | Accepted |
| --- | --- | --- | --- | --- | --- | --- |
| default | StRS | StRS-default-001 | Export a report | ❌ missing | 0/1 | ✅ 1/1 |

| Scope | Tier | ID | Name | Source | Tests | Missing transitions |
| --- | --- | --- | --- | --- | --- | --- |
| default | SwRS | SwRS-default-001 | Write CSV rows | ❌ missing | ❌ missing | S2 |
```

```{code-block} text
:caption: Example 2: okfreq validate output

2 requirements, 0 errors, 0 warnings
```

### 3. A StRS without `scenarios:`

The StRS body has a `### Main paths` section, but its frontmatter declares no
`scenarios:`. A fragmentless `@tests_req` counts, and nothing accepts it.

```{code-block} yaml
:caption: Example 3: frontmatter of StRS-default-001

id: StRS-default-001
type: StRS
title: Export a report
description: Users SHALL export a report of the rows they select.
```

```{code-block} markdown
:caption: Example 3: body of StRS-default-001 (excerpt)

### Main paths

#### Path 1: Export the selected rows

1. The user selects rows and asks for a report.
2. The report lists exactly the selected rows.

#### Path 2: Export an empty selection

1. The user asks for a report with no row selected.
2. The report holds only its header line.
```

```{code-block} python
:caption: Example 3: tests/test_export.py

# @tests_req StRS-default-001
def test_export_selected_rows(): ...
```

Without `scenarios:` the StRS has no paths to count: the fragmentless `@tests_req`
makes it tested, and nothing makes it accepted. Its `stakeholder_test_coverage.tests`
lists the `@tests_req` file, while the record's own `tests` follows
`validation_tests`, the `@accepts_req` files, here none.

```{code-block} json
:caption: Example 3: report JSON excerpt

{
  "requirements": [
    {
      "id": "StRS-default-001",
      "tests": {"files": [], "count": 0},
      "stakeholder_test_coverage": {
        "status": "missing",
        "paths": {"total": 0, "tested": 0, "accepted": 0},
        "tested": true,
        "accepted": false,
        "tests": {"status": "defined", "files": ["tests/test_export.py"], "count": 1},
        "acceptance_tests": {"status": "missing", "files": [], "count": 0},
        "validation_tests": {"status": "missing", "files": [], "count": 0}
      }
    }
  ]
}
```

```{code-block} markdown
:caption: Example 3: Markdown report rows

| Scope | Tier | ID | Name | Tests | Tested | Accepted |
| --- | --- | --- | --- | --- | --- | --- |
| default | StRS | StRS-default-001 | Export a report | ❌ missing | ✅ no paths | ❌ no paths |
```

`okfreq validate` exits 0 and prints `W003`, with the `scenarios:` block to paste
built from the body's path headings, and `W004` (file paths shown relative to the
project):

```{code-block} text
:caption: Example 3: okfreq validate output

1 requirements, 0 errors, 2 warnings
W003 .agents/requirements/tiers/strs/StRS-default-001.md: StRS-default-001 declares no scenarios: (its main paths). Headings found in its body: "Path 1: Export the selected rows"; "Path 2: Export an empty selection"
Add to its frontmatter, one entry per main path:
scenarios:
- id: S1
  title: Export the selected rows
- id: S2
  title: Export an empty selection
Edit the frontmatter only and leave the body as it is; on an approved StRS, log the change in the bundle's tiers/log.md naming the owner's agreement. See https://okf-schema.readthedocs.io/en/stable/reference/okfreq-frontmatter.html#okfreq-declared-scenarios
W004 .agents/requirements/tiers/strs/StRS-default-001.md: StRS-default-001 has no acceptance test: no @accepts_req marker that counts names it. Mark the test closest to the final product that walks each main path with @accepts_req StRS-default-001#S<n> (@accepts_req StRS-default-001 while it declares no scenarios:). That test may be costly and run in the main-branch pipeline, beside cheaper @tests_req tests run on every pull or merge request. See https://okf-schema.readthedocs.io/en/stable/explanation/okfreq-acceptance-paths.html#okfreq-execution-cost
```

Pasting the proposed block into the frontmatter removes `W003`; the fragmentless
`@tests_req StRS-default-001` then becomes an error and must name `#S1` or `#S2`.
An `@accepts_req StRS-default-001#S<n>` on the test closest to the final product
removes `W004`.

## Findings

In the new mode `okfreq validate`, `okfreq lint` and `okfreq status` check the
markers against the declared scenarios. Errors make `validate` and `lint` exit
non-zero; they carry no code. A report lists each error in the
`diagnostics.errors` of the requirement it names. `W003` and `W004` are printed
with or without `--prose` and never change the exit code. Messages use the
configured keywords.

| Finding | Message | Fix |
|---|---|---|
| Fragment missing | `<file>:<line>: @tests_req SwRS-X has no scenario fragment; SwRS-X declares scenarios S1, S2: write @tests_req SwRS-X#S<n> (this marker does not count)` (same for `@tests_req` and `@accepts_req` on a StRS that declares paths) | Add the `#S<n>` of the scenario the test really walks; one line per scenario when it walks several. Remove the marker from a test that walks none. |
| Unknown fragment | `<file>:<line>: @accepts_req StRS-X#S4 names no declared scenario of StRS-X (declared: S1, S2)`, or `… (StRS-X declares no scenarios:)` | Name a declared id, or declare the scenario in `scenarios:` with a new id. |
| `@accepts_req` on a SwRS | `<file>:<line>: @accepts_req SwRS-X: Never present. @accepts_req names a StRS main path; mark a SwRS test with @tests_req <SwRS-ID>#S<n>.` | Use `@tests_req SwRS-X#S<n>`, or put the `@accepts_req` on the StRS path the test walks. |
| Malformed `scenarios:` | `<file>: scenarios: <problem> (each entry is {id: S<n>, title: <text>}, ids unique)` | Each entry has exactly `id` (`S1`, `S2`…, unique) and a non-empty `title`. |
| SwRS schema written before 0.18.0 | `<swrs.schema.yaml>: accepted_in_files is not refused; mode linked-swrs-and-acceptance-paths needs the okf-schema 0.18.0 declaration: update the bundle schema by adding under properties:` and the declaration | See below. |
| `W003` | A live StRS (any lifecycle but `deprecated` and `superseded`) declares no `scenarios:`. The message quotes the headings under `### Main paths` and every `### Scenario…` heading, and gives the `scenarios:` block to paste | Paste the block into the frontmatter, fix the titles, and leave the body as it is. On an approved StRS, log the change in `tiers/log.md`; see {ref}`okfreq-declared-scenarios`. |
| `W004` | A live StRS has no counting `@accepts_req` marker at all | Mark the test closest to the final product that walks each main path with `@accepts_req StRS-X#S<n>`; see {ref}`okfreq-execution-cost`. |

`W004` disappears as soon as one `@accepts_req` counts, even when only one path of
three is accepted: the report's `Accepted` column shows the rest. A SwRS that has
`### Scenario` headings and no `scenarios:` gets no finding.

### Update a bundle schema written before 0.18.0

`okfreq init` never replaces an existing schema, so a bundle created before 0.18.0
has a `tiers/_schema/swrs.schema.yaml` that does not refuse `accepted_in_files`.
Its project cannot use the new mode until it adds, under the `properties:` of that
schema (beside `tested_in_files`), the declaration the error prints:

```yaml
accepted_in_files:
  type: array
  maxItems: 0
  description: Never present. @accepts_req names a StRS main path; mark a SwRS test
    with @tests_req <SwRS-ID>#S<n>.
```

okfreq applies no declaration of its own. While the schema accepts the property,
every `okfreq validate` in the new mode fails with this one error. The other 0.18.0
declarations, `scenarios` in `base.schema.yaml` and `tested_in_files` and
`accepted_in_files` in `strs.schema.yaml`, are recommended but not required, since
an older schema accepts these fields; copy them from a bundle that `okfreq init`
creates in an empty directory. In the old modes the same bundle validates as
before.

## Generated fields

`accepted_in_files` is a supported generated field, listed by `okfreq init`. In the
new mode `okfreq update-coverage` writes, each only when listed in
`generated_fields`:

- on a SwRS, `tested_in_files`: the files of its counting `@tests_req` markers
  (fragmentless when it declares no transitions, with a declared `#S<n>` when it
  does); a rejected marker's file is not listed;
- on a StRS, `tested_in_files` (counting `@tests_req`) and `accepted_in_files`
  (counting `@accepts_req`).

A field that `generated_fields` does not list is left as it is. In the old modes,
`update-coverage` removes `tested_in_files` and `accepted_in_files` from every StRS.

## Report fields

`okfreq generate-report` writes `"format_version": 2` in every mode. The fields
below appear in the new mode only.

| Field | Meaning |
|---|---|
| `stakeholder_test_coverage.paths` (aggregate) | `total`, `tested`, `accepted`: sums over every StRS. |
| `requirements[].stakeholder_test_coverage.paths` (StRS) | `total` declared paths, `tested` paths with a counting `@tests_req`, `accepted` paths with a counting `@accepts_req`. |
| `….tested`, `….accepted` (StRS) | Booleans: every declared path tested, or accepted; for a StRS without paths, at least one counting fragmentless marker of that verb. |
| `….tests` (StRS) | Files of the counting `@tests_req` markers on the StRS (its `tested_in_files`). |
| `….acceptance_tests` (StRS) | Files of the counting `@accepts_req` markers (its `accepted_in_files`). |
| `….validation_tests` (StRS) | Kept for compatibility: the same files and status as `acceptance_tests`. |
| `requirements[].transitions` (SwRS that declares `scenarios:`) | `tested` and `missing` transition ids. |

Three fields keep a name with a different content, on purpose:

- per StRS, `stakeholder_test_coverage.tests` lists the `@tests_req` files, while
  the StRS record's own `tests` follows `validation_tests`, that is the
  `@accepts_req` files in the new mode;
- `marker_coverage.tested` is a link count (requirements with at least one counting
  `@tests_req`), while `totals.tested` counts the test-covered requirements: a SwRS
  with one of two transitions marked counts in the first and not in the second;
- the report's `validation_tests` (in `marker_coverage`,
  `legacy.marker_coverage` and per StRS) holds the counting `@accepts_req` files,
  while `okfreq trace --json`'s `validation_tests` keeps, in every mode, the raw
  `@tests_req` files on each StRS.

In the new mode `marker_coverage`, `legacy.marker_coverage` and each SwRS's
`tests.files` hold only counting markers; a rejected marker appears only in the
errors. `okfreq trace --json` adds `accepted` (ID to files of `@accepts_req`
markers) and `scenario_markers` (one entry per marker kind, ID, fragment and file,
with its first line) in every mode.

The Markdown summary gains the line `- StRS paths: tested <t>/<n>, accepted
<a>/<n>`, the stakeholder table the `Tested` and `Accepted` columns (`2/3`, `✅ 3/3`
when complete, `✅ no paths` or `❌ no paths` for a StRS without `scenarios:`), and
the software table a `Missing transitions` column (`S2, S3`, or `—`). In the old
modes the Markdown report is unchanged.

## See also

- [Why okfreq measures acceptance paths](../explanation/okfreq-acceptance-paths.md)
- {ref}`okfreq-declared-scenarios`
- [Configuration](okfreq-configuration.md), "StRS test-coverage modes"
- [CLI reference](okfreq-cli.md)
