# Acceptance paths and scenario markers

A requirement declares the scenarios it promises. A test marker then names the
one scenario it really walks. In the mode `linked-swrs-and-acceptance-paths`,
`okfreq` counts how many declared stakeholder main paths a test accepts, and how
many are tested, instead of treating one direct StRS marker as a single link.

This page is the contract: the two verbs, the three modes, every combination of
marker, tier, declared scenarios, fragment and mode, the worked examples, the
findings, and the report fields. For the reasoning behind the model, read
[Why okfreq measures acceptance paths](../explanation/okfreq-acceptance-paths.md).

Every example below starts from `okfreq init`, switches
`strs_test_coverage_mode` to `linked-swrs-and-acceptance-paths`, and declares one
scope `core` that scans `src` and `tests`.

## The two verbs

Two marker kinds read tests. They differ by what the test is, not by where it
runs: the test source states its own role, so no configuration can drift away
from it.

| Marker | Targets | Meaning | Recommended for |
|---|---|---|---|
| `@tests_req` | an `SwRS` transition, or an `StRS` main path | a test of the requirement, or of one of its scenarios | the cheaper tests run on every pull or merge request |
| `@accepts_req` | an `StRS` main path only | the acceptance test of a stakeholder main path | the test closest to the final product, possibly costly and run in the main-branch pipeline, or any test when tests are cheap |

`@accepts_req` on an `SwRS` is an error: a software requirement's transition is
a `@tests_req` concern, and the SwRS schema refuses the property it would feed.

The recommendation is a recommendation. `okfreq` records the link and the
counters; it never checks where or how a test runs, how long it takes, or in
which pipeline it executes. See
{ref}`Choosing by execution cost <okfreq-execution-cost>`
for the trade-off.

The counters are independent. A path may be tested only, accepted only, both, or
neither, and each verb has its own counter. A path that only carries
`@accepts_req` is accepted and not tested.

## Modes

`strs_test_coverage_mode` selects the stakeholder-coverage policy.

| Mode | A SwRS is test-covered when | An StRS is covered when | `@tests_req` on an StRS | `@accepts_req` on an StRS |
|---|---|---|---|---|
| `linked-swrs` (default) | it has at least one `@tests_req SwRS-ID` marker | it links to at least one SwRS and every linked SwRS is test-covered | counts as the raw validation-test file list of `trace`/report; fragments ignored; `@accepts_req` counts nothing | counts nothing |
| `linked-swrs-and-validation-test` | same | the `linked-swrs` rule holds, and a direct `@tests_req StRS-ID` is defined | counts as the validation-test definition; fragments ignored | counts nothing |
| `linked-swrs-and-acceptance-paths` | every declared transition carries a `@tests_req SwRS-ID#S<n>`, or at least one fragmentless marker when no transition is declared | the `linked-swrs` rule holds (a linked SwRS may instead be individually exempted) **and** every declared main path is accepted, or the whole StRS carries a justified acceptance waiver | counts only with a declared `#S<n>` fragment, feeding the *tested* path counter | counts only with a declared `#S<n>` fragment, feeding the *accepted* path counter |

In the two older modes `okfreq` accepts `scenarios:` and `@accepts_req` but
requires and counts nothing new: coverage, generated fields and findings stay as
they were. The bundle's own JSON Schema still applies, because it is the schema
`validate_requirements` runs.

Only the new mode applies the rules on this page. A project chooses it with:

```yaml
strs_test_coverage_mode: linked-swrs-and-acceptance-paths
```

## Marker keys and the `#S<n>` fragment

Three marker kinds, with these default keywords and configuration keys:

| Config key | Default keyword | Read in |
|---|---|---|
| `markers.implements` | `@implements_req` | `source_dirs` |
| `markers.tests` | `@tests_req` | `test_dirs` |
| `markers.accepts` | `@accepts_req` | `test_dirs` |

`okfreq init` writes all three. Two kinds configured with the same keyword is a
configuration error, because the kind would be ambiguous.

A marker may carry a fragment that names one declared scenario:

