# Acceptance paths and scenario markers

This reference specifies `strs_test_coverage_mode: linked-swrs-and-acceptance-paths`,
declared `scenarios:`, `#S<n>` marker fragments, `@accepts_req`, whole-StRS
acceptance waivers, validation findings, and `format_version: 2` reports.
See [Why `okfreq` measures acceptance paths](../explanation/okfreq-acceptance-paths.md)
for the rationale.

## Marker verbs

| Marker (default) | Config key | Allowed targets | Role and recommended use |
|---|---|---|---|
| `@implements_req` | `markers.implements` | Leaf `SwRS` (ID only; no `#S<n>` fragment) | Implementation evidence in configured `source_dirs`. |
| `@tests_req` | `markers.tests` | `SwRS` transition (`#S<n>` when `scenarios:` is declared) or `StRS` main path | Test evidence in configured `test_dirs`. On a `StRS` in `linked-swrs-and-acceptance-paths` mode, feeds the `tested` counter; recommended for cheaper tests run on every pull or merge request. |
| `@accepts_req` | `markers.accepts` | `StRS` main path only (never `SwRS`) | Acceptance-test evidence in configured `test_dirs`. Feeds the `accepted` counter; recommended for the test closest to the final product (possibly costly and run on the main-branch pipeline, or placed directly on cheap tests). |

The cost split between `@tests_req` and `@accepts_req` is a recommendation, not
a rule checked by `okfreq`: `okfreq` checks marker syntax and linkage, not
where or how tests execute.

All three configured marker keywords (`markers.implements`, `markers.tests`,
`markers.accepts`) must be distinct; duplicate keywords fail `load_config` with
an error in every mode.

## Fragment syntax

A `@tests_req` or `@accepts_req` marker has the form:

```text
<keyword> <ID>[#S<n>]
```

- `<ID>` matches `markers.id_pattern` (default `[A-Za-z][A-Za-z0-9_-]*`, which
  excludes `#`).
- Optional `#S<n>` follows immediately with no whitespace, matching
  `#S[0-9]+` at a non-identifier boundary. Valid declared IDs match
  `^S[1-9][0-9]*$` (`S1`, `S2`, …, `S12`), so `#S0` and `#S01` are captured as
  fragments and fail in `linked-swrs-and-acceptance-paths` mode as unknown
  fragments.
- Any other suffix (`#path1`, `#s1`, `#S1a`, `#`) is **not** a scenario
  fragment: the scanner ignores it and reads the bare `<ID>` as fragmentless.
- `@implements_req` uses `<ID>` only and never parses fragments.

## Mode comparison

| Mode | SwRS test-covered when | StRS covered when | `@tests_req StRS-ID` | `@accepts_req StRS-ID` |
|---|---|---|---|---|
| `linked-swrs` (default) | At least one `@tests_req SwRS-ID` | ≥ 1 linked SwRS and every linked SwRS is test-covered | Scanned (`trace.validation_tests`), not required | Scanned (`trace.accepted`), counts nothing |
| `linked-swrs-and-validation-test` | At least one `@tests_req SwRS-ID` | `linked-swrs` + ≥ 1 `@tests_req StRS-ID` | Required for StRS coverage | Scanned (`trace.accepted`), counts nothing |
| `linked-swrs-and-acceptance-paths` | Every declared `S<n>` has `@tests_req SwRS-ID#S<n>` (or ≥ 1 fragmentless `@tests_req SwRS-ID` if no `scenarios:`) | ≥ 1 linked SwRS, each test-covered or individually `exempt`, **and** (`accepted` is true or justified whole-StRS waiver) | Feeds StRS `tested` counter and `tested_in_files` | Feeds StRS `accepted` counter, `accepted_in_files`, and StRS coverage policy |

## Marker combination matrix

The table below states the exact outcome for every combination of marker, tier,
declared `scenarios:`, fragment, and mode.

