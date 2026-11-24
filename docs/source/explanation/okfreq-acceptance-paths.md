# Why okfreq measures acceptance paths

A direct StRS marker is evidence of a link, not proof that a test walks a
stakeholder path. A test can photograph one state or repeat a single SwRS
transition without exercising the complete outcome.

`linked-swrs-and-acceptance-paths` therefore separates two questions:

- `@tests_req` says a test exercises a requirement or one declared scenario.
- `@accepts_req` says a test accepts one StRS main path.

Their tested and accepted counters are independent. One marker can accept a
path without supplying its cheaper path test, and one test can cover a path
without accepting it. Normal StRS coverage needs complete linked-SwRS coverage
and complete acceptance. A justified, whole-StRS acceptance waiver is the
exception; it is never counted as an accepted path.

(okfreq-execution-cost)=
## Choosing by execution cost

When the test closest to the final product is expensive, put `@accepts_req` on
that test and run it in the main-branch pipeline. Put `@tests_req` on a cheaper
test of the same path that runs on each pull or merge request. When tests are
cheap, put `@accepts_req` directly on them. This is a recommendation only:
okfreq does not check where or how a test runs.

`W004` reports a live, non-waived StRS with no counting acceptance marker. Cost
alone is not a reason for a waiver. Use `acceptance_exemption` only when the
complete StRS cannot be acceptance-tested, for example an interactive skill
whose outcome requires human review. The owner reviews the reason, it must be
removed when no longer justified, and linked SwRS still need their own source,
test, or justified annotation exemption.

## Why fragments are part of the marker

Declaring `scenarios:` means a fragmentless marker could claim every path at
once. In that case `#S<n>` is mandatory for both verbs and both tiers. Without
declared scenarios, a fragmentless marker is the only honest whole-requirement
link. The verb belongs in the marker because the test states what it is; a
separate setting could drift from the evidence.

okfreq collects linkage, not execution. Reports retain
`execution_evidence.status: not_collected`. See
[acceptance paths and scenario markers](../reference/okfreq-acceptance-paths.md)
for the exact marker and report contract.
