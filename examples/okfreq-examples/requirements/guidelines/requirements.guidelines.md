---
name: okfreq-requirements
description: 'Shared, project-independent guidance for maintaining okfreq requirement bundles.'
---

# Requirements guidelines

Use this guide for an okfreq requirements bundle. Resolve project-specific paths,
scopes, identifiers, commands and constraints from the project's governing
instructions, configuration and schemas, not from another project's examples.

## Bundle layout

The bundle root owns `config.yml`, this `guidelines/` folder and an optional
human-authored `index.md` overview. `tiers/` owns `_schema/`, `index.md`,
`log.md` and the configured level folders, such as `strs/` and `swrs/`.
Requirement documents live only under `tiers/`.

## Before editing

- Read the nearest `AGENTS.md`, constitution and registered requirements rules.
  Follow the project's authority order; this shared guide does not override it.
- Read every other guideline in this `guidelines/` folder (by convention
  `project.guidelines.md`). Project guidelines specialize this shared text and
  win where they differ. Never edit this file for project rules:
  `okfreq init <bundle> --force` replaces it with the packaged text. Put them in
  a separate file of the folder, which initialization never touches.
- Read the bundle's `config.yml` and every schema under `tiers/_schema/`.
- Derive levels, folders, ID prefixes, scopes, lifecycle values, marker syntax,
  evidence directories and coverage policy from that configuration. Do not
  hard-code another project's names, paths, counts or commands.
- Use `okfreq` for creation, validation, indexing, traceability, and lifecycle changes.
- Use the project's configured environment and task runner; `okfreq` in this
  guide stands for the prescribed invocation, including its environment wrapper.
- Read `okfreq --help` for the authoritative command options.
- When backfilling an existing feature, specify what the code does today (see
  "Anchored to the code"), from the source, the tests and the documentation.
- Follow the governing project's policy for known defects. Describe verified
  behavior accurately, record discrepancies explicitly, and use a `Known issues`
  section when required. Never present a planned fix as already implemented.
- Missing evidence is a coverage gap. Do not repair it by inventing markers,
  approvals, external ownership, exemptions or successful test results.

## Anchored to the code

- Requirements state what the software does today, never the desired state.
- A behaviour that looks wrong is still specified as it behaves, with a line
  "Known issue: …" in the SwRS. The fix changes the code, the test and the SwRS
  in the same change.
- The anchor is the marker pair: `@implements_req` at the code that produces the
  behaviour, `@tests_req` at the test that checks it. When marked code or tests
  move, the markers move in the same change.
- A requirement never names a backlog item or ticket; the ticket names the
  requirement.

## Granularity

- One SwRS is one observable behaviour, with all its scenarios: the nominal
  case, each refusal and each boundary. Do not split them into several SwRS.
- A rule shared by many features (a refusal, a validation, a limit) is written
  once and cited by `depends_on`; it is not repeated per feature.
- Settings, commands and buttons are scenarios of the behaviour they drive, not
  SwRS of their own, unless the project guideline says otherwise.
- An StRS is a user use case; a scope usually has 3 to 8.
- A project may set a finer or coarser rule in its own guideline section.

## Identities

- Never reuse or hand-allocate an ID; create with `okfreq new`.
- `okfreq new` numbers a requirement one above the highest number ever used in
  its level prefix and scope, counting the IDs in `retired_ids` of `config.yml`.
  A number freed by deleting a file is therefore not handed out again, and
  `okfreq validate` rejects a requirement whose ID is listed as retired.
- Retire published requirements with `okfreq archive` or `okfreq supersede`,
  never by deleting the file.
- Discard a draft that was never published (for example one merged into another
  requirement) with `okfreq retire <ID> --yes`, not with `rm` or `git rm`. It
  deletes the file, records the ID in `retired_ids` and appends an entry to
  `tiers/log.md`. It refuses a requirement that is not a draft or that another
  requirement (`derives_from`, `depends_on`, `relates_to`, `superseded_by`) or a
  marker still references: fix those first. Then run `okfreq update-coverage` and `okfreq lint`.
- Deleting a requirement file by hand skips the record: the number stays free
  if it was the highest one. Never delete a file without `okfreq retire`.

## While editing

- Use the frontmatter `title` verbatim as the first Markdown heading (`## Title`).
  Keep the heading synchronized when renaming a requirement; EARS describes
  the statement format, not the document title.

- Store stakeholder requirements under `tiers/strs/<scope>/` and software
  requirements under `tiers/swrs/<scope>/`.
- Use the filename and ID convention established by the bundle.
- Create requirements through `okfreq new`, never by allocating IDs or writing
  frontmatter manually. Preserve IDs, UUIDs, authored fields, unknown metadata,
  comments and bodies.
- Author parent relationships with `derives_from`. Retire a published requirement
  with `okfreq supersede OLD NEW [NEW...] --yes`, which writes the authored
  `superseded_by` list (required, non-empty, on every `superseded` requirement and
  only there). Link requirements that are merely connected with `relates_to`.
  Never hand-edit generated `derived_by`, `supersedes`, `implemented_in_files`,
  or `tested_in_files` fields.
- For leaf software requirements, add `@implements_req <ID>` markers near the
  implementation and `@tests_req <ID>` markers near corresponding tests. Do not
  use source markers on stakeholder or other non-leaf levels. A real direct
  stakeholder validation test may carry an StRS test marker when the configured
  coverage mode requires it.
- A behavior fix changes the code, tests and SwRS together. Preserve the identity
  when refining the same contract; use lifecycle operations when replacing it.
- Define a cross-cutting rule once. Requirements that rely on it reference its
  ID through configured dependency fields instead of copying its scenarios.
