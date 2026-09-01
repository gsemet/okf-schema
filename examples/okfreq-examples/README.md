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
