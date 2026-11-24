# Why okfreq measures acceptance paths

A stakeholder requirement (StRS) states an outcome a person cares about. The
question a project wants answered is not "does some test mention this StRS?" but
"is every way a person reaches this outcome walked by a test?". The
`strs_test_coverage_mode` value `linked-swrs-and-acceptance-paths` lets okfreq
measure that. This page explains its choices; the exact rules, the combination
table and worked examples are in the
[acceptance paths reference](../reference/okfreq-acceptance-paths.md).

## A marker is a link, not a proof

In the mode `linked-swrs-and-validation-test`, any `@tests_req StRS-X` marker makes
the StRS "validated". A marker only says that a test is related to the
requirement. A test that checks one intermediate state, or that repeats what one
SwRS transition already checks, carries the marker as well as a test that walks a
stakeholder path from the first step to the observable outcome. Counting both the
same way gives a high figure that says little.

The new mode asks each StRS to declare its **main paths**, the few distinct ways a
stakeholder reaches the outcome, in the frontmatter field `scenarios:` (see
{ref}`okfreq-declared-scenarios`). A SwRS declares its transition scenarios in the
same field. A test marker then names the path or the transition it walks, and
okfreq can count what fraction of the declared paths is walked.

## Two verbs, two counters

A test of a StRS path is not always the test that proves the path to a
stakeholder. okfreq separates them by the marker's verb:

- `@tests_req <ID>#S<n>`: a test of a requirement, or of one of its scenarios: a
  SwRS transition or a StRS main path;
- `@accepts_req <StRS-ID>#S<n>`: the acceptance test of a StRS main path, the test
  that shows the path works as the stakeholder gets it.

Each StRS gets two independent counters, **tested** (paths with a `@tests_req`)
and **accepted** (paths with an `@accepts_req`). A path marked only with
`@accepts_req` is accepted and not tested; a path marked only with `@tests_req` is
tested and not accepted. Neither verb implies the other, so the report shows
exactly what exists.

A StRS is **covered** when its linked SwRS are test-covered, as in the other modes,
and every one of its paths is **accepted**. "Tested" is reported beside it and does
not change the status: a stakeholder outcome is reached when it is accepted, and
the cheaper tests that also walk it help find a regression sooner, but do not
replace the acceptance.

(okfreq-execution-cost)=

## Choosing by execution cost

Which test gets which verb is the project's choice. okfreq recommends one rule,
based on what a test costs to run:

- **When the test closest to the final product is expensive** (it builds and
  installs the product, starts a service, drives a user interface, needs a target
  or takes minutes), mark it `@accepts_req StRS-X#S<n>` and run it in the
  main-branch pipeline. Mark a cheaper test of the same path, one that runs
  in-process or against a stub, `@tests_req StRS-X#S<n>` and run it on every pull
  or merge request. Each pull or merge request gets fast feedback on the path, and
  the main branch proves it end to end.
- **When the tests are cheap**, put `@accepts_req` directly on the tests that walk
  each path, and run them everywhere. There is no reason to keep a second, lesser
  test of the same path.

This is a recommendation, not an obligation. okfreq does not know where, when or
how a test runs: it reads markers in the scopes' `test_dirs`, and nothing else.
`W004` says only that a live StRS has no acceptance test at all; it does not check
which pipeline runs it.

## Why a fragment

A fraction needs a numerator. A marker that says "this test is about StRS-X"
cannot say which path it walks, so okfreq could not compute "2 of 3 paths". The
fragment `#S<n>` glued to the ID, as in `@accepts_req StRS-X#S2`, names the path.
Ids are short and stable (`S1`, `S2`…) and never reused, even after a path is
removed, so a marker never silently changes meaning.

## Why declared scenarios make fragments mandatory

Once a requirement declares `scenarios:`, a marker without fragment would claim
every path at once: it would be the same "link, not proof" that the mode exists to
replace. So the rule is the same for both verbs and both tiers: when the target
declares `scenarios:`, a marker must name one of them, and a marker without it is an
error that counts toward nothing. When the target declares no `scenarios:`, a
fragmentless marker is the only honest link and counts for the whole requirement;
`W003` then asks for the paths and proposes the block to paste, built from the
body's `### Main paths` headings.

## Why the verb is in the marker

The test itself states what it is. A setting that listed which test files are
acceptance tests would drift as files move and tests are added; a marker moves with
its test and is reviewed with it. For the same reason okfreq has no notion of test
environments in its configuration.

## Still linkage, not execution

Counting walked paths is still counting markers. okfreq does not run tests or read
their results: the report's `execution_evidence` stays `not_collected`, and
"accepted 3/3" means that three acceptance tests are declared, not that they
passed. See [What okfreq coverage really means](okfreq-coverage-boundaries.md).

## Choosing a mode

- `linked-swrs` (the default) suits a project that wants to know whether each
  stakeholder outcome is decomposed into test-linked software behavior.
- `linked-swrs-and-validation-test` adds one direct test per StRS, without saying
  which path it walks.
- `linked-swrs-and-acceptance-paths` suits a project that wants to know, per StRS,
  which main paths have an acceptance test, and which have a cheaper test.

The [mode comparison](../reference/okfreq-acceptance-paths.md) lists what each
mode requires and does with each marker. A project switches by setting
`strs_test_coverage_mode` in `config.yml`; `okfreq validate` then lists, through
`W003`, `W004` and its errors, everything left to declare or mark. A bundle created
before okf-schema 0.18.0 first adds one declaration to its SwRS schema; the
reference page gives it.