| Marker | Tier | `scenarios:` declared? | Fragment | Old modes (`linked-swrs`, `linked-swrs-and-validation-test`) | New mode (`linked-swrs-and-acceptance-paths`) |
|---|---|---|---|---|---|
| `@implements_req` | `SwRS` | Either | None | Counts as implementation | Counts as implementation |
| `@implements_req` | `StRS` | Either | None | Non-leaf warning (`non_leaf`) | Non-leaf warning (`non_leaf`) |
| `@tests_req` | `SwRS` | No | None | Counts as SwRS test | Counts as SwRS test |
| `@tests_req` | `SwRS` | No | `#S<n>` | Ignored fragment; counts on `<ID>` | **Error** (unknown fragment; declares no `scenarios:`); does not count |
| `@tests_req` | `SwRS` | No | Other `#…` | Fragmentless on `<ID>`; counts | Fragmentless on `<ID>`; counts |
| `@tests_req` | `SwRS` | Yes | None | Counts on `<ID>` | **Error** (fragment missing); does not count |
| `@tests_req` | `SwRS` | Yes | Declared `#S<n>` | Counts on `<ID>` | Counts toward transition `S<n>` and `tested_in_files` |
| `@tests_req` | `SwRS` | Yes | Undeclared `#S<n>` | Counts on `<ID>` | **Error** (unknown fragment); does not count |
| `@tests_req` | `StRS` | No | None | Validation test (`linked-swrs-and-validation-test`) / recorded | Counts as StRS `tested` (`tested: true`) and `tested_in_files` |
| `@tests_req` | `StRS` | No | `#S<n>` | Recorded on `<ID>` | **Error** (unknown fragment; declares no `scenarios:`); does not count |
| `@tests_req` | `StRS` | Yes | None | Recorded on `<ID>` | **Error** (fragment missing); does not count |
| `@tests_req` | `StRS` | Yes | Declared `#S<n>` | Recorded on `<ID>` | Counts toward StRS `paths.tested` and `tested_in_files` |
| `@tests_req` | `StRS` | Yes | Undeclared `#S<n>` | Recorded on `<ID>` | **Error** (unknown fragment); does not count |
| `@accepts_req` | `SwRS` | Either | Any | Scanned in `trace.accepted`; counts nothing | **Error** (schema refuses `accepted_in_files` on SwRS); does not count |
| `@accepts_req` | `StRS` | No | None | Scanned in `trace.accepted`; counts nothing | Counts as StRS `accepted` (`accepted: true`) and `accepted_in_files` |
| `@accepts_req` | `StRS` | No | `#S<n>` | Scanned in `trace.accepted`; counts nothing | **Error** (unknown fragment; declares no `scenarios:`); does not count |
| `@accepts_req` | `StRS` | Yes | None | Scanned in `trace.accepted`; counts nothing | **Error** (fragment missing); does not count |
| `@accepts_req` | `StRS` | Yes | Declared `#S<n>` | Scanned in `trace.accepted`; counts nothing | Counts toward StRS `paths.accepted` and `accepted_in_files` |
| `@accepts_req` | `StRS` | Yes | Undeclared `#S<n>` | Scanned in `trace.accepted`; counts nothing | **Error** (unknown fragment); does not count |
| Any | Unknown ID | — | Any | Recorded in `missing_ids` | Recorded in `missing_ids` |

`okfreq retire` refuses to delete a draft requirement if any `@implements_req`,
`@tests_req`, or `@accepts_req` marker still references its ID, in every mode.

## Worked examples

### Example 1: StRS with three paths, independent tested and accepted counters

In this example, `StRS-DEMO-001` declares three main paths (`S1`, `S2`, `S3`).
Fast tests cover `S1` and `S2` (`@tests_req`), while an acceptance test covers
`S3` (`@accepts_req`). Path `S3` is accepted without being marked `@tests_req`:
the two counters are independent (`tested: 2/3`, `accepted: 1/3`), and the StRS
is not yet `covered` because `accepted` is `false`.

```{code-block} yaml
:caption: Example 1 StRS frontmatter

id: StRS-DEMO-001
type: StRS
title: Export reports
req_lifecycle: proposed
scenarios:
  - id: S1
    title: Export CSV report
  - id: S2
    title: Export JSON report
  - id: S3
    title: Reject invalid format
```

```{code-block} python
:caption: Example 1 test markers

# tests/test_export_fast.py
# @tests_req StRS-DEMO-001#S1
# @tests_req StRS-DEMO-001#S2

# tests/test_export_acceptance.py
# @accepts_req StRS-DEMO-001#S3
```

```{code-block} json
:caption: Example 1 JSON excerpt

{
  "status": "missing",
  "mode": "linked-swrs-and-acceptance-paths",
  "paths": {"total": 3, "tested": 2, "accepted": 1},
  "tested": false,
  "accepted": false,
  "tests": {"status": "defined", "files": ["tests/test_export_fast.py"], "count": 1},
  "acceptance_tests": {"status": "defined", "files": ["tests/test_export_acceptance.py"], "count": 1},
  "validation_tests": {"status": "defined", "files": ["tests/test_export_acceptance.py"], "count": 1}
}
```

```{code-block} markdown
:caption: Example 1 Markdown row

| demo | StRS | StRS-DEMO-001 | Export reports | 2/3 | 1/3 | ❌ missing |
```

### Example 2: SwRS with declared transitions where one transition is missing

