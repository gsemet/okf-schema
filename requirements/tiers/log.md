# Update Log

## 2026-11-25

### Trust tier actor forms

- Why: OKF 0.2 sections 5.3 and 7. An actor written as `<producer>/<version>` read as
  unverified and was warned W10.
- What: [SwRS-OKFSCHEMA-CORE-006](swrs/core/SwRS-OKFSCHEMA-CORE-006.md) gained S5. Any
  actor that is not `human:<id>` counts as machine-confirmed (`human:` alone included).
  W10 accepts `<producer>/<version>` and `<prefix>:<identifier>`, with a dot allowed in
  the producer and the prefix, and its message now prints the entry index.
- Verification: `okfreq update-coverage`, `okfreq validate --prose --check-links`
  (0 errors, 0 warnings), `okfreq lint --prose --check-links`, `okfreq trace --json`,
  `just style-check`, `just lint`, `just typecheck` and `just requirements-lint` pass.
  `just test` on Windows: 1118 passed, 14 skipped, 8 failed because the host refuses to
  create symbolic links (`WinError 1314`).

### Show a concept by name, inside the bundle

- Added [SwRS-OKFSCHEMA-CORE-010](swrs/core/SwRS-OKFSCHEMA-CORE-010.md) (S1 to S3) as
  the shared "stay inside the bundle" rule: a concept path whose real path, symbolic
  links followed, is outside the bundle is refused without being read. It is applied to
  `show` only so far, and its known issue names the commands that still follow outside
  links.
- [SwRS-OKFSCHEMA-CORE-005](swrs/core/SwRS-OKFSCHEMA-CORE-005.md) gained S3 (a name
  resolves without `.md`) and S4 (a leading `/` reads from the bundle root, OKF 0.2
  section 6.1), a widened S2 that includes a directory, and `depends_on`
  SwRS-OKFSCHEMA-CORE-010.
- Reason: `show` read files outside the bundle and refused names without `.md`.
- Both stay `proposed`; neither is approved.
- Verification, on Windows with Python 3.12: `okfreq update-coverage --check`,
  `okfreq validate --prose --check-links` and `okfreq lint --check --check-links` pass,
  and `okfreq trace --json` lists both requirements as implemented and tested.
  `just preflight` stops at its test step: 1112 tests pass, 21 are skipped, and 8
  tests of other capabilities fail because this host does not permit symbolic links
  (WinError 1314). The 7 new symlink tests are skipped for that reason and the
  acceptance test of `show` is skipped on Windows. The examples, report and
  documentation steps pass when run on their own.

## 2026-11-24

### Acceptance paths

- Switched `strs_test_coverage_mode` from `linked-swrs-and-validation-test` to
  `linked-swrs-and-acceptance-paths`. `markers.accepts` is `@accepts_req` and
  `generated_fields` lists `accepted_in_files`.
- Added [SwRS-OKFSCHEMA-OKFREQ-015](swrs/okfreq/SwRS-OKFSCHEMA-OKFREQ-015.md): okfreq
  reads the StRS main paths and the requirement scenarios, counts the markers that
  carry a `#S<n>` fragment into independent tested and accepted counters, warns with
  `W003` and `W004`, reports the paths and leaves the other modes unchanged.
- Updated the bundle schemas: `base.schema.yaml` gains the `scenarios` property and the
  `req_lifecycle` description states the exception for a `scenarios:`-only edit;
  `strs.schema.yaml` gains `acceptance_exemption`, `acceptance_exemption_reason`,
  `tested_in_files` and `accepted_in_files`; `swrs.schema.yaml` refuses
  `accepted_in_files`.
- Declared the acceptance paths of the five StRS (13 in all) in a `### Main paths`
  section and in `scenarios:` frontmatter, and declared `scenarios:` on the 29 other
  SwRS from their 93 `### Scenario` headings (`S1…` in order). The five StRS and
  all SwRS are `proposed`, so the body headings were aligned to
  `### Scenario S<n>: <title>` and the StRS bodies gained the `### Main paths` section.
- Declaring only `scenarios:` on an approved requirement is a frontmatter-only edit
  that keeps `approved_by` and `approved_at`; no requirement of this bundle is approved
  now, and the owner agrees to this edit by reviewing the change. The owner reviews the
  paths written in the five StRS.
- Every `@tests_req` marker in `tests/` now carries a `#S<n>` fragment on the test that
  exercises the scenario; the six direct StRS markers name the path they exercise;
  tests that exercise no scenario lost their marker. Scenarios without a test got
  new tests.
- Added the acceptance tests `tests/test_acceptance_core.py`,
  `tests/test_acceptance_okfkb.py` and `tests/test_acceptance_okfreq.py`: twelve
  `@accepts_req` tests that walk the paths against the installed wheel.
