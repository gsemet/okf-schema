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

This example runs in `linked-swrs-and-acceptance-paths` mode. It includes one
stakeholder requirement (`StRS-CORE-001`) with one declared main path (`S1`:
*Export selected rows for offline review*), one Python software requirement
(`SwRS-CORE-001`, covering the Python CSV writer), and one Rust software
requirement (`SwRS-CORE-002`, covering a Rust CSV row formatter).

Here, a software requirement (`SwRS`) is simply a promise about observable
software behavior. `SwRS-CORE-001` says that the service writes CSV output, and
`SwRS-CORE-002` says that its Rust formatter returns a CSV row. A requirement is
not the implementation and it is not the test; it is the contract that the
code and test are expected to satisfy.

This example uses two test verbs with `#S<n>` fragments:

- `@tests_req` marks unit/component verification of declared transitions on
  `SwRS-CORE-001#S1`/`#S2` (`tests/test_export.py`) and `SwRS-CORE-002#S1`/`#S2`
  (`tests/rust_export_test.rs`), and marks the cheap in-process test of the
  stakeholder path (`StRS-CORE-001#S1`) in `tests/test_export.py::test_export_rows`.
- `@accepts_req StRS-CORE-001#S1` marks the end-to-end acceptance test in
  `tests/test_acceptance_export.py`, which runs `src/export.py` as a separate
  process from a temporary working directory and reads the generated CSV back
  from disk — matching how a user runs the export rather than calling an
  in-process helper.
- The commented-out slow acceptance variant in `tests/test_acceptance_export.py`
  (`# # @accepts_req StRS-CORE-001#S1`) is only an illustrative future example:
  it is not collected by pytest and is not counted as evidence.

That is why this example contains a few different kinds of files: together
they show the path from the original need to the requirement, implementation,
test evidence, acceptance evidence, and traceability report.

## Pointers

- [Requirements bundle](requirements/)
- [Stakeholder requirement](requirements/tiers/strs/StRS-CORE-001.md)
- [Python software requirement](requirements/tiers/swrs/SwRS-CORE-001.md)
- [Rust software requirement](requirements/tiers/swrs/SwRS-CORE-002.md)
- [Implementation](src/export.py)
- [Unit tests](tests/test_export.py)
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

The first command regenerates the CSV requirements, runs the Python CSV tests,
refreshes source/test evidence and validates file targets before writing JSON,
JSON Schema and Markdown reports under this example's `dist/`. Rust source and
test markers demonstrate linkage; this command does not run a Rust compiler.

The showcase creates a temporary shipping-manifest project and verifies:

- scoped IDs/folders, custom markers, authored dependencies and external demo metadata;
- all three StRS coverage modes (`linked-swrs`, `linked-swrs-and-validation-test`, and
  `linked-swrs-and-acceptance-paths` with declared `scenarios:`, `#S<n>` fragments,
  custom `@accepts` markers, independent `tested`/`accepted` counters, and the
  `acceptance_paths` outcome);
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
The Python CSV unit tests (`tests/test_export.py`) and end-to-end acceptance
test (`tests/test_acceptance_export.py`) provide actual executable behavior
evidence separately.

For the live project's feature/evidence map, read
[How this project exercises okfreq](../../docs/source/explanation/project-feature-coverage.md).

## Navigation and history

After editing requirements, run `okfreq lint examples/okfreq-examples/requirements`.
It refreshes the generated navigation blocks in `tiers/index.md`, each tier and
all requirement subdirectories. Use `--check` to verify freshness without writes.
Keep authored introductions outside the markers. Record substantive changes with
IDs, rationale and validation evidence in `requirements/tiers/log.md`; that file
is authored history and is never overwritten by lint.
