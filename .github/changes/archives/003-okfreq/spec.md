# okfreq Requirements Layer Specification

## Request Context

Add a standalone `okfreq` requirements layer to `okf-schema`, alongside the existing
`okfkb` knowledge-base functionality. `okfreq` is an opinionated, ISO/IEC/IEEE
29148-like requirement layer using the `StRS` and `SwRS` vocabulary. It must provide
`okfreq init`, a dedicated minimal agent guideline, and a reusable command surface
comparable to `craftsman req`.

The implementation should reuse and move generally useful requirements functionality
into the `okf-schema` library rather than calling or synchronizing with Craftsman or
`okfkb`.

## Shared Understanding Summary

`okfreq` is a standalone, first-class requirements bundle managed by `okf-schema`. It
uses OKF-compatible Markdown files with YAML frontmatter. The implementation is
agent-first: agents should be able to retrieve, validate, trace, inspect, and safely
update requirements without losing human-authored content or producer-specific
metadata.

The initial built-in requirement levels are `StRS` and `SwRS`. The configuration and
common model should support additional generic hierarchy levels in the future, using
the same directional derivation conventions. `okfreq` may scan and update
traceability, but must interoperate with other tools that populate traceability
fields.

## Resolved Decisions

| ID | Topic | Resolution | Rationale |
|---:|---|---|---|
| 1 | Product boundary | `okfreq` is a standalone bundle. It does not call or synchronize with `okfkb`. | Prevents competing knowledge-base and requirements sources of truth. |
| 2 | Storage | Requirements are OKF-compatible Markdown documents with YAML frontmatter. | Reuses the existing parser, validator, formatter, and preservation guarantees. |
| 3 | Built-in levels | Ship `StRS` and `SwRS` semantics. | Preserves the requested vocabulary and close Craftsman compatibility. |
| 4 | Extensibility | Permit additional configured hierarchy levels using generic rules, without requiring tier-specific semantics in v1. | Supports future intermediate levels while keeping the initial contract focused. |
| 5 | Primary user | Coding agents. | Prioritizes reliable retrieval, validation, traceability, and safe mutation. |
| 6 | Common required metadata | Require `type`, `id`, `uuid`, `title`, `description`, `project`, `scope`, `lifecycle`, `origin`, and `tier`. | Gives agents stable identity and sufficient interpretation context. |
| 7 | UUID | Mandatory for native and imported/legacy requirements; generate it for new requirements. | Avoids identity ambiguity across sources. |
| 8 | Authored derivation | Use `derives_from` for human- or agent-managed links to higher-level requirements. | Makes the authoritative parent relationship explicit. |
| 9 | Computed reverse derivation | Use Craftsman-compatible `derived_by` for computed reverse links. | Supports intermediate levels and preserves existing terminology. |
| 10 | StRS/SwRS relationship | Native `SwRS` requirements require one or more `derives_from` `StRS` IDs. | Preserves a meaningful stakeholder-to-software requirement chain. |
| 11 | Dependencies | `depends_on` is authored metadata. | Dependencies are semantic inputs, not generated coverage. |
| 12 | Verification | Model a controlled verification method and optional verification criteria; verification is required before approval, not necessarily at draft creation. | Supports verifiability without blocking early drafting. |
| 13 | Coverage ownership | `implemented_in_files` and `tested_in_files` are generated/optional fields. | They may be maintained by `okfreq` or another tool and must not be required for creation. |
| 14 | External metadata | Preserve unknown frontmatter properties. | Supports producer-specific fields and interoperability. |
| 15 | Non-destructive formatting | Preserve YAML comments, quotes where possible, Markdown body text, and unknown fields. | Prevents agent/tool updates from destroying human context. |
| 16 | Ordinary command behavior | `validate`, `lint`, `index`, search, graph, and reporting are read-only by default. | Makes inspection safe for agents and CI. |
| 17 | Explicit generated updates | Update commands may modify only fields owned by `okfreq` as generated fields, using atomic writes and `--check`/`--diff` previews. | Separates authored content from derived state. |
| 18 | ID allocation | Use configurable, scope-aware, stable IDs; reject collisions; never automatically renumber existing IDs. | Keeps human-readable references durable. |
| 19 | Lifecycle values | Use `draft`, `proposed`, `approved`, `deprecated`, and `superseded`. | Prevents agents from treating all requirements as equally authoritative. |
| 20 | Lifecycle mutation | `archive` and `supersede` require explicit targets and confirmation. Archive must never delete. | Makes lifecycle changes deliberate and auditable. |
| 21 | Configuration | `okfreq init` creates or explicitly merges an `okfreq`-owned `.agents/requirements/config.yml`. | Centralizes hierarchy, IDs, lifecycle, scanning, and scope configuration. |
| 22 | Scope mapping | Store mappings under `scopes.<name>.source_dirs` and `scopes.<name>.test_dirs` in `config.yml`. | Preserves existing per-scope source/test semantics without a second mapping file. |
| 23 | Config migration | Support explicit import/merge; preserve unknown keys and report conflicts; never silently overwrite. | Allows reuse of Craftsman configuration without breaking it. |
| 24 | Markers | Default to `@implements_req ID` and `@tests_req ID`; support configured keywords and ID patterns. | Retains Craftsman-compatible defaults while supporting generic levels. |
| 25 | Non-leaf markers | Warn by default unless explicitly allowed. | Keeps implementation/test traceability focused on suitable requirement levels. |
| 26 | Lint strictness | Deterministic structural checks are errors; prose-quality heuristics are opt-in warnings with rule IDs. | Avoids fragile linguistic heuristics blocking agents. |
| 27 | Status/reporting | `status` gives a concise deterministic health summary. `generate-report` emits Markdown and JSON with separate metrics. | Makes reports useful to both humans and automation. |
| 28 | Command surface | Include `init`, `new`, `validate`, `lint`, `index`, `trace`, `in-file`, `status`, `scope`, `update-coverage`, `archive`, `supersede`, `graph`, and `generate-report`. | Provides reusable parity with Craftsman requirements functionality. |
| 29 | Excluded commands | Exclude project-specific `migrate-prd` and `create-from-proposed` from v1 unless a generic input contract is later defined. | Avoids embedding Craftsman-specific workflow assumptions. |
| 30 | Initialization | Generate a complete self-contained bundle: `_schema/`, tier folders, index/log files, config, and valid templates. Do not copy the agent guideline into the bundle. | Makes initialized bundles discoverable and usable without duplicating global guidance. |
| 31 | `new` behavior | Provide `new strs` and `new swrs`; generate UUID and stable ID; require authored metadata; require `derives_from` for native SwRS; do not invent coverage. | Ensures newly created documents are valid without fabricating evidence. |
| 32 | Imported requirements | Require identity including UUID; permit documented exemptions; keep imported content read-only by default; change it only through explicit import/migration commands. | Supports interoperability while protecting external source content. |
| 33 | Guideline location | Ship the specialized guideline separately in the repository/package; do not generate it inside initialized bundles. | Keeps project bundles small and prevents duplicated instructions. |
| 34 | Guideline scope | Keep it short and pointed: before editing / while editing / after editing, with pointers to config, schemas, and CLI help. | The guideline should direct agents, not duplicate the full specification. |
| 35 | Guideline prohibitions | Agents must not hand-edit generated fields, renumber IDs/UUIDs, drop unknown metadata/comments/body text, claim coverage without evidence, or change lifecycle/approval implicitly. | Prevents the highest-risk failure modes. |