```text
^\s*(?:(?:#|//|/\*|\*|<!--)\s*)?
(?P<marker>@implements_req|@tests_req|@accepts_req)\s+
(?P<identifier>ID)\#(?P<fragment>S[0-9]+)(?![A-Za-z0-9_-])?
```

- The fragment is `#` glued directly to the ID, followed by `S` and digits, and
  it ends at a character that is not part of an ID (`A-Za-z0-9_-`).
- Any other suffix is **not** a fragment and is ignored, as it always was: the
  marker is read without fragment. `#path1`, `#s1`, `#S1a` and a bare `#` all
  leave a fragmentless marker.
- `#S0` and `#S01` *are* fragments, and they name no declarable id: in the new
  mode they are the unknown-fragment error.
- The fragment is not read on `@implements_req`.
- A custom `markers.id_pattern` must not admit `#`, or the ID would swallow the
  fragment.

### One fragment rule, two verbs, two tiers

When the targeted requirement declares `scenarios:`, a `#S<n>` naming a declared
id is mandatory on every test marker. When it declares none, a fragmentless
marker counts for the whole requirement and any fragment is an error.

| Marker | Target declares `scenarios:` | Target declares none |
|---|---|---|
| `@tests_req StRS-X#S<n>`, `S<n>` declared | path `S<n>` **tested** | — |
| `@accepts_req StRS-X#S<n>`, `S<n>` declared | path `S<n>` **accepted** | — |
| `@tests_req` or `@accepts_req StRS-X#S<n>`, `S<n>` not declared | **error**, does not count | **error**, does not count |
| `@tests_req StRS-X` fragmentless | **error**, does not count | the StRS is **tested** |
| `@accepts_req StRS-X` fragmentless | **error**, does not count | the StRS is **accepted** |
| `@tests_req SwRS-X#S<n>`, `S<n>` declared | transition `S<n>` tested | — |
| `@tests_req SwRS-X#S<n>`, `S<n>` not declared | **error**, does not count | **error**, does not count |
| `@tests_req SwRS-X` fragmentless | **error**, does not count | the whole SwRS is test-covered, as in the old modes |
| `@accepts_req SwRS-X`, any suffix | **error**, from the SwRS schema | same |
| `@implements_req SwRS-X` | unchanged: source coverage | unchanged |

## Every combination

The table below reproduces the rules completely. "Old modes" means
`linked-swrs` or `linked-swrs-and-validation-test`; "new" means
`linked-swrs-and-acceptance-paths`. A marker on a tier other than StRS or SwRS
keeps its previous handling in every mode: no fragment check, no merge into its
frontmatter, no new finding.

| Marker | Tier | `scenarios:` | Fragment | Old modes | New mode |
|---|---|---|---|---|---|
| `@implements_req` | SwRS | either | any | source coverage; fragment ignored | source coverage; fragment ignored |
| `@implements_req` | StRS | either | any | recorded, never leaf coverage | recorded, never leaf coverage |
| `@tests_req` | StRS | declared | declared `S<n>` | validation-test files, fragment ignored | path `S<n>` tested |
| `@tests_req` | StRS | declared | undeclared `S<n>` | validation-test files, fragment ignored | error: names no declared scenario |
| `@tests_req` | StRS | declared | other suffix | validation-test files, suffix ignored | error: no scenario fragment |
| `@tests_req` | StRS | declared | none | validation-test files | error: no scenario fragment |
| `@tests_req` | StRS | none | declared `S<n>` | validation-test files, fragment ignored | error: names no declared scenario (`StRS-X declares no scenarios:`) |
| `@tests_req` | StRS | none | other suffix | validation-test files, suffix ignored | counts: StRS tested |
| `@tests_req` | StRS | none | none | validation-test files | counts: StRS tested |
| `@tests_req` | SwRS | declared | declared `S<n>` | test link, fragment ignored | transition `S<n>` tested |
| `@tests_req` | SwRS | declared | undeclared `S<n>` | test link, fragment ignored | error: names no declared scenario |
| `@tests_req` | SwRS | declared | other suffix | test link, suffix ignored | error: no scenario fragment |
| `@tests_req` | SwRS | declared | none | test link | error: no scenario fragment |
| `@tests_req` | SwRS | none | declared `S<n>` | test link, fragment ignored | error: names no declared scenario |
| `@tests_req` | SwRS | none | other suffix | test link, suffix ignored | counts: whole SwRS test-covered |
| `@tests_req` | SwRS | none | none | test link | counts: whole SwRS test-covered |
| `@accepts_req` | StRS | declared | declared `S<n>` | counts nothing | path `S<n>` accepted |
| `@accepts_req` | StRS | declared | undeclared `S<n>` | counts nothing | error: names no declared scenario |
| `@accepts_req` | StRS | declared | other suffix | counts nothing | error: no scenario fragment |
| `@accepts_req` | StRS | declared | none | counts nothing | error: no scenario fragment |
| `@accepts_req` | StRS | none | declared `S<n>` | counts nothing | error: names no declared scenario |
| `@accepts_req` | StRS | none | other suffix | counts nothing | counts: StRS accepted |
| `@accepts_req` | StRS | none | none | counts nothing | counts: StRS accepted |
| `@accepts_req` | SwRS | either | any | counts nothing | error, from the SwRS schema |
| `@tests_req`/`@accepts_req` on another tier | any | either | any | unchanged | unchanged: `@accepts_req` counts nothing, `@tests_req` keeps `marker_scan`'s handling |
| `@implements_req`/`@tests_req`/`@accepts_req` on an unknown ID | — | — | any | `missing_ids` | `missing_ids` |

