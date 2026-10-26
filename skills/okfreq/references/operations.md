# Operating okfreq without the source repository

Use this reference for commands, configuration, navigation, and troubleshooting.
It is shipped inside the skill; no project source checkout or documentation site
is needed. Run the installed CLI. Use `okfreq COMMAND --help` to check flags if
an older installed release differs. Project-local guidelines override examples.

## A complete first workflow

From the target project's root:

```bash
okfreq init .
okfreq new strs "Export reports" --path . --project demo \
  --description "The reporting capability SHALL provide portable reports." \
  --user-need "Users need to review reports offline."
okfreq new swrs "Write CSV" --path . --project demo \
  --description "When export is requested, the service SHALL return CSV." \
  --derives-from StRS-default-001
```

With no existing bundle this creates `.agents/requirements/`, unless project
agent configuration selects `.github/`. An explicit `requirements/` path creates
a top-level bundle. Read the generated config and guideline before continuing.
IDs in this example assume default settings and an empty bundle; use the IDs
actually returned. Fill the StRS need and constraints, then the SwRS nominal and
failure scenarios and verification notes. Scaffold placeholders remain advisory
prose findings, not completed requirements.

Implement the behavior and test it. Put comment markers near the corresponding
source and tests, using the configured spellings:

Use `# @implements_req SwRS-default-001` in source and
`# @tests_req SwRS-default-001` in the corresponding test file.

```bash
okfreq trace . --json
okfreq update-coverage . --diff
okfreq update-coverage .
okfreq update-coverage . --check
okfreq validate . --prose --check-links --project-root .
okfreq lint . --prose --check-links --project-root .
okfreq generate-report . --output-json dist/requirements-report.json \
  --output-summary-md dist/requirements-report.md
```

`--check` exits non-zero when generated fields are stale. `--diff` prints the
proposed updates without writing. Validation is read-only; lint validates then updates only marked index blocks. `validate
--json` emits structural findings; an unindexable document instead fails with
an explicit file-path error. Missing/malformed mapping frontmatter or a missing
string ID must be repaired before graph operations or reporting can continue.
No requirement is silently dropped from totals.

A JSON report also produces a sibling `.schema.json` file. Without output
options, `generate-report` writes JSON, schema and Markdown under the resolved
bundle's parent's `dist/`; it does not print the report body to stdout. Prefer
explicit project `dist/` paths for predictable placement.

## Configuration and ownership

The bundle root owns `config.yml` and `guidelines/`; its `tiers/` owns `_schema/`
and requirement documents. Source and test scan paths are project-relative,
whereas level folders are relative to `tiers/`.

```yaml
version: 1
levels:
  StRS: {folder: strs, prefix: StRS, derives_from: []}
  SwRS: {folder: swrs, prefix: SwRS, derives_from: [StRS]}
id_policy: scope-prefix-sequence
strs_test_coverage_mode: linked-swrs-and-validation-test
lifecycle:
  values: [draft, proposed, approved, deprecated, superseded]
markers:
  implements: '@implements_req'
  tests: '@tests_req'
  id_pattern: '[A-Za-z][A-Za-z0-9_-]*'
generated_fields: [derived_by, supersedes, implemented_in_files, tested_in_files]
retired_ids: []
scopes:
  core: {id_token: CORE, folder: core, source_dirs: [src], test_dirs: [tests]}
```

- `id_token` controls new ID spelling; `folder` groups new documents by scope.
  Never change existing IDs or UUIDs when changing allocation settings.
- `derives_from` is authored; `derived_by` is computed. `depends_on` is authored
  dependency metadata, not a second derivation graph.
- `superseded_by` is an authored list of the requirement IDs that replace this
  one (write it with `okfreq supersede`, never by flipping the lifecycle alone);
  `supersedes` is its computed inverse. `relates_to` is an authored list for
  lateral links that mean neither derivation nor replacement; it has no inverse,
  so declare it on one side only. A legacy scalar `superseded_by: ID` is still read
  (validation adds the informational `I2`); convert it to a list.
