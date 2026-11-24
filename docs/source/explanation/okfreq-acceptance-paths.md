# Why `okfreq` measures acceptance paths

`okfreq` links requirements to the files that implement them and to the tests
that exercise them. For a leaf `SwRS` that link is enough to say the requirement
is covered. For a stakeholder requirement (`StRS`) it is not, and this page
explains why, and what `okfreq` measures instead.

## A direct StRS marker is a link, not a proof

An `StRS` states an outcome a stakeholder committed to. It is delivered by
several `SwRS` requirements, each of which a test can exercise on its own. A test
that carries `@tests_req StRS-CORE-001` says only that the test mentions the
stakeholder requirement. It may photograph one state of the product, seed one
record, or repeat one `SwRS` transition. None of that walks a stakeholder path
from the user's request to the user's outcome.

Because the marker proves nothing on its own, the mode
`linked-swrs-and-validation-test` made it a third condition stacked on top of the
`SwRS` coverage of the `linked-swrs` rule: an `StRS` needed its `SwRS` children
covered *and* such a marker. That is linkage, twice. It does not say the product,
as installed, delivers the outcome.

## The two verbs and the two counters

The acceptance-paths mode separates two claims that the old single marker
conflated, and gives each its own verb:

- `@tests_req` marks *a test of a requirement or of one of its scenarios*: a unit
  or integration test of a `SwRS` transition, or a cheap test of one `StRS` main
  path.
- `@accepts_req` marks *the acceptance test of an `StRS` main path*: the test
  closest to the final product that walks the path the way its stakeholder would.

They feed two independent counters:

- **tested** counts the declared paths (or `SwRS` transitions) covered by an
  `@tests_req` marker.
- **accepted** counts the declared paths covered by an `@accepts_req` marker.

Keeping them apart is what lets a project see a path that is accepted and not
tested, or tested and not accepted, instead of one blended number that hides
both. [Worked example 1](../reference/okfreq-acceptance-paths.md) shows a
requirement at `2/3` tested and `1/3` accepted.

Coverage normally requires **accepted**: an `StRS` is covered when every declared
main path is accepted, and when it declares no `scenarios:` at all, when at least
one fragmentless `@accepts_req` marker names it. The one exception is the
explicit, justified waiver described below, which is a decision an owner records,
not a way to silence a warning.

(okfreq-execution-cost)=

## Choosing by execution cost

Which verb goes on which test is a cost decision, and it is a recommendation, not
an obligation: `okfreq` never checks where or how a test runs.

- When the test closest to the final product is expensive (it boots the installed
  package, drives a browser, exports from a real document), put `@accepts_req` on
  it and run it in the main-branch pipeline, and put `@tests_req` on a cheaper
  test of the same path and run that one in the pull or merge request pipeline.
  Both counters then move: the path is tested early and accepted before release.
- When tests are cheap, put `@accepts_req` directly on them. A fast acceptance
  test needs no cheaper twin, and one marker is easier to keep true than two.

The one thing `okfreq` does check is the absence of acceptance: `W004` fires when
a non-waived `StRS` has no acceptance test at all. It says nothing about how
often that test runs.

## Waiving acceptance for a whole StRS

Some stakeholder requirements cannot be acceptance-tested by a program. An
interactive skill is the usual example: its outcome is a conversation whose
quality a test cannot judge, and asserting on its transcript would test the
transcript, not the outcome.

Such a requirement may carry a waiver in its frontmatter:

```yaml
acceptance_exemption: true
acceptance_exemption_reason: The skill is judged by its owner in a review session,
  not by an automated acceptance test.
```

The waiver is scoped to the whole `StRS`. It does not waive any individual path,
it does not change what the accepted counter counts, and it never replaces the
`SwRS` coverage the requirement still needs. It suppresses `W004` and it does not
suppress `W003`: a requirement that still declares no `scenarios:` keeps warning
about it.

Cost alone is never a sufficient reason. "The test is slow" is answered by the
execution-cost split above, which keeps the acceptance claim and moves the work
to a cheaper pipeline. A waiver is for an outcome no automated test can walk. The
owner reviews it like any other approved change, the reason names the
circumstance, and the waiver is removed as soon as the requirement becomes
testable again; a stale waiver is a claim nobody checked.

## Why a fragment

A marker must say *which* path it walks, so a fraction can be computed. Without
that, one marker would either claim every path at once or claim none, and neither
is a measurement. The fragment is the `#S<n>` suffix in
`@tests_req SwRS-CORE-001#S2` or `@accepts_req StRS-CORE-001#S1`; `<n>` is the id
of a declared scenario, declared in the requirement's `scenarios:` frontmatter.

## Why declaring `scenarios:` makes fragments mandatory

Once paths exist, a fragmentless marker becomes a false claim: it would mean "this
test walks every path". So the moment a requirement declares `scenarios:`, every
test marker on it must name one path, for both verbs and both tiers. Without the
declaration, the fragmentless marker is the only honest link there is, and it
counts.

That asymmetry is deliberate. A project can start with the old modes and no
declarations, then declare paths one requirement at a time; each declaration
raises the bar for that requirement only, and the error message names the
scenarios it now requires.

## Why the verb is in the marker rather than in a setting

The test itself states what it is. A setting such as "tests under `tests/e2e` are
acceptance tests" drifts: the folder fills with other things, a test moves, a
configuration copy goes stale, and the report keeps claiming something no file
says. A marker in the file cannot drift from the file. It is also the only place
where the author — who knows what the test really does — can make the claim.

## Still linkage, never execution

This is still linkage, not execution. `okfreq` reads markers; it does not run
tests, and it does not collect results. The report keeps
`execution_evidence: not_collected`, which is why
[the coverage boundaries](okfreq-coverage-boundaries.md) matter: a covered
requirement means the markers line up, not that a green suite ran. Proving
execution needs a runner integration that writes results back, which is a
different project.

## Choosing a mode

The mode is chosen once per bundle with `strs_test_coverage_mode`:

| Mode | Use it when |
|---|---|
| `linked-swrs` | `SwRS` coverage is the only claim the project wants. |
| `linked-swrs-and-validation-test` | The project wants one direct `StRS` marker as a third condition, and no path accounting. |
| `linked-swrs-and-acceptance-paths` | The project wants to know which stakeholder paths are tested and which are accepted. This is the recommended mode once requirements declare `scenarios:`. |

The modes compare in full in
[Acceptance paths and scenario markers](../reference/okfreq-acceptance-paths.md),
which also holds the marker behaviour table, the fragment syntax, the worked
examples and the findings.