## Proposed Domain Contract

### Requirement document

Each requirement is an OKF Markdown document with YAML frontmatter. The schema must
separate authored metadata from generated metadata.

Authored/common fields:

- `type`
- `id`
- `uuid`
- `title`
- `description`
- `project`
- `scope`
- `tier`
- `lifecycle`
- `origin`
- `depends_on`
- `verification_method`
- `verification_criteria`
- `derives_from` where required by hierarchy and lifecycle rules

Generated or externally maintained fields:

- `derived_by`
- `implemented_in_files`
- `tested_in_files`
- indexes and scope indexes
- coverage statistics
- generated reports

Unknown properties must be allowed and preserved where the applicable schema permits
them.

### Hierarchy

`StRS` and `SwRS` are built-in levels. Configured additional levels use the generic
hierarchy model:

- `derives_from`: authored links to requirements in a higher level
- `derived_by`: computed reverse links from lower-level requirements

`derived_by` is never treated as an authored source of truth and is regenerated only
by an explicit update operation.

### Lifecycle

The initial lifecycle vocabulary is:

- `draft`
- `proposed`
- `approved`
- `deprecated`
- `superseded`

Approval requires the configured verification information and all structural
validation needed by the selected policy. Lifecycle changes are explicit operations,
not side effects of formatting, indexing, coverage updates, or report generation.

### Traceability

The default marker syntax remains:

- `@implements_req <requirement-id>`
- `@tests_req <requirement-id>`