- Only the four listed `generated_fields` are supported. Omitting a generated
  field leaves it unmanaged; unsupported names fail. StRS never carries generated
  source/test file arrays, even when the setting lists those fields.
- The default StRS mode is `linked-swrs`: every linked SwRS needs a test marker
  and at least one SwRS must exist. The stricter mode also needs a direct
  `@tests_req StRS-...` marker in a configured test file. This is a defined
  validation test, not proof of execution. Do not put implementation markers on StRS.
- `annotation_exemption: true` needs a non-empty `exemption_reason`. Use only
  for an agreed exception; report it separately, never as observed coverage.
- Unknown producer metadata is preserved. `external_id` and `external_url`
  describe external tracker identity; they are not local requirement IDs.
- `okfreq config-merge incoming.yml --path .` (alias `import`) merges config,
  preserves destination values on conflicts and reports the conflicts. It does
  not import requirement documents from a tracker.
- Additional levels require compatible schemas and config. The creation CLI
  offers `new strs` and `new swrs`; do not invent `new sysrs` commands.

## File navigation and target checks

Generated schemas annotate relationship items as `filename-stem` and evidence
items as `project-relative`. Relationships must use unique, case-sensitive
Markdown basenames matching their IDs. Graph validation still uses frontmatter
IDs, so moving or renaming a file can leave the graph valid while navigation
fails. `external_id` remains an ordinary external identifier.

Custom fields may use `x-okf-link: {resolution: ..., syntax: ...}` on a scalar
string or on string array `items`. Both keys are required:

| Resolution | Target |
|---|---|
| `document-relative` | Exact path from the current Markdown file, allowing `../`. |
| `bundle-relative` | Exact path from the bundle root, including its extension. |
| `bundle-relative-stem` | Bundle path without `.md`; the checker appends `.md`. |
| `project-relative` | Exact path from `--project-root`, otherwise the containing Git root. |
| `filename-stem` | Unique Markdown basename without extension anywhere in the bundle. |

`syntax: plain` uses an ordinary path; `syntax: wikilink` accepts
`[[target#heading|label]]`. Query, fragment and label are separated from the
filename; headings and block anchors are not checked. Absolute targets and
bundle/project escapes are rejected. Missing or ambiguous stems and missing
exact files produce `E10`; unavailable roots or inaccessible candidates produce
`W15` skipped checks. A warning is not a verified target. No workspace/CWD root
is guessed. Checks are opt-in and do not migrate existing schemas.

Navigation hints are advisory: `id_marker: id` identifies requirement identity,
`basename_marker` supplies a marker prefix such as `@implements_req`,
`show_line_number: true` guides opening at a marker, and
`tooltip_shows_fields`/`preview_shows_fields` list target metadata to display.
The CLI checks files; it does not render tooltips or find marker lines for editors.

## Inspection, lifecycle and repair

| Task | Command or interpretation |
|---|---|
| List/find requirements | `okfreq index .`, `okfreq search CSV .`, `okfreq in-file FILE` |
| Inspect scope and hierarchy | `okfreq scope .`, `okfreq graph . --json` |
| Inspect lifecycle health | `okfreq status .` |
| Inspect marker evidence | `okfreq trace . --json` |
| Archive explicitly | `okfreq archive ID --path . --yes` sets `deprecated`, never deletes. |
| Supersede explicitly | `okfreq supersede OLD NEW [NEW2...] --path . --yes` sets `superseded`, writes the `superseded_by` list and preserves identity; then run `okfreq update-coverage` to refresh `supersedes`. Validation requires a non-empty `superseded_by` on every superseded requirement, forbids it otherwise, and rejects unknown, self, repeated or cyclic targets. |
| Discard a never-published draft | `okfreq retire ID --path . --reason TEXT --yes` deletes it, lists the ID in `retired_ids` of `config.yml` and logs it in `tiers/log.md`. It refuses a non-draft, a requirement referenced by `derives_from`, `depends_on`, `relates_to`, `superseded_by` or a marker, and a missing `--yes`; resolve the reference first. Afterwards run `update-coverage` and `lint`. |