## Worked example 1: three paths, tested 2/3 and accepted 1/3

One stakeholder requirement declares three main paths. Two cheap tests carry
`@tests_req`, and one acceptance test carries `@accepts_req` on the path that no
cheap test walks. Path `S1` is accepted and not tested: the counters are
independent.

```{code-block} markdown
:caption: example 1 — requirements/tiers/strs/StRS-CORE-001.md

---
type: StRS
id: StRS-CORE-001
uuid: 0d6f2c8e-1f5f-4a0e-9d33-6a1f5c2b7e10
title: Deliver reports
description: When a team asks for a report, the tool SHALL deliver it.
project: demo
scope: core
tier: StRS
req_lifecycle: proposed
origin: native
user_need: Teams need reports.
scenarios:
  - id: S1
    title: Export the report
  - id: S2
    title: Refuse an empty selection
  - id: S3
    title: Report an unwritable destination
---

## Deliver reports

### Normative behavior

The tool SHALL deliver the report the team asked for.

### Main paths

#### Path S1: Export the report

1. The team asks for a report.
2. The tool delivers it.

#### Path S2: Refuse an empty selection

1. The team asks for a report with nothing selected.
2. The tool refuses and says why.

#### Path S3: Report an unwritable destination

1. The team asks for a report at an unwritable path.
2. The tool reports the failure.
```

```{code-block} python
:caption: example 1 — tests/test_flow.py

# @tests_req StRS-CORE-001#S2
def test_refuses_an_empty_selection():
    ...

# @tests_req StRS-CORE-001#S3
def test_reports_an_unwritable_destination():
    ...
```

```{code-block} python
:caption: example 1 — tests/test_acceptance.py

# @accepts_req StRS-CORE-001#S1
def test_exports_the_report():
    ...
```

The report record of the requirement, from
`stakeholder_test_coverage`, is:

```{code-block} json
:caption: example 1 — report excerpt

{
  "StRS-CORE-001": {
    "status": "missing",
    "mode": "linked-swrs-and-acceptance-paths",
    "linked_swrs": [],
    "validation_tests": {
      "status": "defined",
      "files": ["tests/test_acceptance.py"],
      "count": 1
    },
    "paths": {"total": 3, "tested": 2, "accepted": 1},
    "tested": false,
    "accepted": false,
    "tests": {
      "status": "defined",
      "files": ["tests/test_flow.py"],
      "count": 1
    },
    "acceptance_tests": {
      "status": "defined",
      "files": ["tests/test_acceptance.py"],
      "count": 1
    }
  }
}
```

The status stays `missing`: no SwRS is linked, and only one path is accepted. The
Markdown summary shows both columns, with no ✅ because neither counter is
complete:

```{code-block} text
:caption: example 1 — Markdown row

| core | StRS | StRS-CORE-001 | Deliver reports | ❌ missing | 2/3 | 1/3 |
```