- Two justified exemptions: [StRS-OKFSCHEMA-OKFKB-001](strs/okfkb/StRS-OKFSCHEMA-OKFKB-001.md)
  carries `acceptance_exemption` because its path S3 (propose a consolidation for human
  review) is interactive, and
  [SwRS-OKFSCHEMA-OKFKB-005](swrs/okfkb/SwRS-OKFSCHEMA-OKFKB-005.md) carries
  `annotation_exemption` for the same reason.
- Verification: `okfreq update-coverage`, `okfreq validate --prose --check-links`
  (0 errors, no `W003` or `W004`), `okfreq lint`, `okfreq trace` and `just preflight`.

## 2026-10-30

### Native OKF projection

- Added [SwRS-OKFSCHEMA-CORE-009](swrs/core/SwRS-OKFSCHEMA-CORE-009.md): schemas
  declare how metadata is projected for plain OKF consumers. `x-okf-link` accepts a
  `link-projection` label (only on a resolution inside the bundle) and a property may
  carry an `x-okf-status-projection` mapping; `okf-schema lint` and `okfkb update`
  generate a delimited `### Links` body section and `status` from them, `validate`
  reports malformed annotations as `E11`, and `log.md` headings must be exactly
  `## YYYY-MM-DD`, newest first (`W5`, new `W18`; `lint --check` fails on them).
- Added [SwRS-OKFSCHEMA-OKFREQ-014](swrs/okfreq/SwRS-OKFSCHEMA-OKFREQ-014.md): okfreq
  bundles stay native OKF bundles. The lifecycle key is `req_lifecycle`, mapped onto
  OKF `status`; `approved_on` is replaced by `approved_at` (ISO 8601 datetime with an
  offset), projected onto a `verified` event by a `human:` actor; relation fields
  become Links sections; `status` and `verified` are new generated fields; `validate`
  also runs the base OKF checks on the tiers folder. No backward compatibility is kept.
- Updated [SwRS-OKFSCHEMA-OKFREQ-013](swrs/okfreq/SwRS-OKFSCHEMA-OKFREQ-013.md) for
  `req_lifecycle` and `approved_at`, and
  [SwRS-OKFSCHEMA-OKFKB-006](swrs/okfkb/SwRS-OKFSCHEMA-OKFKB-006.md) for the projected
  derivation links.
- This bundle renamed `lifecycle` to `req_lifecycle`, annotated its base schema and
  regenerated `status` and the Links sections of all requirements.
- Verification: `just preflight`.

## 2026-10-28

- Added [SwRS-OKFSCHEMA-OKFREQ-013](swrs/okfreq/SwRS-OKFSCHEMA-OKFREQ-013.md):
  lifecycle states now have documented meanings (`draft` is a proposal not yet
  implemented, `proposed` is implemented but not frozen, `approved` is frozen by its
  owner). `config.yml` uses `tiers` instead of `levels` and names the lifecycle field
  instead of repeating its values, which now come from the base schema; both legacy
  forms are still read. Each tier states `approval_lock` (true for StRS, false for SwRS
  by default) and may name an `owner_email`; a scope overrides the owner, and
  `scopes.<scope>.tiers.<tier>` overrides both. `default_owner_email` is a new
  generated field, `owner_email` its authored override. An `approved` requirement
  needs `approved_by` and `approved_on` and a lockable tier and scope; the error
  tells a coding agent to record the owner's agreement and request the owner's
  review. `okfreq new --lifecycle proposed` creates a requirement delivered with its
  code. This bundle moved to the new configuration names, names its owner, and all
  32 requirements moved from `draft` to `proposed`: each one is implemented and
  linked. No requirement is approved: approval is the owner's decision.
- Extended [SwRS-OKFSCHEMA-OKFREQ-013](swrs/okfreq/SwRS-OKFSCHEMA-OKFREQ-013.md) after
  review: `okfreq import`/`config-merge` rename `levels` to `tiers` on both sides and
  report an imported `lifecycle.values` list as a conflict when the destination names
  `lifecycle.field`; a custom lifecycle field name works in a hand-written schema; a
  `null` `approval_lock` counts as unset; a retired requirement may keep its approval
  record. [SwRS-OKFSCHEMA-OKFREQ-010](swrs/okfreq/SwRS-OKFSCHEMA-OKFREQ-010.md): the
  setup skill creates requirements `proposed`, records the owner and approves
  nothing. [SwRS-OKFSCHEMA-OKFREQ-005](swrs/okfreq/SwRS-OKFSCHEMA-OKFREQ-005.md) says
  tiers instead of levels (wording only).
- Verification: see the pull request for the preflight result.

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