`SwRS-DEMO-001` declares transitions `S1` and `S2`, and only `S1` has a
`@tests_req` marker. `SwRS-DEMO-001` is therefore not test-covered (`missing`),
its `transitions.missing` lists `S2`, and its parent StRS is not covered.

```{code-block} yaml
:caption: Example 2 SwRS frontmatter

id: SwRS-DEMO-001
type: SwRS
title: Format CSV output
derives_from:
  - StRS-DEMO-001
req_lifecycle: proposed
scenarios:
  - id: S1
    title: Valid rows serialize to CSV
  - id: S2
    title: Empty input fails with usage error
```

```{code-block} python
:caption: Example 2 test markers

# tests/test_export_fast.py
# @tests_req SwRS-DEMO-001#S1
```

```{code-block} json
:caption: Example 2 JSON excerpt

{
  "tests": {"status": "missing", "files": ["tests/test_export_fast.py"], "count": 1},
  "transitions": {"tested": ["S1"], "missing": ["S2"]}
}
```

```{code-block} markdown
:caption: Example 2 Markdown row

| demo | SwRS | SwRS-DEMO-001 | Format CSV output | ✅ covered | ❌ missing | S2 |
```

### Example 3: StRS without `scenarios:` declared

`StRS-DEMO-002` has a `### Main paths` heading in its body but has not yet
declared `scenarios:` in frontmatter. A fragmentless `@tests_req StRS-DEMO-002`
counts (`tested: true`), no `@accepts_req` is present (`accepted: false`), and
`okfreq validate` emits both `W003` (with the `scenarios:` block to paste) and
`W004` (no acceptance test).

```{code-block} markdown
:caption: Example 3 StRS document

---
id: StRS-DEMO-002
type: StRS
title: Inspect report summary
req_lifecycle: proposed
---

## Inspect report summary

### Main paths

#### Path 1: Print summary counts
```

```{code-block} python
:caption: Example 3 test markers

# tests/test_summary.py
# @tests_req StRS-DEMO-002
```

```{code-block} json
:caption: Example 3 JSON excerpt

{
  "status": "missing",
  "mode": "linked-swrs-and-acceptance-paths",
  "paths": {"total": 0, "tested": 0, "accepted": 0},
  "tested": true,
  "accepted": false,
  "tests": {"status": "defined", "files": ["tests/test_summary.py"], "count": 1},
  "acceptance_tests": {"status": "missing", "files": [], "count": 0},
  "validation_tests": {"status": "missing", "files": [], "count": 0}
}
```

```{code-block} markdown
:caption: Example 3 Markdown row

| demo | StRS | StRS-DEMO-002 | Inspect report summary | ✅ no paths | ❌ no paths | ❌ missing |
```

## Whole-StRS acceptance waivers and SwRS annotation exemptions

A whole-StRS acceptance waiver is authored in StRS frontmatter:

```yaml
acceptance_exemption: true
acceptance_exemption_reason: >
  Interactive human-guided workflow; automated end-to-end acceptance is not
  feasible, and each automated behavior is verified by linked SwRS tests.
```

- **Owner review:** changing or adding a waiver on an `approved` StRS is a
  meaning change and requires the owner's agreement (`approved_by` /
  `approved_at` and PR review).
- **When to remove:** remove `acceptance_exemption` and
  `acceptance_exemption_reason` as soon as automated acceptance tests exist,
  and add `@accepts_req` markers for each declared path.
- **Whole-StRS scope:** the waiver applies to the whole StRS, not individual
  paths. It satisfies the StRS acceptance condition (`status: "covered"` when
  all linked SwRS are covered or exempt), suppresses `W004` (never `W003` or
  marker errors), adds `acceptance_exemption: {"reason": "..."}` to
  `stakeholder_test_coverage`, and renders `exempt` in the Markdown `Accepted`
  column.
- **Honest evidence counters:** `accepted`, `paths.accepted`,
  `acceptance_tests`, and `validation_tests` still reflect actual counting
  `@accepts_req` markers only. A waived StRS's declared paths remain in the
  aggregate `stakeholder_test_coverage.paths.total` denominator.
- **Distinct from SwRS `annotation_exemption`:** on a leaf `SwRS`,
  `annotation_exemption: true` with a non-blank `exemption_reason` exempts that
  SwRS from source and test marker coverage. In
  `linked-swrs-and-acceptance-paths` mode, that SwRS appears in its parent
  StRS's `linked_swrs` with `status: "exempt"` and satisfies the parent's
  linked-SwRS condition, without waiving the parent StRS's own acceptance.

## Validation findings and fixes

In `linked-swrs-and-acceptance-paths` mode, `okfreq validate` scans markers and
reports the following errors (failing validation) and advisory warnings
(`W003`, `W004`, printed with or without `--prose`, never changing exit code):

