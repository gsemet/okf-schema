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
- both StRS coverage policies, including a direct stakeholder validation marker;
- conflict-preserving config merge and preservation of unknown authored fields;
- all five file-resolution modes, wikilink labels/fragments, E10 failures and W15 skips;
- index/search/in-file/scope/graph/trace/status and schema-validated JSON reports;
- explicit exemptions, confirmed archive/supersede and preserved UUIDs/bodies;
- a missing-ID failure followed by repaired validation.

Its marker fixtures demonstrate scanning, not execution of shipping software.
Its tracker reference is fictional demo data. All intentional failures and
lifecycle changes stay temporary; the checked-in requirements are preserved.
The Python CSV tests provide actual executable behavior evidence separately.

For the live project's feature/evidence map, read
[How this project exercises okfreq](../../docs/source/explanation/project-feature-coverage.md).

## Navigation and history

After editing requirements, run `okfreq lint examples/okfreq-examples/requirements`.
It refreshes the generated navigation blocks in `tiers/index.md`, each tier and
all requirement subdirectories. Use `--check` to verify freshness without writes.
Keep authored introductions outside the markers. Record substantive changes with
IDs, rationale and validation evidence in `requirements/tiers/log.md`; that file
is authored history and is never overwritten by lint.