The scanner must support configured marker keywords and configured ID patterns. It
must not remain hard-coded to `SwRS-`. Marker results should distinguish implementation
and test references, missing IDs, duplicate/unexpected references, unsupported
non-leaf references, and scan warnings.

`update-coverage` is explicit. It may update only `okfreq`-owned generated fields,
preserve all authored and unknown metadata, preserve comments and body content, and
write atomically. It should provide preview modes such as `--check` and `--diff`.

## Documentation Contract

The implementation must document the `okfreq` feature in the Sphinx documentation.
The documentation is part of the product contract and must be included in the
documentation navigation and cross-linked from the relevant `okfreq` pages.

### Design explanation

Add the exact page:

```text
docs/source/explanation/okfreq-choices.md
```

This page must explain the design choices and trade-offs behind `okfreq`, including
why requirements are kept separate from `okfkb`, why the bundle uses layered
requirements, how `StRS` and `SwRS` relate, and why authored and generated metadata
are separated. It should explain the consequences of the lifecycle, traceability,
non-destructive editing, and interoperability decisions rather than merely restating
the CLI contract.

The page must include references to:

- ISO/IEC/IEEE 29148;
- the OKF and `okf-schema` documentation/specification;
- the Craftsman requirements documentation, where compatibility or terminology is
  discussed; and
- any other external standard or tool documentation relied upon by the design.

References must be usable hyperlinks, with enough surrounding context for a reader to
understand why each source is relevant.

### Direct how-to guide

Add a task-oriented guide at:

```text
docs/source/how-to/build-requirement-base.md
```

The guide must provide a direct, step-by-step path for a developer to:

1. set up a requirement base in a project;
2. initialize and configure `okfreq`;
3. create and edit requirements safely;
4. run local preflight validation; and
5. enable the corresponding CI validation.

The guide should stay procedural and concise. Detailed explanation of requirements,
traceability concepts, layering, and rationale belongs in the tutorial below rather
than being duplicated in the how-to guide. The guide must link to the explanation,
tutorial, reference material, and relevant command documentation.

### Beginner tutorial

Add a tutorial at:

```text
docs/source/tutorials/requirements-traceability.md
```

The tutorial must teach a developer who has never performed requirements traceability.
It must begin with the general concept of a requirement and progressively explain:

- what a requirement is and what makes one useful and verifiable;
- how requirements move from user intent to implementation and verification;
- why traceability matters for communication, change impact, evidence, and regression
  prevention;
- how requirements are tracked in source code and tests using `okfreq` markers;
- how the examples work in both Python and Rust;
- why requirements are organized into layers;
- `StRS` as a stakeholder-level/use-case statement describing something the user can
  follow or accomplish; and
- `SwRS` as the software-level statement describing behavior that can be implemented
  and tested.

The tutorial must show the relationship from an `StRS` use case to one or more `SwRS`
requirements, then to implementation markers and test markers. It must explain why
the layers are useful, what each layer must and must not contain, and how a reader can
follow the chain when a requirement changes. Examples must use realistic but small
Python and Rust source/test files and must not imply coverage that is not supported by
the shown markers or validation output.

For every image intended for the tutorial or the related `okfreq` documentation, add
an image-generation prompt beside the target image at the same path. The prompt file
must clearly state the intended audience, concepts to depict, labels, relationships,
visual constraints, and accessibility requirements. Prompts are authoring inputs only:
they will be executed manually later and must not require an image-generation service
as part of the build or CI process. The specification should define image targets and
their adjacent prompt files together, for example:

```text
docs/source/_static/okfreq-traceability-overview.svg
docs/source/_static/okfreq-traceability-overview.prompt.md
```

The final image set must include, at minimum, an overview of the requirement
traceability chain and a layered `StRS`-to-`SwRS` explanation. Any additional images
must follow the same adjacent-prompt convention. Images must have meaningful alt text
and must be referenced by the documentation.

The tutorial, how-to guide, and explanation page must be added to the Sphinx toctree
and must cross-link to one another. Documentation acceptance includes successful
Sphinx documentation generation, valid links where the project checks them, and
reviewable references and image prompts committed alongside the documentation.

## Configuration Contract

`okfreq init` creates or explicitly merges:

```text
.agents/requirements/config.yml
```

The configuration should include, at minimum:

- configuration/schema version
- hierarchy levels and folders
- tier labels and link verbs
- ID prefixes and allocation policy
- lifecycle values and transition policy
- source/test scan settings
- marker keywords and ID patterns
- generated-field ownership
- per-scope mappings:
  - `source_dirs`
  - `test_dirs`

