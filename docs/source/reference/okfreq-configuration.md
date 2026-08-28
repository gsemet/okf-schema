# `okfreq` configuration reference

The project-owned configuration is `config.yml` at the root of the requirements
bundle: `requirements/config.yml` in this repository, or
`.agents/requirements/config.yml` in a project initialized by `okfreq init`. It
defines the hierarchy, identifiers, lifecycle policy, scanning conventions, and
generated-field ownership. `okfreq init` creates a conservative default. Each
requirement type selects the schema with the matching filename: `type: StRS`
uses `strs.schema.yaml`, while `type: SwRS` uses `swrs.schema.yaml`. Both tier
schemas extend `base.schema.yaml`.

The bundle is split into a control layer and a document layer:

```text
requirements/
├── config.yml                 configuration (this reference)
├── guidelines/                agent guidance installed by `okfreq init`
└── tiers/
    ├── _schema/base.schema.yaml
    ├── _schema/strs.schema.yaml
    ├── _schema/swrs.schema.yaml
    ├── index.md
    ├── log.md
    ├── strs/                  stakeholder requirements
    └── swrs/                  software requirements

  Generated reports are written to `dist/requirements-report.json`,
  `dist/requirements-report.schema.json`, and `dist/requirements-report.md` by
  the project workflow. They are build artifacts, not requirements-bundle content.
```

Every `okfreq` command accepts either the project root or the bundle root and
resolves `config.yml` itself. The `levels[].folder` values are relative to
`tiers/`. A scope's optional `folder` is relative to its level folder, while
`source_dirs` and `test_dirs` are relative to the project root.

```yaml
version: 1
levels:
  StRS: {folder: strs, prefix: StRS, derives_from: []}
  SwRS: {folder: swrs, prefix: SwRS, derives_from: [StRS]}
id_policy: scope-prefix-sequence
lifecycle:
  values: [draft, proposed, approved, deprecated, superseded]
markers:
  implements: '@implements_req'
  tests: '@tests_req'
  id_pattern: '[A-Za-z][A-Za-z0-9_-]*'
generated_fields: [derived_by, implemented_in_files, tested_in_files]
scopes:
  core: {id_token: CORE, folder: core, source_dirs: [src], test_dirs: [tests]}
```

## Settings

| Key | Role |
|---|---|
| `version` | Configuration contract version. |
| `levels` | Maps each level to its document folder, ID prefix, and allowed parent levels. Additional levels use the same generic derivation rules. |
| `id_policy` | Allocation strategy. `scope-prefix-sequence` is currently supported; `okfreq new` rejects unsupported values. Existing documents are never renumbered. |
| `lifecycle.values` | Allowed lifecycle values. The built-in values distinguish draft, proposed, approved, deprecated, and superseded requirements. |
| `markers` | Implementation/test marker keywords and the regular expression used to recognise IDs. Use a pattern with an `id` named group, or make the entire match the ID. |
| `generated_fields` | Fields `update-coverage` may regenerate. Supported values are `derived_by`, `implemented_in_files`, and `tested_in_files`; unsupported values fail explicitly. |
| `scopes` | Per-scope ID token, requirement subfolder, and source/test ownership. Keep `source_dirs` and `test_dirs` separate. |

A scope entry may name individual files as well as directories, and it may point
at non-Python deliverables. When a requirement is satisfied by shipped prompt or
data content rather than by executable code, add that location to the scope and
place the marker in the file itself instead of forcing a misleading code marker.

Set `id_token` when the identifier spelling differs from the frontmatter scope
name, such as `scope: core` with `id_token: CORE`. Set `folder` to group newly
created requirements below their configured level, producing paths such as
`tiers/swrs/core/SwRS-PROJECT-CORE-001.md`. Both settings are optional; without
them, `okfreq new` preserves the supplied scope token and writes directly into
the level folder for backward compatibility.

## Merging configuration

Configuration changes must be explicit. Use `okfreq config-merge FILE --path .`
to merge a compatible source configuration. Existing values are retained when
they conflict; conflicts are reported so the caller can decide what to change.
Unknown keys are preserved. This allows producer-specific metadata and future
settings without losing information.

Do not flatten scope mappings into one global source/test list. Scope ownership
is part of traceability evidence. Review the result with `okfreq scope .` and
validate it with `okfreq validate .`.

## Extending levels and fields

Add a level under `levels` with a unique folder and prefix. For example, an
architecture level could derive from `StRS` and be a parent of `SwRS`. Authored
links use `derives_from`; reverse `derived_by` links are computed.

Requirement documents may contain additional frontmatter fields because the
schema allows unknown properties. Add fields such as `owner`, `safety_goal`, or
`external_reference` without changing the common identity fields. Preserve
unknown fields during generated updates and document any external ownership.

See the [`okfreq` frontmatter reference](okfreq-frontmatter.md) and the
[traceability tutorial](../tutorials/okfreq-traceability.md).