## Worked example 2: a SwRS with transitions S1 and S2, only S1 tested

The software requirement declares two transitions and only `S1` carries a test.
The SwRS is not test-covered, so its parent StRS is not covered even though its
single main path is accepted. The SwRS record gains `transitions`.

```{code-block} markdown
:caption: example 2 — requirements/tiers/strs/StRS-CORE-001.md

---
type: StRS
id: StRS-CORE-001
uuid: 0d6f2c8e-1f5f-4a0e-9d33-6a1f5c2b7e10
title: Deliver reports
description: When a team asks for a report, the tool SHALL deliver it.
project: demo
scope: core
tier: StRS
req_lifecycle: proposed
origin: native
user_need: Teams need reports.
scenarios:
  - id: S1
    title: Export the report
---

## Deliver reports

### Normative behavior

The tool SHALL deliver the report the team asked for.

### Main paths

#### Path S1: Export the report

1. The team asks for a report.
2. The tool delivers it.
```

```{code-block} markdown
:caption: example 2 — requirements/tiers/swrs/SwRS-CORE-001.md

---
type: SwRS
id: SwRS-CORE-001
uuid: 3f6a1d92-8c47-4b0e-a1d5-9e52c7b48f31
title: Write CSV output
description: When export is requested, the service SHALL write UTF-8 CSV.
project: demo
scope: core
tier: SwRS
req_lifecycle: proposed
origin: native
derives_from:
  - StRS-CORE-001
annotation_exemption: false
scenarios:
  - id: S1
    title: Produce a report
  - id: S2
    title: Refuse an empty selection
---

## Write CSV output

### Normative behavior

When export is requested, the service SHALL write UTF-8 CSV.

### Scenario S1: Produce a report

- GIVEN a selection
- WHEN export is requested
- THEN a CSV file is written

### Scenario S2: Refuse an empty selection

- GIVEN an empty selection
- WHEN export is requested
- THEN the request is refused
```

```{code-block} python
:caption: example 2 — src/report.py

# @implements_req SwRS-CORE-001
def write_csv():
    ...
```

```{code-block} python
:caption: example 2 — tests/test_flow.py

# @tests_req SwRS-CORE-001#S1
def test_produces_a_report():
    ...
```

```{code-block} python
:caption: example 2 — tests/test_acceptance.py

# @accepts_req StRS-CORE-001#S1
def test_exports_the_report():
    ...
```

The excerpt shows the StRS's `stakeholder_test_coverage` and the SwRS's
`transitions`:

```{code-block} json
:caption: example 2 — report excerpt

{
  "StRS-CORE-001": {
    "status": "missing",
    "mode": "linked-swrs-and-acceptance-paths",
    "linked_swrs": [{"id": "SwRS-CORE-001", "status": "missing"}],
    "validation_tests": {
      "status": "defined",
      "files": ["tests/test_acceptance.py"],
      "count": 1
    },
    "paths": {"total": 1, "tested": 0, "accepted": 1},
    "tested": false,
    "accepted": true,
    "tests": {"status": "missing", "files": [], "count": 0},
    "acceptance_tests": {
      "status": "defined",
      "files": ["tests/test_acceptance.py"],
      "count": 1
    }
  },
  "SwRS-CORE-001": {"tested": ["S1"], "missing": ["S2"]}
}
```

```{code-block} text
:caption: example 2 — Markdown row

| core | StRS | StRS-CORE-001 | Deliver reports | ❌ missing | 0/1 | ✅ 1/1 |
| core | SwRS | SwRS-CORE-001 | Write CSV output | ✅ covered | ✅ covered | S2 |
```

The `Tests` cell of the stakeholder table follows `validation_tests`, which in
the new mode lists the `@accepts_req` files. The `Tests` cell of the software
table shows the SwRS test-link status, which is `covered` here only because
`marker_scan` finds a `@tests_req` marker on the SwRS at all; the missing
transition is what `Missing transitions` reports, and it is what keeps the SwRS
out of `totals.tested`.

## Worked example 3: no `scenarios:`, no acceptance test

