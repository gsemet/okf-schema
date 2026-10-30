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
(using `okfreq update-coverage` command) such as reverse links (`derived_by`),
marker coverage (`implemented_in_files`, `tested_in_files`)
and the configured owner (`default_owner_email`).
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
and archive operations never delete a document. Only `okfreq retire` deletes,
and only a never-published draft; it records the ID so its number is never
allocated again.

## Why requirements are proposed by default, and approved by their owner

In a project where agents deliver the code and its requirements together, a
requirement is an output of the change, not a plan for a later one. It is
implemented when it lands, so it starts `proposed`, and it keeps evolving with the
code through ordinary planning and review. `draft` remains for a requirement
written ahead of its implementation; on a default branch it signals a gap.

Some requirements must stop moving: the stakeholder outcomes a product owner has
committed to, or the software behaviour of a scope another team owns. `approved`
freezes them. Locking is configured per tier and per scope, not per document,
because the policy follows who owns what: StRS are lockable by default and SwRS
are not, and a scope can name its own owner or lock its SwRS too.

okfreq cannot witness an agreement given in a planning meeting. It therefore
checks only that the agreement is recorded (`approved_by`, `approved_at`), and
its error message tells an agent what to do: record the agreement it was given,
then ask the owner to review the file. The forge enforces the rest, for example a
`CODEOWNERS` rule that blocks the merge until the owner approves.

See the [setup guide](../how-to/okfreq-build-requirement-base.md) and the
[beginner tutorial](../tutorials/okfreq-traceability.md) for usage.
