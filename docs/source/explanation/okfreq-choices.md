# `okfreq` Design Choices

`okfreq` is a requirements layer built using `okf-schema`.
It stores requirements as OKF-compatible Markdown documents,
but keeps them separate from `okfkb`,
whose purpose is recording and navigating knowledge.

The initial vocabulary follows the layered approach described by
[ISO/IEC/IEEE 29148](https://www.iso.org/standard/72089.html):
`StRS` captures stakeholder intent and use cases,
while `SwRS` states implementable software behavior.
A software requirement derives from one or more stakeholder requirements.

This separation improves communication
and makes user-level change impact (`StRS`) clearly visible
and separated from testable software change (`SwRS`).

Authored fields such as `derives_from`, lifecycle, and verification intent are
kept distinct from automatically generated fields
(using `okfreq lint` command) such as reverse links (`derived_from`)
and marker coverage (`implemented_in_files`, `tested_in_files`).
This allows agents (and tools) to navigate back and forth more easily
without the need of an external parser or LSP (Language Server Protocal) server.

This clearly separate the metadata from the main content,
allowing to declare links and maturity information
without overwriting human context, comments.
This is deliberately compatible with the [OKF specification](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md)
and the [okf-schema documentation](../index.md).

The in-source and in-tests marker vocabulary defaults
to `@implements_req` and `@tests_req`.
`okfreq` only interoperates through stable IDs and preserved metadata.
Lifecycle changes are explicit so a draft cannot silently become approved,
and archive operations never delete a document.

See the [setup guide](../how-to/okfreq-build-requirement-base.md) and the
[beginner tutorial](../tutorials/okfreq-traceability.md) for usage.