A stakeholder requirement declares no scenarios and carries only a fragmentless
`@tests_req`. That marker counts, so the StRS is tested; no `@accepts_req` counts,
so `okfreq validate` prints both warnings.

```{code-block} markdown
:caption: example 3 — requirements/tiers/strs/StRS-CORE-001.md

---
type: StRS
id: StRS-CORE-001
uuid: 0d6f2c8e-1f5f-4a0e-9d33-6a1f5c2b7e10
title: Deliver reports
description: When a team asks for a report, the tool SHALL deliver it.
project: demo
scope: core
tier: StRS
req_lifecycle: proposed
origin: native
user_need: Teams need reports.
---

## Deliver reports

### Normative behavior

The tool SHALL deliver the report the team asked for.

### Main paths

#### Path 1: Export the report

1. The team asks for a report.
2. The tool delivers it.
```

```{code-block} python
:caption: example 3 — tests/test_flow.py

# @tests_req StRS-CORE-001
def test_delivers_the_report():
    ...
```

`okfreq validate` exits 0 and prints, in this order, the W003 block with the
heading it found and the `scenarios:` block to paste, then W004. `<bundle>` is
the bundle root's path:

```{code-block} text
:caption: example 3 — findings

W003 <bundle>/tiers/strs/StRS-CORE-001.md: StRS-CORE-001 declares no scenarios:; headings found:
  - "Path 1: Export the report"
Add this block to the frontmatter (body intact), then add a #S<n> fragment to each test marker:
scenarios:
  - id: S1
    title: Export the report

On an approved StRS, log the change in the bundle's tiers/log.md.
https://okf-schema.readthedocs.io/en/stable/reference/okfreq-frontmatter.html#okfreq-declared-scenarios
W004 <bundle>/tiers/strs/StRS-CORE-001.md: StRS-CORE-001 has no acceptance test: no @accepts_req marker that counts names it. Mark the test closest to the final product that walks each main path with @accepts_req StRS-CORE-001#S<n> (@accepts_req StRS-CORE-001 while it declares no scenarios:). That test may be costly and run in the main-branch pipeline, beside cheaper @tests_req tests run on every pull or merge request. See https://okf-schema.readthedocs.io/en/stable/explanation/okfreq-acceptance-paths.html#okfreq-execution-cost
```

The StRS still reaches `tested: true` with zero paths, and the report records
`"paths": {"total": 0, "tested": 0, "accepted": 0}`.

## Findings and how to fix them

In the new mode `okfreq validate` and `okfreq lint` fail on the errors below
(`okfreq status` counts them, and the report lists each in the `diagnostics.errors`
of the requirement whose ID it contains). Warnings never change the exit code.
Messages use the configured keywords. `W00n` findings are printed with or without
`--prose`.

### Errors

| Finding | Message | How to fix it |
|---|---|---|
| Fragment missing | `<file>:<line>: @tests_req SwRS-X has no scenario fragment; SwRS-X declares scenarios S1, S2: write @tests_req SwRS-X#S<n> (this marker does not count)` | add the `#S<n>` of the scenario the test really walks; the same text appears for `@accepts_req` and for an StRS that declares paths |
| Unknown fragment | `<file>:<line>: @accepts_req StRS-X#S4 names no declared scenario of StRS-X (declared: S1, S2)`; with none declared it ends `(StRS-X declares no scenarios:)` | correct the fragment, or declare the scenario if it really exists; never renumber silently |
| `@accepts_req` on a SwRS | `<test file>:<line>: @accepts_req SwRS-X: Never present. @accepts_req names a StRS main path; mark a SwRS test with @tests_req <SwRS-ID>#S<n>.` — the wording is the SwRS schema's own description of the refused `accepted_in_files` property, so the rule's text and its tier live in the schema | replace it with `@tests_req`; the marker also never counts |
| Malformed `scenarios:` | `<file>: scenarios: <problem> (each entry is {id: S<n>, title: <text>}, ids unique)` | write `scenarios:` as a non-empty list of `{id, title}` mappings with `S<n>` ids that are unique and non-empty titles |
| SwRS schema does not refuse `accepted_in_files` | `<swrs.schema.yaml path>: accepted_in_files is not refused; mode linked-swrs-and-acceptance-paths needs the okf-schema 0.18.0 declaration: update the bundle schema by adding under properties:` followed by the declaration | see {ref}`okfreq-pre-018-schema` |

