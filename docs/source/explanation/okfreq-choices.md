# Why `okfreq` is separate

`okfreq` is the requirements layer for `okf-schema`. It stores requirements as
OKF-compatible Markdown documents, but keeps them separate from `okfkb`, whose
purpose is recording and navigating knowledge. This gives each collection one
clear source of truth while reusing the same YAML and Markdown preservation
machinery.

The initial vocabulary follows the layered approach described by
[ISO/IEC/IEEE 29148](https://www.iso.org/standard/72089.html): `StRS` captures
stakeholder intent and use cases, while `SwRS` states implementable software
behavior. A software requirement derives from one or more stakeholder
requirements. This separation improves communication and makes change impact
visible without pretending that a stakeholder statement is already a design.

Authored fields such as `derives_from`, lifecycle, and verification intent are
kept distinct from generated fields such as reverse links and marker coverage.
Tools can therefore regenerate derived data without overwriting human context,
comments, unknown producer metadata, or the Markdown body. This is deliberately
compatible with the [OKF specification](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md)
and the [okf-schema documentation](../index.md).

The marker vocabulary defaults to `@implements_req` and `@tests_req`, matching
the terminology used by [Craftsman requirements traceability](https://github.com/gsemet/craftman-cli).
`okfreq` does not synchronize with Craftsman or `okfkb`; it only interoperates
through stable IDs and preserved metadata. Lifecycle changes are explicit so a
draft cannot silently become approved, and archive operations never delete a
document.

See the [setup guide](../how-to/okfreq-build-requirement-base.md) and the
[beginner tutorial](../tutorials/okfreq-traceability.md) for usage.
