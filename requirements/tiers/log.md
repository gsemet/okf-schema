# Update Log

## 2026-10-26

- Added [SwRS-OKFSCHEMA-OKFREQ-012](swrs/okfreq/SwRS-OKFSCHEMA-OKFREQ-012.md):
  `superseded_by` is now an authored list of replacing requirements (a superseded
  requirement must have a non-empty one, any other lifecycle must not; unknown, self,
  repeated and cyclic targets are rejected; the scalar written by earlier releases is
  still read, with informational `I2`). `supersedes` is its generated inverse, kept by
  `okfreq update-coverage` through `generated_fields` and written only where it has a
  value. `relates_to` is a new authored list for lateral links, with no generated
  inverse by decision: a stored inverse doubles every edit and goes stale, and readers
  treat the link as undirected. `okfreq supersede` takes one or more replacements.
  Extended [SwRS-OKFSCHEMA-OKFREQ-007](swrs/okfreq/SwRS-OKFSCHEMA-OKFREQ-007.md) and
  [SwRS-OKFSCHEMA-OKFREQ-004](swrs/okfreq/SwRS-OKFSCHEMA-OKFREQ-004.md) with the
  list form and the report fields. This bundle's schema gained the three `x-okf-link`
  properties and `supersedes` joined its `generated_fields`; it supersedes nothing
  itself, so the showcase covers the lifecycle path. Retire also refuses a requirement
  referenced by `relates_to`.
- Verification: see the pull request for the preflight result.

## 2026-10-25

- Added [SwRS-OKFSCHEMA-CORE-008](swrs/core/SwRS-OKFSCHEMA-CORE-008.md): schema files
  that yield no schema are now reported instead of skipped silently. An empty or
  comment-only file is informational `I1`; a syntax error, unreadable file or
  non-mapping content is warning `W17` (`W16` is reserved elsewhere). The scenarios
  also fix that the legacy `load_schema_database` stays silent. Coverage fields were
  regenerated with `okfreq update-coverage`, which also added the new requirement to
  the derived list of StRS-OKFSCHEMA-CORE-001. Verification: see the pull request for
  the preflight result.

- Added [SwRS-OKFSCHEMA-OKFREQ-011](swrs/okfreq/SwRS-OKFSCHEMA-OKFREQ-011.md)
  for the new `okfreq retire` command and extended
  [SwRS-OKFSCHEMA-OKFREQ-002](swrs/okfreq/SwRS-OKFSCHEMA-OKFREQ-002.md) with a
  scenario: `okfreq new` now numbers after the highest number ever used in a
  level prefix and scope, counting the new `retired_ids` list of `config.yml`,
  so a deleted requirement's number is never allocated again. Validation rejects
  a requirement whose ID is retired, and config merge takes the union of
  `retired_ids`. The shipped baseline guideline and the okfreq skills describe
  when to retire a draft instead of deleting it; the local overlay needs no
  change because it specializes only paths, scopes and checks. This
  repository's `retired_ids` is empty: no requirement has been discarded.
- Verification: see the pull request for the preflight result.
- Added [SwRS-OKFSCHEMA-OKFREQ-010](swrs/okfreq/SwRS-OKFSCHEMA-OKFREQ-010.md)
  for the new `okfreq-setup` skill, which delivers a baseline of current
  behaviour in one pull request, and added the skill to the `okfreq` scope's
  source folders. The shipped baseline guideline now states that requirements
  describe current behaviour (bugs as "Known issue"), one SwRS per observable
  behaviour with a scenario per refusal or boundary, shared rules written once,
  and IDs never reused. The local overlay needs no change: it specializes only
  paths, scopes and checks. The gardening skill gained a user-approved
  simplification phase.
- Verification: see the pull request for the preflight result.
- Extended [SwRS-OKFSCHEMA-CORE-006](swrs/core/SwRS-OKFSCHEMA-CORE-006.md)
  with two scenarios: `stale_after` is compared as an instant when it is an ISO
  8601 datetime with a UTC offset (the OKF 0.2 form; bare dates still work), and
  a value that cannot be parsed now reports the new warning W16 instead of
  silently disabling the staleness check. The ID, UUID and normative statement
  are unchanged.
