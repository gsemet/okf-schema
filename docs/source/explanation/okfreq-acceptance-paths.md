# Why `okfreq` measures acceptance paths

A requirements tool that counts any test marker on a stakeholder requirement
(StRS) as a "validation test" reports a number, not a proof. This page explains
what `okfreq` does instead when you select the mode
`strs_test_coverage_mode: linked-swrs-and-acceptance-paths`, and why. For the
exact rules, fields, messages and report shapes, see the
[acceptance paths reference](../reference/okfreq-acceptance-paths.md).

## A marker is a link, not a proof

Consider a stakeholder requirement such as "a user can export a report for
offline review". Its main paths might be: export every row, export a filtered
selection, export when the selection is empty. A direct marker
`@tests_req StRS-CORE-001` on a test file says only that some test in that file
relates to the requirement. The test may photograph one state of the output, or
repeat a software-level transition that a software requirement (SwRS) already
covers. It does not say that a stakeholder path was walked from start to its
observable outcome, and it says nothing about the other paths.

The mode measures a StRS by its **declared main paths** instead. Each path has
a stable short id (`S1`, `S2`, ...) and a title, written in the StRS
frontmatter. A test names the path it walks with a fragment, as in
`@tests_req StRS-CORE-001#S2`. `okfreq` can then report which fraction of the
paths has a test, rather than whether any test exists.

## Two verbs, two independent counters

Two test markers exist, and the verb says what the test is:

- `@tests_req` marks a test of a requirement or of one of its scenarios: a
  SwRS transition, or a StRS main path. These feed the "tested" counter.
- `@accepts_req` marks the **acceptance test** of a StRS main path: the test
  that checks the stakeholder-visible outcome of that path on the product as
  close as possible to what the stakeholder gets. These feed the "accepted"
  counter. It applies to a StRS only; a SwRS has no acceptance marker.

The two counters are independent. A path with only an `@accepts_req` marker is
accepted and not tested; a path with only a `@tests_req` marker is tested and
not accepted. A StRS is "tested" when every declared path has a `@tests_req`
marker, and "accepted" when every declared path has an `@accepts_req` marker.

Normally a StRS is **covered** when its linked SwRS are all covered (or
individually exempted with a reason) **and** it is accepted. "Tested" is
reported beside it and does not change the status: tested says that tests of
each path exist, accepted says that the paths have been accepted. When a StRS
declares no paths, one fragmentless `@accepts_req StRS-ID` marker is the
acceptance condition, the only honest link in that case.

The only other way to be covered is the explicit, justified
acceptance waiver ({ref}`okfreq-acceptance-waiver`) described below. A waiver is a
policy decision, not acceptance evidence.

## Why a fragment

A marker must say which path it walks, otherwise `okfreq` cannot compute a
fraction. `@tests_req StRS-CORE-001#S2` is a test of path `S2`; it does not
claim the other paths.

For the same reason, **declaring `scenarios:` makes the fragment mandatory**,
for both verbs and for both tiers. Once paths exist, a fragmentless marker would
claim every path at once, which is exactly the vague link this mode removes. An
unknown fragment is an error too. A requirement that declares no `scenarios:`
keeps working with fragmentless markers: they count for the requirement as a
whole, because there is nothing finer to name. `okfreq` then warns (`W003`) that
a live StRS should declare its paths, and tells an agent how.

The same shared field applies to a SwRS: its `scenarios:` are its transition
scenarios, and it is test-covered only when each declared transition has a
`@tests_req SwRS-ID#S<n>` marker.

## Why the verb is in the marker

The marker, not a setting, says what a test is. No configuration maps a
directory or a pipeline to "acceptance", so no configuration can drift from the
tests it describes: reading the test shows what it claims to be. Which
pipeline runs the test is the project's decision and `okfreq` does not look at
it.

(okfreq-execution-cost)=

## Choosing by execution cost

`okfreq` does not check where or how a test runs. It does recommend a
convention, which this page explains. The recommendation is not an obligation.

