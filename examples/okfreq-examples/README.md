# OKFREQ Example

This directory is a small, runnable example of requirements traceability.

## Overview

`okf-schema` brings schema validation for structured Markdown. It gives each
document a known shape, validates its metadata, and checks that the bundle is
consistent.

`okfreq` adds the requirements vocabulary and workflow on top of that
foundation. It connects stakeholder intent to software behavior, tracks the
requirement lifecycle, and records whether the behavior is implemented and
tested.

This example runs in the `linked-swrs-and-acceptance-paths` mode: a stakeholder
requirement declares its main paths, each software requirement declares its
transition scenarios, and the tests name the scenario they exercise.

This example includes one Python requirement and one Rust requirement:
`SwRS-CORE-001` covers the Python CSV writer, while `SwRS-CORE-002` covers a
Rust CSV row formatter.

Here, a software requirement (`SwRS`) is simply a promise about observable
software behavior. `SwRS-CORE-001` says that the service writes CSV output, and
`SwRS-CORE-002` says that its Rust formatter returns a CSV row. A requirement is
not the implementation and it is not the test; it is the contract that the
code and test are expected to satisfy.

That is why this example contains a few different kinds of files: together
they show the path from the original need to the requirement, implementation,
test evidence, and traceability report.

## Pointers

- [Requirements bundle](requirements/)
- [Stakeholder requirement](requirements/tiers/strs/StRS-CORE-001.md)
- [Python software requirement](requirements/tiers/swrs/SwRS-CORE-001.md)
- [Rust software requirement](requirements/tiers/swrs/SwRS-CORE-002.md)
- [Implementation](src/export.py)
- [Tests](tests/test_export.py)
- [Acceptance test](tests/test_acceptance_export.py)
- [Rust implementation](src/rust_export.rs)
- [Rust test](tests/rust_export_test.rs)
- [Traceability report](dist/requirements-report.md)

## Run the concrete workflows

From the repository root:

```bash
just refresh-okfreq-examples
uv run python examples/okfreq-examples/showcase.py
```

The first command regenerates the CSV requirements, runs the Python CSV and
acceptance tests, refreshes source/test evidence and validates file targets
before writing JSON, JSON Schema and Markdown reports under this example's `dist/`. Rust source and
test markers demonstrate linkage; this command does not run a Rust compiler.

The showcase creates a temporary shipping-manifest project and verifies:

- scoped IDs/folders, custom markers, authored dependencies and external demo metadata;
- the three StRS coverage modes (`linked-swrs`, `linked-swrs-and-validation-test` and
  `linked-swrs-and-acceptance-paths`), including a direct stakeholder validation
  marker and the acceptance-paths outcome, where declared main paths are counted
  as tested and as accepted separately;
- conflict-preserving config merge and preservation of unknown authored fields;
- all five file-resolution modes, wikilink labels/fragments, E10 failures and W15 skips;
- index/search/in-file/scope/graph/trace/status and schema-validated JSON reports;
- explicit exemptions, confirmed archive/supersede and preserved UUIDs/bodies;
- a requirement superseded by several others, the generated `supersedes` backlinks, a
  lateral `relates_to` link, and the refused cycle and missing replacement;
- retirement of a never-published draft, refused when unconfirmed or referenced, and
  an ID allocator that skips the retired number;
- a missing-ID failure followed by repaired validation.

Its marker fixtures demonstrate scanning, not execution of shipping software.
Its tracker reference is fictional demo data. All intentional failures and
lifecycle changes stay temporary; the checked-in requirements are preserved.
The Python CSV tests and the acceptance test provide actual executable behavior
evidence separately.

For the live project's feature/evidence map, read
[How this project exercises okfreq](../../docs/source/explanation/project-feature-coverage.md).

## How the example proves its main path

`StRS-CORE-001` declares one main path, `S1` "Export selected rows for offline
review", in its frontmatter `scenarios:` field and in its `### Main paths` body
section. The two SwRS split that promise into behavior: `SwRS-CORE-001` declares
`S1` "Export selected rows" and `S2` "Export an empty selection", `SwRS-CORE-002`
declares `S1` "Return a Rust CSV row" and `S2` "Export an empty Rust row".

The example uses the two test verbs for two different jobs:

- `@tests_req <ID>#S<n>` marks a test of one declared scenario. The Python tests
  carry it per test (`tests/test_export.py::test_export_rows` for `#S1`,
  `::test_export_rows_with_empty_selection` for `#S2`), and so do the two Rust
  tests. `test_export_rows` also carries `@tests_req StRS-CORE-001#S1`: it is the
  cheap in-process test of the stakeholder path.
- `@accepts_req StRS-CORE-001#S1` marks the acceptance test of that main path. It
  applies to a stakeholder requirement only; on an SwRS it is an error, because
  acceptance evidence is stakeholder evidence. Acceptance and tests are counted
  separately: a path can be tested, accepted, both, or neither.

The fast acceptance test,
`tests/test_acceptance_export.py::test_fast_export_selected_rows_for_offline_review`,
runs `src/export.py` with `sys.executable` through `subprocess` from a temporary
directory. It never imports the implementation: it writes a JSON list of rows,
runs the export as a separate process exactly as a user does, and reads
`report.csv` back with `csv.reader`. A test that imported `export_rows` would
prove the function works, not that the path a user walks works, and would hide a
broken command line or a report written somewhere unexpected.

The file also shows a second, slow acceptance variant for the same path, kept
entirely commented out with an inactive `# # @accepts_req StRS-CORE-001#S1`
marker. It is a future example of a costly test run in the main-branch pipeline,
not evidence: nothing implements it and the scanner cannot count it.
`test_commented_marker_does_not_count` removes the fast marker in a temporary
copy and proves both facts — the commented marker still counts for nothing, and
the "no acceptance test" warning comes back.

## Navigation and history

After editing requirements, run `okfreq lint examples/okfreq-examples/requirements`.
It refreshes the generated navigation blocks in `tiers/index.md`, each tier and
all requirement subdirectories. Use `--check` to verify freshness without writes.
Keep authored introductions outside the markers. Record substantive changes with
IDs, rationale and validation evidence in `requirements/tiers/log.md`; that file
is authored history and is never overwritten by lint.