### `W003`: a live StRS declares no scenarios

`okfreq validate` prints `W003` for a live StRS (any lifecycle but `deprecated`
and `superseded`; `draft` included) that declares no `scenarios:`. One finding
per requirement. It names the requirement and its file, quotes the headings it
found under `### Main paths` and every `### Scenario…` heading (or says none was
found), gives the `scenarios:` block to paste, one entry per heading in order,
tells you to edit the frontmatter only and, on an approved StRS, to log the change
in the bundle's `tiers/log.md`, and ends with the
{ref}`okfreq-declared-scenarios` link.

Fix it by pasting the suggested block. Legacy `Path <n>:` and `Scenario:`
headings, and explicit `Path S<n>:` / `Scenario S<n>:` headings, are understood;
titles come from after the prefix, and explicit ids are kept. This is authoring
guidance: `okfreq` checks the fragments against `scenarios:`, not the headings
against it, so keep both consistent yourself. There is no `W003` for a SwRS
without `scenarios:`, even with `### Scenario` headings.

### `W004`: a live StRS has no acceptance test

`okfreq validate` prints `W004` when no `@accepts_req` marker that counts names a
live StRS: none at all, or only rejected ones. One finding per requirement. A StRS
with at least one counting `@accepts_req`, even `accepted 1/3`, gets none. It is
independent of `W003`: a non-waived live StRS with neither `scenarios:` nor an
acceptance test gets both.

Fix it by marking the test closest to the final product with
`@accepts_req StRS-X#S<n>`, or, while the requirement declares no scenarios, with
`@accepts_req StRS-X`. When the whole requirement genuinely cannot be
acceptance-tested, use a justified waiver instead (below). Read
{ref}`Choosing by execution cost <okfreq-execution-cost>`
before deciding that a test is too expensive to mark.

(okfreq-pre-018-schema)=

### A bundle schema written before 0.18.0

`okfreq init` never replaces existing schemas, so a bundle created before 0.18.0
has an `swrs.schema.yaml` that does not declare `accepted_in_files`, and nothing
then refuses `@accepts_req` on a SwRS. In the new mode, `okfreq validate` checks
that the composed SwRS tier schema refuses the property, and fails with one error
whether or not a marker uses it. Add this under `properties:` of
`tiers/_schema/swrs.schema.yaml`:

```yaml
accepted_in_files:
  type: array
  maxItems: 0
  description: Never present. @accepts_req names a StRS main path; mark a SwRS
    test with @tests_req <SwRS-ID>#S<n>.
```

That is exactly the declaration `schema_text("swrs")` writes, so a schema
regenerated by a fresh `okfreq init` already has it. `okfreq` applies no shipped
declaration and has no silent fallback. Outside the new mode nothing is checked.

### The acceptance waiver

A stakeholder requirement whose main paths genuinely cannot be walked by an
automated test may be waived as a whole, an interactive agent skill being the
typical case. The waiver is authored frontmatter, never generated, and applies to
the complete StRS, not to one scenario:

```yaml
acceptance_exemption: true
acceptance_exemption_reason: >-
  The consolidation is an interactive agent skill: no automated test can walk the
  operator dialogue. Reviewed coverage is an inspection report, see
  https://requirements.example.test/reviews/skill-audit.
```

A waiver is effective only when the flag is `true` and the reason is a non-blank
string; a whitespace-only reason is also refused. It suppresses `W004` and lets
the StRS reach `covered` without an `@accepts_req`, but it changes nothing else:

- it does not add an accepted path, change `accepted`, or touch any path count,
  so the report and the aggregate still show the actual numbers;
- it does not relax the linked-SwRS rule, the fragment errors, the scenario
  declarations, or `W003`;
- it does not create a marker and is not acceptance evidence.

The owner reviews the exemption under the project's approval rules, removes it
when it is no longer justified, and never uses it to hide an acceptance test that
can be written. `okfreq` does not collect or verify that approval. Being slow or
expensive alone is not a reason to waive: mark the expensive test `@accepts_req`
instead.