The tests closest to the final product, which drive the built and installed
product the way a stakeholder does, are often the costly ones: they may need a
build, an installed environment, a device, a long run or shared resources. The
cheaper tests of the same path run in-process, against fixtures, in seconds.

- **When the test closest to the final product is costly**, mark it
  `@accepts_req StRS-ID#S<n>` and run it where cost is acceptable, for example in
  the pipeline of the main branch. Mark a cheaper test of the same path
  `@tests_req StRS-ID#S<n>` and run it on every pull or merge request, so a
  regression in the path is caught early without paying for the acceptance run
  each time.
- **When the tests are cheap**, put `@accepts_req` directly on them. A second,
  cheaper test is then unnecessary, and the path is both accepted and, if you
  also mark it `@tests_req`, tested.

Both patterns give the same report: the path is accepted by the first, tested by
the second. The report cannot tell which pipeline ran a test, and it does not
need to; that is why the choice is yours.

`W004` is the one place where `okfreq` pushes on this. It warns when a live
StRS, with no justified waiver, has **no acceptance test at all**: no
`@accepts_req` marker that counts names it. Its message links to this section.
A StRS accepted on `1/3` paths gets no `W004`; the missing paths show in the
counters and the report instead.

(okfreq-acceptance-waiver)=

## When an owner may waive acceptance

Some stakeholder requirements cannot be acceptance-tested by a program. An
interactive consolidation, where a person reviews proposals and decides, is an
example: no deterministic command walks the path. Declaring a fake marker on an
unrelated test would fabricate evidence, so `okfreq` lets the owner waive
acceptance for the **whole StRS** with an authored, justified exemption:

```yaml
acceptance_exemption: true
acceptance_exemption_reason: >-
  The path is an interactive review by a person; no deterministic command
  can accept it. Reviewed in the monthly maintainer session.
```

Use it only when:

- the requirement genuinely cannot be accepted by an automated test, and the
  reason says why;
- the owner has reviewed the waiver under the project's approval rules.
  `okfreq` does not collect or verify that approval.

Do not use it because a test is slow or expensive: cost is a reason to choose
`@accepts_req` for the costly test and `@tests_req` for a cheaper one, see
above. Do not use it to hide an acceptance test that could be written. Remove
the waiver as soon as it is no longer justified.

A waiver changes a single policy decision: a StRS whose linked SwRS are covered
is `covered` without acceptance. It does not create a marker, change `accepted`
or any path count, relax fragment errors or the linked-SwRS rule, and it does
not silence `W003`. It does stop `W004`, since the absence of an acceptance
test is then deliberate. The report shows the reason and the Markdown shows
`exempt` in the StRS's accepted column; the actual counts stay honest.

A StRS waiver is not a SwRS exemption. A SwRS's own `annotation_exemption` with
its reason exempts that requirement from its source and test coverage and makes
it satisfy its parent's linked-SwRS condition (reported as `exempt`, not
`covered`); the parent's acceptance condition remains. The two exemptions are
independent: neither waives the other, and neither fabricates evidence.

## This is linkage, not execution

All of this remains **linkage**. `okfreq` scans source files for markers. It does
not read test-runner results, so it cannot say that an acceptance test ran or
passed. The report's `execution_evidence` stays `not_collected`. An "accepted"
path means that an acceptance test is defined and linked to it. Read
[What `okfreq` coverage really means](okfreq-coverage-boundaries.md) for what
linkage can and cannot conclude.

## Choosing a mode

| If you want... | Use mode |
|---|---|
| A StRS covered once its linked SwRS are tested | `linked-swrs` (default) |
| The same, plus one direct validation-test marker on the StRS | `linked-swrs-and-validation-test` |
| Declared main paths, a tested and an accepted counter, and acceptance as the condition | `linked-swrs-and-acceptance-paths` |

The old modes accept `scenarios:`, `@accepts_req` and `#S<n>` suffixes, and
require and count nothing new, so a project can adopt the vocabulary before it
switches mode. The [reference](../reference/okfreq-acceptance-paths.md) holds the
full comparison, the combination table, worked examples and every message.