| Finding | Cause | Fix |
|---|---|---|
| `<file>:<line>: @tests_req <ID> has no scenario fragment; <ID> declares scenarios S1, S2: write @tests_req <ID>#S<n> (this marker does not count)` | Requirement declares `scenarios:` but marker omits `#S<n>`. | Append `#S<n>` naming the scenario the test exercises. |
| `<file>:<line>: @accepts_req <ID>#S4 names no declared scenario of <ID> (declared: S1, S2)` (or `(<ID> declares no scenarios:)`) | Marker fragment does not match any declared `scenarios:` entry. | Fix `#S<n>` to a declared ID, or remove `#S<n>` if the requirement declares no `scenarios:`. |
| `<file>:<line>: @accepts_req <SwRS-ID>: Never present. @accepts_req names a StRS main path; mark a SwRS test with @tests_req <SwRS-ID>#S<n>.` | `@accepts_req` targets a `SwRS`. | Replace `@accepts_req` with `@tests_req <SwRS-ID>#S<n>` (or `@tests_req <SwRS-ID>`). |
| `<swrs.schema.yaml>: accepted_in_files is not refused; mode linked-swrs-and-acceptance-paths needs the okf-schema 0.18.0 declaration: ...` | Bundle `swrs.schema.yaml` predates 0.18.0 and does not refuse `accepted_in_files`. | Add the `accepted_in_files` (`maxItems: 0`) property shown in the message to `tiers/_schema/swrs.schema.yaml`. |
| `acceptance_exemption_reason` blank or missing when `acceptance_exemption: true` | Waiver set without a non-blank reason. | Provide a non-blank `acceptance_exemption_reason`, or remove `acceptance_exemption`. |
| Malformed `scenarios:` (not a list, invalid ID, duplicate ID, blank title, extra keys) | Invalid `scenarios:` frontmatter. | Use a list of `{id: S<n>, title: <non-blank string>}` entries with unique `S1`, `S2`, … IDs. |
| `W003 <file>: ...` | Live (`draft`, `proposed`, `approved`) StRS declares no `scenarios:`. | Paste the suggested `scenarios:` block into frontmatter only (log in `tiers/log.md` on an approved StRS), then add `#S<n>` to its markers. |
| `W004 <file>: <StRS-ID> has no acceptance test: ...` | Live, non-waived StRS has no counting `@accepts_req` marker. | Mark the acceptance test for each main path with `@accepts_req <StRS-ID>#S<n>`, or record a justified whole-StRS waiver if acceptance testing is genuinely infeasible. |

## Report fields (`format_version: 2`)

Every `okfreq generate-report` JSON output uses `"format_version": 2`.

In `linked-swrs-and-acceptance-paths` mode:

- **Aggregate `stakeholder_test_coverage.paths`**: `{total, tested, accepted}`
  summed across all StRS requirements.
- **Per-StRS `stakeholder_test_coverage`**: adds `paths` (`{total, tested,
  accepted}`), `tested` (boolean), `accepted` (boolean), `tests` (files of
  counting `@tests_req` markers on the StRS), `acceptance_tests` (files of
  counting `@accepts_req` markers), and optional `acceptance_exemption`
  (`{"reason": "..."}`). `validation_tests` remains required and mirrors
  `acceptance_tests` in this mode.
- **Per-StRS `tests` vs. `stakeholder_test_coverage.tests`**: the StRS record's
  top-level `tests` follows `validation_tests` (so in the new mode it holds the
  `@accepts_req` files), whereas `stakeholder_test_coverage.tests` holds the
  `@tests_req` files.
- **`trace --json` `validation_tests` vs. report `validation_tests`**:
  `okfreq trace --json` keeps raw `@tests_req` files targeting a StRS in
  `validation_tests` across every mode, while `okfreq generate-report` in
  `linked-swrs-and-acceptance-paths` mode populates `validation_tests` (both
  aggregate and per-StRS) with the counting `@accepts_req` files.
- **Per-SwRS `transitions`**: present when the SwRS declares `scenarios:`, with
  `{"tested": [...], "missing": [...]}` in declared order.
- **`marker_coverage.tested` vs. `totals.tested`**: `marker_coverage.tested` is
  a **link count** (leaf requirement IDs with at least one counting `@tests_req`
  file). `totals.tested` is the **test-covered count** (non-exempt leaf
  requirements whose every declared transition is tested, or with at least one
  `@tests_req` when none is declared). A SwRS declaring `S1` and `S2` with only
  `S1` marked counts in `marker_coverage.tested` and appears in `missing_tests`,
  while not counting in `totals.tested`.