- Kept a single requirements guideline: the shipped text is the only maintained copy
  and is project-independent (names, paths and commands come from the bundle's
  configuration). `okfreq init --force` now replaces the installed
  `guidelines/requirements.guidelines.md` with it (without `--force` an existing file
  is kept), strips the shipped file's own requirement marker from the installed copy
  and reports the outcome; other files of `guidelines/` are never touched. Extended
  [SwRS-OKFSCHEMA-OKFREQ-001](swrs/okfreq/SwRS-OKFSCHEMA-OKFREQ-001.md) with that
  scenario. This bundle's rules moved to `guidelines/project.guidelines.md`; its
  `requirements.guidelines.md` is now init output. The okfreq skills no longer embed
  a copy and tell agents to read the installed guideline, then the project file;
  `okfreq-setup` writes project rules to `project.guidelines.md`.
- Extended [SwRS-OKFSCHEMA-OKFREQ-003](swrs/okfreq/SwRS-OKFSCHEMA-OKFREQ-003.md) with
  a scenario: the same requirement ID may be marked several times in one file (for
  example beside distinct tests) and is accepted silently; the file is listed once.
  The `duplicates` key stays in the reports, always empty, for compatibility.
- Verification: see the pull request for the preflight result.

## 2026-10-19

- Consolidated the first-Finding introduction and hardware narrative into the
  [self-contained OKFKB tutorial](../../docs/source/tutorials/okfkb-workflow.md),
  including both illustrations formerly located in the design explanation.
  Kept generic OKF links as an optional separate mechanics exercise and left
  continuation pages at the old tutorial URLs. Reworked the explanation around
  role/history/provenance/governance trade-offs and corrected outdated skill
  installation instructions. The tutorial acceptance test exercises capture,
  derived evidence and navigation for
  [OKFKB-003](swrs/okfkb/SwRS-OKFSCHEMA-OKFKB-003.md) and
  [OKFKB-004](swrs/okfkb/SwRS-OKFSCHEMA-OKFKB-004.md).
  Verification: the published CLI/document snippets passed in a disposable KB,
  including generated provenance and preservation of Finding bodies. The complete
  preflight passed 849 tests with 95.39% coverage and built the documentation,
  including the old-URL continuation pages, without Sphinx warnings.
- Reworked the [traceability tutorial](../../docs/source/tutorials/okfreq-traceability.md)
  around existing-feature adoption: reviewed intent, executable CSV examples,
  agent instructions, local/CI harness targets, a subsequent contract change
  and report interpretation. Preserved the original layered-requirements SVG
  and added ownership/workflow diagrams. The tutorial-snippet acceptance test
  covers the new guidance evidence for
  [SwRS-OKFSCHEMA-OKFREQ-008](swrs/okfreq/SwRS-OKFSCHEMA-OKFREQ-008.md).
  Verification: the actual tutorial snippets and task-runner recipes passed in
  a disposable project; the full preflight passed 848 tests with 95.19% coverage
  and built Sphinx successfully. Both new SVGs were rendered and inspected; the
  existing layered-requirements SVG was preserved byte-for-byte.
- Replaced the generic EARS heading in every project requirement with its
  frontmatter title, preserving the remaining content. Updated StRS/SwRS
  creation templates, human documentation and packaged agent guidance so new
  requirements follow the same reading convention. The CSV examples use their
  own frontmatter titles as well.
- Added [SwRS-OKFSCHEMA-OKFREQ-009](swrs/okfreq/SwRS-OKFSCHEMA-OKFREQ-009.md)
  for generated tier/scope navigation after the missing indexes exposed a gap
  between the expected OKF workflow and the implementation. `okfreq lint` now
  refreshes delimited navigation blocks; `--check` and `--diff` preserve files.
  Authored frontmatter, introductions, the bundle-root overview and this log
  remain outside generator ownership.
- Registered the shipped requirements guideline in the repository's `AGENTS.md`.
  The local guideline now specializes that baseline with our paths, scopes and
  checks; agents must follow the same navigation and logging rules we install
  into other projects.
- Recorded the preceding validation and guidance work: expanded
  [file-link inspection](swrs/core/SwRS-OKFSCHEMA-CORE-007.md), explicit rejection
  of unindexable requirement documents, and
  [standalone operations guidance](swrs/okfreq/SwRS-OKFSCHEMA-OKFREQ-008.md).
  Enabled direct stakeholder-validation evidence and checked documentation,
  skill and example references without changing approval states.
- Verification: the focused navigation, requirement and executable-example
  tests passed (54 tests); Ruff, mypy and ty passed. The preceding complete
  preflight passed 838 tests before the navigation change. The completed
  navigation preflight passed 847 tests, type/style checks, the executable
  examples and the Sphinx documentation build. Navigation freshness is checked
  in CI and in the live-bundle acceptance test.

## 2026-08-28