- Use the project's shared vocabulary. Keep issue/backlog references outside
  normative statements so an issue's lifecycle cannot change their meaning.

## Traceability markers

- Use the configured marker prefixes near actual evidence. With the defaults,
  put `@implements_req <ID>` near the implementation and `@tests_req <ID>` near
  each test that checks the behavior.
- The same requirement ID may appear more than once in a file, for example
  when several tests verify different scenarios of the same requirement.
  Keep a marker beside each relevant test or implementation point. Do not
  remove these links or consolidate them at the first test merely to make
  the ID unique per file. Repeating an identical marker at the same evidence
  point adds no useful information.
- `okfreq` accepts repeated markers silently and lists the file once in the
  generated coverage. That file-level list neither enumerates tests nor
  proves that each marked test ran successfully.
- Markers must start a line after optional indentation and a supported comment
  opener (`//`, `#`, `/*`, `*` or `<!--`). A marker after executable code on
  the same line is not recognized. In JSDoc, use a separate ` * ` line rather
  than the `/**` opening line.
- Implementation markers belong to configured `source_dirs`; test markers
  belong to configured `test_dirs`. When code or tests move, move their markers
  with them. Keep markers outside generated HTML/CSS strings.
- For declarative behavior that cannot carry a marker, use configured exemption
  fields only with an explicit, justified decision. Companion marker files,
  when permitted by project policy, identify their owning file and remain
  synchronized with its existence and behavior.

## Generated navigation metadata

`okfreq init` adds `x-okf-link` annotations to the generated schemas. They
declare requirement filename-stem links and project-relative source/test links,
including advisory `id_marker`, marker prefixes, tooltip/preview field hints,
and source/test line-number hints. These annotations guide editors and other
consumers; they do not execute tests or prove coverage. Existing schemas are
preserved and are not migrated by `okfreq init`.

## Tier-specific authoring formats

- For an StRS, pass a stakeholder-observable `SHALL` statement as
  `--description` and the underlying outcome as `--user-need`. Complete the
  generated normative behavior, user need, and rationale/constraints sections.
  Do not add SwRS scenarios or verification notes.
- For an SwRS, pass one observable, bounded `SHALL` response as `--description`
  and at least one valid StRS ID with `--derives-from`. Complete the generated
  GIVEN-WHEN-THEN scenarios, adding one per refusal or boundary of the same
  behaviour, and the objective verification notes. Do not add an StRS user-need
  or stakeholder-constraints section.
- Cover nominal behavior and relevant refusal, failure or boundary cases.
  Group equivalent inputs and outcomes in a scenario table. Split unrelated
  behaviors rather than growing an unbounded scenario list in one SwRS.
- Settings, commands, buttons and protocol shapes belong to the bounded
  behavior they implement. State accepted values, defaults, malformed input
  and stale-request handling where applicable; avoid duplicate requirements
  for equivalent entry points.
- Replace every angle-bracket placeholder before review. A remaining placeholder
  is an explicit gap, not content to delete or silently reinterpret.

## After editing

- Run `okfreq validate --prose`, then `okfreq lint --prose` so unfinished
  scaffold placeholders remain visible as advisory findings.
- Refresh owned fields with `okfreq update-coverage <bundle>`. When the project
  root is known, add `--check-links --project-root <project>` to validation and
  lint. Inspect trace, graph, status and reports as appropriate.
- Preview generated updates with the command's `--check` or `--diff` options
  before applying them.
- Write generated reports to the project's designated output directory with
  `--output-json` and `--output-summary-md`, never into `tiers/`. Use a
  project-relative `dist/` directory when no output policy is defined.
- Missing or malformed requirement frontmatter and missing IDs fail explicitly;
  repair the document instead of dropping it from the reported inventory.
- Treat `draft`, `proposed`, and `approved` as distinct lifecycle states.
- Run the project's own test suite; a marker is a link, not proof that a test passes.
- Run the complete project quality gate. Do not claim complete traceability
  when non-exempt leaf requirements lack source or test links, markers reference
  unknown IDs, or validation/tests fail. Report unexecuted checks and failures.
- A behavior change updates affected requirements, tests, human documentation,
  release notes, standalone agent guidance and examples in the same change.
  Preserve unrelated working-tree edits and review generated diffs.
- Initialization preserves existing project files; it must not silently replace
  project policies with new defaults. The one exception is this file, which
  `okfreq init --force` replaces so that it can be refreshed.

## Navigation and change history

- Run `okfreq lint <bundle>` after adding, moving, removing or changing a
  requirement. It generates `tiers/index.md`, configured tier indexes and
  indexes in every directory containing requirements or their descendants,
  including scope folders such as `tiers/swrs/core/index.md`.
- Only content between `<!-- okfreq:index:start -->` and
  `<!-- okfreq:index:end -->` is generated. Do not hand-edit that block.
  Frontmatter, introductions and authored text outside it are preserved.
  The optional `<bundle>/index.md` overview is authored and is not generated.
- Preview with `okfreq lint <bundle> --diff`; use `--check` for read-only CI
  verification. Check mode fails when navigation is absent or stale. Structural
  validation must pass before lint writes any indexes.
- Agents append a dated entry to `<bundle>/tiers/log.md` after substantive
  requirement changes: record affected IDs or relative links, what changed,
  why it changed, decisions or open questions and actual verification results.
  Put newest dates first and append to an existing date section when appropriate.
- The canonical filename is `log.md`, not `logs.md`. It is authored history:
  lint must never regenerate or overwrite it. Do not add a history entry solely
  because identical generated artifacts were refreshed, or invent approvals or
  test results. Preserve previous entries.