`okfreq new` numbers after the highest number ever used in the level prefix and
scope, counting `retired_ids`; a number is never reused. Never delete a requirement
file by hand (the highest number would be allocated again): use `retire` for a
draft, `archive` or `supersede` for anything published. `validate` reports a
document whose ID is listed in `retired_ids`.

Only run lifecycle mutations when authorized. Preview/review config and authored
changes before applying; preserve imported requirements unless their migration
is part of the task. A duplicate trace marker means the same ID appears twice
in one file; evidence in multiple files is legitimate. `missing_ids` needs a
real requirement or a corrected marker; `non_leaf` needs inspection of the
configured hierarchy. Missing scan directories make coverage incomplete.

For structural errors repair the indicated file, do not delete it to reduce the
error count. For `E10` fix the target, filename ambiguity, or annotation; for
`W15` provide the correct root or restore access. For `W17` (a requirement schema file
that is unparsable or not a mapping) repair the named file; `I1` (an empty schema file) is
informational and does not fail validation. For stale coverage preview and
regenerate it. Execute the project's actual tests separately and report their
results independently from marker percentages. For broad drift audits locate
the installed `okfreq-gardening` skill by name.

## Navigation and authored change history

After substantive changes run `okfreq lint <bundle>`: it creates `tiers/index.md`,
configured tier indexes and all requirement/scope ancestor indexes. Each lists
immediate subdirectories and requirements with their IDs, titles and descriptions.
Only the block bounded by `<!-- okfreq:index:start -->` and
`<!-- okfreq:index:end -->` is generated; preserve authored prose and frontmatter
outside it. `<bundle>/index.md` is an optional authored overview.

Use `okfreq lint <bundle> --diff` to preview without writes and `--check` to
fail on stale indexes without writes. Structural validation runs before writing.
`okfreq index <bundle>` prints IDs, not generated Markdown. Do not confuse these
commands or claim lint is entirely read-only without a preview flag.

Append a dated entry to `<bundle>/tiers/log.md` for substantive requirement
changes. Record affected IDs/relative links, changes, rationale, decisions/open
questions and actual verification results; newest dates first, preserving prior
entries. The canonical filename is singular `log.md`. Lint never generates log
content. Routine regeneration alone needs no invented history or approval.

## Backfill an existing feature and install the maintenance loop

Start with one bounded feature. Read its agreed documentation, implementation
and tests, then propose a draft stakeholder outcome and observable software
behaviors. Identify evidence and unresolved assumptions. Existing code is not
sufficient evidence of desired behavior: do not turn bugs or incidental design
choices into stakeholder requirements. Review the intended contract before
creating drafts. Preserve working code when only its documentation or links need
updating.

Create StRS/SwRS through the CLI, fill both bodies and add one configured marker
per requirement ID per source/test file. A file can address several requirements;
a requirement can refer to several files. Do not duplicate a marker for each
case in a test file. Run the real tests separately from link inspection.

Register the bundle's local guideline, config, schemas and affected requirement
reading path in the target project's AGENTS.md or equivalent instructions.
Require stable IDs/UUIDs, unchanged approval state unless explicitly decided,
real evidence, heading/title consistency and authored log entries for substantive
changes. Use the project's actual task runner and dependency environment.

Separate local generation from CI checks:

```bash
# Preview, then refresh intentionally after reviewing the diff.
okfreq update-coverage requirements --diff
okfreq lint requirements --diff --prose --check-links --project-root .
okfreq update-coverage requirements
okfreq lint requirements --prose --check-links --project-root .
# CI: check freshness and targets without rewriting files.
okfreq lint requirements --check --prose --check-links --project-root .
okfreq update-coverage requirements --check
```

Adapt the example bundle path. Run normal tests in the same preflight and keep
runtime dependencies locked. These checks do not require every feature to have
a requirement or every requirement to have markers; inspect trace/report gaps
and establish any stronger delivery policy explicitly. Prose warnings remain
advisory. Keep generated reports in explicit project dist/ paths and distinguish
linkage from test execution and human approval in the final report.