Existing configuration must not be silently overwritten. Explicit import/merge mode
must preserve unknown keys, map compatible Craftsman fields, report conflicts, and
make precedence visible. Scope mappings must not be flattened in a way that loses
scope-specific source/test ownership.

## CLI Contract

The v1 command family is intended to expose reusable equivalents for:

- `okfreq init`
- `okfreq new strs`
- `okfreq new swrs`
- `okfreq validate`
- `okfreq lint`
- `okfreq index`
- `okfreq trace`
- `okfreq in-file`
- `okfreq status`
- `okfreq scope`
- `okfreq update-coverage`
- `okfreq archive`
- `okfreq supersede`
- `okfreq graph`
- `okfreq generate-report`

Commands that inspect, validate, index, or report are read-only unless an explicit
mutation option is supplied. Lifecycle commands require explicit targets and
confirmation. Archive never deletes content.

Project-specific PRD migration and proposed-change conversion are not part of the
initial generic contract.

## Specialized Agent Guideline Requirements

The guideline is shipped separately from initialized bundles. It should contain only:

1. Read the project-local `config.yml` and applicable schemas before editing.
2. Use `okfreq` commands for creation, validation, indexing, traceability, and lifecycle changes.
3. Preserve comments, Markdown body content, unknown frontmatter, IDs, and UUIDs.
4. Run validation/lint after changes and use preview modes before generated updates.
5. Treat draft/proposed/approved lifecycle values distinctly.

It must explicitly prohibit:

- hand-editing `derived_by`, coverage fields, indexes, or reports;
- changing or renumbering existing IDs and UUIDs;
- dropping unknown frontmatter, comments, or body text;
- claiming implementation/test coverage without markers or evidence;
- changing lifecycle or approval state as an incidental edit.

The guideline should point to the authoritative configuration, schemas, and
`okfreq --help` rather than duplicating field definitions or command details.

## Acceptance Boundaries

The implementation is successful only if it demonstrates that:

- `okfreq init` creates a valid standalone bundle without depending on `okfkb`;
- initialized requirements validate against bundled schemas;
- `new strs` and `new swrs` create valid documents with UUIDs and stable IDs;
- native SwRS derivation is enforced;
- generic configured hierarchy levels support authored `derives_from` and computed
  `derived_by`;
- comments, quotes, body content, and unknown properties survive formatting and
  coverage updates;
- IDs are collision-safe and are never automatically renumbered;
- validation/linting catches deterministic structural and graph errors;
- optional prose heuristics are warnings and do not fail default structural checks;
- configurable markers support non-SwRS IDs and scope-aware scanning;
- coverage updates are explicit, atomic, previewable, and preserve authored data;
- lifecycle commands are explicit, confirmed, and non-destructive;
- status and reports separate schema health, structural traceability, marker coverage,
  lifecycle counts, and other metrics;
- explicit config import/merge preserves unknown keys and reports conflicts;
- the specialized guideline is concise, separately shipped, and points to authority;
- the complete behavior is covered by focused unit and integration tests and documented
  in the `okf-schema` project;
- `docs/source/explanation/okfreq-choices.md` documents the design rationale and
  references ISO/IEC/IEEE 29148, OKF/`okf-schema`, Craftsman, and other relied-upon
  sources;
- `docs/source/how-to/build-requirement-base.md` gives a direct step-by-step setup,
  configuration, editing, local preflight, and CI workflow without duplicating the
  tutorial's conceptual teaching;
- `docs/source/tutorials/requirements-traceability.md` teaches requirements and
  traceability to a beginner, including the `StRS` use-case layer, the testable `SwRS`
  layer, source/test markers, rationale for layering, and Python and Rust examples;
- every tutorial image has an adjacent image-generation prompt at the same path,
  meaningful alt text, and documentation references; and
- all three documentation pages are included in the Sphinx navigation and cross-link
  to the relevant explanation, how-to, reference, and tutorial pages.

## Remaining Implementation-Level Decisions

The interview resolved the product direction but intentionally left detailed contracts
for implementation/specification work:

- exact JSON Schema property types, patterns, and conditional requirements;
- exact configuration YAML shape and merge precedence;
- exact ID format and allocator behavior for custom scopes and levels;
- exact lifecycle transition matrix;
- exact CLI option names, output formats, exit codes, and confirmation behavior;
- exact imported-requirement exemption model;
- exact report schemas and generated-field ownership metadata;
- exact guideline filename, frontmatter, and installation/distribution mechanism.
