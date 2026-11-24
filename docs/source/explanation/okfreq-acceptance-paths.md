# Why okfreq measures acceptance paths

A direct link to a stakeholder requirement does not prove that the test walks
the stakeholder's path. A test may inspect one state or repeat one software
transition without reaching the user's outcome.

The `linked-swrs-and-acceptance-paths` mode lets requirements declare their
main paths or software transitions in `scenarios:`. A `@tests_req` marker
names a test of a requirement or scenario. An `@accepts_req` marker names an
acceptance test of a stakeholder path. The tested and accepted fractions are
independent: acceptance does not imply a test marker and vice versa. A
stakeholder requirement is covered only when its linked software requirements
are test-covered and all its paths are accepted, unless an explicitly justified
requirement-wide acceptance exemption applies. An exemption is reported as such,
not as an acceptance test.

(okfreq-waiver-rationale)=
## When an acceptance waiver is appropriate

An acceptance waiver is a recorded decision that an **entire StRS** cannot be
acceptance-tested using the project's practical verification process. It is not
a marker and does not establish that the stakeholder outcome works. For
example, an interactive agent workflow that proposes a consolidation for
human review cannot be proven by merely checking that its skill instructions
are present. A project may waive automated acceptance of that requirement
while retaining whatever manual review evidence its process requires.

Discuss the decision with the requirement owner, state the limitation and
the reason in the requirement, and revisit it if verification becomes possible.
Do not waive a requirement just because a test is missing, expensive or
inconvenient: write a real test, or split execution between the main-branch
and pull-request pipelines as described below. An acceptance waiver does not
exempt software requirements from their own test coverage; each linked SwRS
must either be covered or have its own justified annotation exemption.

The waiver affects the coverage decision, not the facts reported: an untested
path remains untested and an unaccepted path remains unaccepted. Markers
still describe actual tests, and `W003` still asks for missing scenarios.
This keeps a policy exception visible rather than converting it into a false
claim of acceptance.

The fragment identifies the path actually walked. Once scenarios are
declared, a marker without a fragment would claim all paths at once, so both
verbs require a `#S<n>` fragment. Without declared scenarios a fragmentless
marker is the only link available. The verb is on the test rather than in a
setting, so the test itself states its purpose.

(okfreq-execution-cost)=
## Choosing by execution cost

When the test closest to the final product is costly, mark it `@accepts_req`
and run it in the main-branch pipeline; a cheaper test of the same path can
carry `@tests_req` and run on every pull or merge request. If tests are cheap,
put `@accepts_req` directly on them. This is a recommendation: okfreq does not
check where or how a test runs. `W004` says only that a live stakeholder
requirement has no counting acceptance marker at all.

These are still links, not execution results: `execution_evidence` remains
`not_collected`. See [Acceptance paths and scenario markers](../reference/okfreq-acceptance-paths.md)
for the modes, rules and report fields.