A SwRS's `annotation_exemption` and `exemption_reason` are a different field:
they exempt that SwRS from its source and test marker coverage. In the new mode a
linked SwRS with a non-blank reason satisfies its parent's linked-SwRS condition
and is reported as `exempt`, not `covered`. It never waives its parent's
acceptance condition, and an StRS waiver never exempts or fabricates evidence for
a SwRS.

### Evidence counters are unchanged

This is still linkage, not execution. `execution_evidence.status` stays
`not_collected` in every report, and no path count asserts that a test ran or
passed.

(okfreq-report-fields)=

## Report fields

The report's `format_version` is `2` in every mode. In the new mode each StRS's
`stakeholder_test_coverage` adds:

```json
"paths": {"total": 3, "tested": 2, "accepted": 1},
"tested": false,
"accepted": false,
"tests": {"status": "defined", "files": ["tests/test_flow.py"], "count": 1},
"acceptance_tests": {"status": "defined", "files": ["tests/test_acceptance.py"], "count": 1}
```

- `paths.tested` and `paths.accepted` count declared paths with at least one
  counting marker of that verb. `tested` and `accepted` are true when each count
  equals `total`. A StRS that declares no scenarios reports
  `{"total": 0, "tested": 0, "accepted": 0}` and sets the booleans from its
  fragmentless markers.
- `tests` lists the files of the counting `@tests_req` markers (its generated
  `tested_in_files`); `acceptance_tests` lists the files of the counting
  `@accepts_req` markers (its `accepted_in_files`). Both are shaped like
  `validation_tests`, with `status` `defined` or `missing`.
- `validation_tests` stays, required, for backward compatibility. In the new mode
  it holds the same files and status as `acceptance_tests`.
- The StRS record's own `tests` (outside `stakeholder_test_coverage`) follows
  `validation_tests`, as it always did. So in the new mode the record's `tests`
  holds the `@accepts_req` files, while `stakeholder_test_coverage.tests` holds the
  `@tests_req` files. Read the record's `tests` for the acceptance link and
  `stakeholder_test_coverage.tests` for the tested link.
- A justified waiver adds `"acceptance_exemption": {"reason": "<authored reason>"}`
  and is omitted otherwise. Waived StRS stay in the aggregate path denominator, and
  only actual accepted paths are counted.
- Each SwRS that declares transitions gains
  `"transitions": {"tested": ["S1"], "missing": ["S2"]}`. A linked SwRS with a
  justified annotation exemption has `linked_swrs[].status` `exempt`.
- The aggregate `stakeholder_test_coverage` gains `paths`, the sums over StRS.
- In the aggregate and `legacy.marker_coverage`, `validation_tests` maps each StRS
  to its `acceptance_tests` files, and `missing_tests` follows the transition rule.
  `marker_coverage.tested` is a **link count**: the number of leaf IDs with at
  least one counting `@tests_req`, not the number of test-covered SwRS. A SwRS that
  declares `S1` and `S2` and has a counting marker on `S1` only counts there and is
  listed in `missing_tests`. `totals.tested` is the test-covered count. The two are
  expected to differ, as they already did for individually exempted leaves.
- Each SwRS record's `tests.files`/`count` list only its counting `@tests_req`
  files. A rejected marker appears only in the errors.

`okfreq trace --json` keeps its own shape in every mode: its `validation_tests`
holds the raw `@tests_req` files on an StRS, unlike the new mode's report
`validation_tests`. It also gains `accepted` and `scenario_markers`, one entry per
(marker kind, ID, fragment, file) with `marker`, `id`, `fragment`, `file` and
`line`.

### Markdown columns

`write_markdown_report`, in the new mode only, adds:

- `- StRS paths: tested <t>/<n>, accepted <a>/<n>` to the summary;
- `Tested` and `Accepted` columns to the stakeholder table, `2/3` with ✅ when
  complete; `✅ no paths` or `❌ no paths` from the booleans for a StRS without
  paths; `exempt` in the `Accepted` cell of a waived StRS, never a claimed
  acceptance;
- a `Missing transitions` column to the software table, `S2, S3` or `—`.

In the old modes the Markdown is unchanged.
