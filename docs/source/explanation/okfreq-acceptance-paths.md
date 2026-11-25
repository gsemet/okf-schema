# Why `okfreq` measures acceptance paths

A stakeholder requirement (`StRS`) describes a complete outcome a user observes
from start to finish. A software requirement (`SwRS`) describes one bounded
software behavior that contributes to that outcome. In `okfreq`, connecting
requirements to tests with markers is useful only when the markers stay honest
about what each test actually walks.

## Why a direct StRS marker is a link, not a proof

In `linked-swrs-and-validation-test` mode, a single `# @tests_req StRS-CORE-001`
comment anywhere in a test file marks the stakeholder requirement as having a
validation test. That tells a reader that *some* test mentions the StRS, not
which stakeholder workflow it exercises. A test that checks one snapshot of
state, or repeats one SwRS transition in isolation, looks identical to an
end-to-end test that walks every main path a user depends on.

Declaring the main paths of a StRS in frontmatter (`scenarios:`) and attaching
a `#S<n>` fragment to every test marker turns an all-or-nothing boolean into a
reviewable fraction: how many of the stakeholder's main paths have tests, and
how many have acceptance tests.

## Two verbs and two independent counters

In `linked-swrs-and-acceptance-paths` mode, `okfreq` separates two test verbs
for stakeholder requirements:

- **`@tests_req`** marks a test of a software requirement transition
  (`@tests_req SwRS-X#S<n>`) or a test of a stakeholder main path
  (`@tests_req StRS-X#S<n>`). On a StRS, it feeds the **tested** counter.
- **`@accepts_req`** marks the **acceptance test** of a stakeholder main path
  (`@accepts_req StRS-X#S<n>`). It applies to StRS only (never SwRS) and feeds
  the **accepted** counter.

The two counters on a StRS are **independent**:

- A path marked only with `@accepts_req` counts as **accepted** and not
  **tested**.
- A path marked only with `@tests_req` counts as **tested** and not
  **accepted**.
- A path marked with both counts in both counters.

StRS coverage (`status: "covered"`) normally requires **accepted** (every
declared main path has a counting `@accepts_req`, in addition to every linked
SwRS being test-covered or individually exempted), because stakeholder
acceptance is the end-to-end claim. The **tested** counter is reported beside
it so teams can see cheaper coverage separately without mistaking it for
acceptance. The one explicit exception is a justified whole-StRS acceptance
waiver (described below).

(okfreq-execution-cost)=
## Choosing by execution cost

Why keep two verbs instead of one? Because the test closest to the final
product often has a different execution cost from a fast in-process test:

- **When acceptance tests are expensive** (for example, building a wheel,
  spinning up a full environment, or driving a browser or external service):
  mark the full end-to-end test with `@accepts_req StRS-X#S<n>` and run it on
  the main-branch or release pipeline. Beside it, mark a faster, cheaper test
  of the same path (for example, an in-process CLI or API test) with
  `@tests_req StRS-X#S<n>` so it runs on every pull or merge request.
- **When acceptance tests are cheap**: put `@accepts_req StRS-X#S<n>` directly
  on them. You do not need a separate `@tests_req` test just to fill the
  `tested` column.

This split is a **recommendation**, not an enforcement rule. `okfreq` does not
inspect CI pipelines or measure how a test runs; it only reads markers. When a
live, non-waived StRS has no counting `@accepts_req` marker at all,
`okfreq validate` emits advisory warning `W004` to make the gap visible.

## When an owner may waive whole-StRS acceptance

Some stakeholder requirements genuinely cannot be acceptance-tested in an
automated suite — for example, an interactive agent skill whose outcome depends
on live human judgment in a conversation. For those cases, the StRS owner may
record a **whole-StRS acceptance waiver** in frontmatter:

```yaml
acceptance_exemption: true
acceptance_exemption_reason: >
  Interactive human-guided workflow; verified by manual review and
  component tests of each linked SwRS rather than automated acceptance runs.
```

Rules for using a waiver honestly:

- **Cost alone is never a valid reason.** If an acceptance test is slow or
  expensive, run it in a slower pipeline and keep `@tests_req` for fast pull
  request checks — do not waive acceptance.
- **Document the reason and remove it later.** `acceptance_exemption_reason`
  must be non-blank and explain *why* automated acceptance is impossible today.
  If the product later becomes acceptance-testable, remove both fields and add
  `@accepts_req` markers.
- **A waiver is not an accepted path.** The waiver satisfies the StRS coverage
  policy (`status: "covered"`) and suppresses `W004`, while `accepted` stays
  `false`, `paths.accepted` stays at the real count of counting `@accepts_req`
  markers, and the Markdown report prints `exempt` in the `Accepted` column.
- **A waiver does not substitute for SwRS coverage.** Every linked SwRS must
  still be test-covered (or carry its own justified `annotation_exemption` with
  a non-blank `exemption_reason`). Conversely, a SwRS annotation exemption
  satisfies only that SwRS (`linked_swrs[].status: "exempt"`) and never waives
  its parent StRS's acceptance.

## Why a fragment (`#S<n>`)

A file-level marker without a fragment (`@accepts_req StRS-CORE-001`) cannot
say *which* of the stakeholder's main paths the test walks. Without a fragment,
one test covering only the simplest path would look identical to a suite
covering all three paths. Appending `#S1`, `#S2`, … ties each test to a
specific declared path or software transition so `okfreq` can compute exact
fractions (`2/3`) and list missing transitions (`S2`).

## Why declaring `scenarios:` makes fragments mandatory

In `linked-swrs-and-acceptance-paths` mode, one uniform rule governs both
`@tests_req` and `@accepts_req` on both `StRS` and `SwRS`:

- **Once `scenarios:` is declared**, every test or acceptance marker targeting
  that requirement **must** carry a declared `#S<n>` fragment. A fragmentless
  marker is an error and does not count, because otherwise a single
  fragmentless marker would silently claim coverage of every path at once.
- **While `scenarios:` is absent**, markers targeting that requirement **must
  not** carry a fragment; a fragmentless marker is the only honest link until
  the author declares the scenarios.

## Why the verb lives in the marker, not in configuration

Putting the verb directly in the comment (`@tests_req` vs `@accepts_req`) means
the test itself declares what kind of evidence it provides. A configuration
file mapping directories or filename patterns to "acceptance" would drift as
soon as tests move or a file mixes fast and slow tests. With two explicit
verbs, moving a test keeps its meaning intact.

## Still linkage, not execution

Measuring paths and separating `@tests_req` from `@accepts_req` makes
traceability finer and more honest, but `okfreq` still scans source text
rather than test-runner output. `execution_evidence.status` remains
`not_collected`: a marker links a path to a test definition and does not prove
that the test ran or passed.

## Choosing a coverage mode

| Need | Recommended mode |
|---|---|
| Lightweight traceability from StRS to tested SwRS only | `linked-swrs` |
| Require at least one direct `@tests_req StRS-ID` link per StRS | `linked-swrs-and-validation-test` |
| Track declared main paths, SwRS transitions, and `@accepts_req` acceptance separately | `linked-swrs-and-acceptance-paths` |

See the [Acceptance paths and scenario markers reference](../reference/okfreq-acceptance-paths.md)
for the complete grammar, mode comparison, combination matrix, worked examples,
and report schema.
