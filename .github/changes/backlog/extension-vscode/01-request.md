# Change Request - VS Code navigation for schema-defined OKF fields

**Status**: Initial input requirements capture. Implementation and the full
specification are deferred.
**Date**: 2026-09-01

## Need

Provide an installable VS Code extension for navigating OKF and OKFKB Markdown
frontmatter. The extension must understand the bundle's schemas and use
schema-declared field semantics instead of hard-coding knowledge of fields such
as `derives_to`.

For example, in
`examples/okfkb-hw-knowledge-base/findings/2026.07.04-21.35-hw-failure-investigation.md`,
the `derives_to` values identify other documents in the bundle. The corresponding
schema should be able to annotate that property as a list of links to bundle
documents. The same mechanism must work for any frontmatter property carrying
the annotation.

## Existing implementation context

- A document's frontmatter `type` selects its concrete schema from the bundle's
  `_schema` directory.
- Concrete schemas commonly inherit shared properties through `allOf` and
  `$ref`, including the link-shaped fields in `Base.schema.yaml`.
- Link semantics are currently expressed only in descriptions. For example,
  `derives_to` is an array of canonical, bundle-relative, extensionless
  document paths.
- The current `okf-schema` CLI has no `install-extension` command. This request
  introduces the future command surface:
  `okf-schema install-extension --vscode`.

## Initial input requirements

### Schema annotations

- A schema author can attach a namespaced annotation beginning with
  `x-okf-schema-` to a property definition.
- The annotation declares that the property's values have a semantic role,
  initially including links to other Markdown documents in the same bundle.
- The extension interprets the annotation generically for every schema field;
  it must not contain a field-name-specific rule for `derives_to`.
- The exact annotation key set and value structure remain open for the full
  specification. The design should leave room for target kind, cardinality,
  path resolution, and nested-value semantics.

### Schema and bundle discovery

- The initial scope is bundle-local. The extension discovers the current or
  nearest OKF bundle and its `_schema` directory.
- It resolves the document's concrete schema from frontmatter `type` and
  follows the local schema `$ref` and inheritance graph.
- The initial contract covers Markdown documents with YAML frontmatter.
- The behavior when a workspace contains multiple possible bundle roots, and
  whether an explicit VS Code setting can override discovery, remains open.

### Editor navigation

- A frontmatter field can be associated with its schema property definition and
  schema description, providing a schema navigation or inspection affordance.
- A value in an annotated link field can be navigated with the normal VS Code
  definition workflow to the referenced bundle document.
- Navigation works for a single scalar target, arrays of targets, and link
  values nested inside supported objects or arrays of objects.
- The first request does not require completion or diagnostics unless the full
  specification later includes them.

### Link model

- The initial target model is bundle-relative Markdown document IDs or paths,
  following the existing OKFKB convention of canonical extensionless paths.
- Targets are resolved relative to the bundle root and must not require access
  to a live system or external service.
- URLs and files outside the current bundle are not part of the initial
  contract; their treatment remains a later decision.

### Distribution and installation

- The VS Code extension source and its distributable assets live under
  `src/okf_schema/extensions/vscode/`.
- The assets are included in the Python wheel and sdist.
- Runtime access to packaged extension files uses `importlib.resources`, so the
  installer does not depend on a source checkout or a repository-relative path.
- `okf-schema install-extension --vscode` installs the complete extension as a
  VS Code-installable VSIX for the current user environment.
- The extension runtime architecture (native JavaScript/TypeScript extension,
  LSP server, or a combination) is intentionally left for the full
  specification.

## Later specification decisions

- Exact `x-okf-schema-...` annotation names, values, and validation rules.
- How schema property locations are surfaced when a property comes through
  multiple `$ref` or `allOf` layers.
- Bundle-root discovery precedence and explicit workspace configuration.
- Canonical path normalization, including compatibility with values ending in
  `.md`.
- VSIX build toolchain, VS Code engine/API compatibility, activation behavior,
  and failure messages from the installer.
- Whether hover, completion, unresolved-target diagnostics, or schema
  validation are included beyond the initial navigation behavior.
