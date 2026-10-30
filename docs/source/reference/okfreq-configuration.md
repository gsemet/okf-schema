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
├── guidelines/                requirements.guidelines.md (installed by `okfreq init`,
│                              replaced by `--force`) and your own project guideline files
└── tiers/
    ├── _schema/base.schema.yaml
    ├── _schema/strs.schema.yaml
    ├── _schema/swrs.schema.yaml
    ├── index.md               generated navigation block + authored introduction
    ├── log.md                 authored dated change history
    ├── strs/                  stakeholder requirements
    └── swrs/                  software requirements

  Generated reports are written to `dist/requirements-report.json`,
  `dist/requirements-report.schema.json`, and `dist/requirements-report.md` by
  the project workflow. They are build artifacts, not requirements-bundle content.
```

For the rationale behind these linkage-based coverage values and the current
absence of test execution results, see [What `okfreq` coverage really
means](../explanation/okfreq-coverage-boundaries.md).

Every `okfreq` command accepts either the project root or the bundle root and
resolves `config.yml` itself. The `tiers.<tier>.folder` values are relative to
`tiers/`. A scope's optional `folder` is relative to its tier folder, while
`source_dirs` and `test_dirs` are relative to the project root.

```yaml
version: 1
tiers:
  StRS: {folder: strs, prefix: StRS, derives_from: [], approval_lock: true,
    owner_email: product-owner@example.org}
  SwRS: {folder: swrs, prefix: SwRS, derives_from: [StRS], approval_lock: false}
id_policy: scope-prefix-sequence
strs_test_coverage_mode: linked-swrs
lifecycle:
  field: req_lifecycle
markers:
  implements: '@implements_req'
  tests: '@tests_req'
  id_pattern: '[A-Za-z][A-Za-z0-9_-]*'
generated_fields: [derived_by, supersedes, implemented_in_files, tested_in_files,
  default_owner_email, status, verified]
retired_ids: []
scopes:
  core: {id_token: CORE, folder: core, source_dirs: [src], test_dirs: [tests]}
  payments:
    id_token: PAY
    folder: payments
    source_dirs: [src/payments]
    test_dirs: [tests/payments]
    owner_email: payments-lead@example.org
    tiers:
      SwRS: {approval_lock: true}
```

## Settings

| Key | Role |
|---|---|
| `version` | Configuration contract version. |
| `tiers` | Maps each tier to its document folder, ID prefix, allowed parent tiers, `approval_lock` and optional `owner_email` (see {ref}`okfreq-ownership-and-approval`). Additional tiers use the same generic derivation rules. Configurations written before 0.16.0 use the key `levels`, which is still read; a file must not declare both. |
| `id_policy` | Allocation strategy. `scope-prefix-sequence` is currently supported; `okfreq new` rejects unsupported values. Existing documents are never renumbered. |
| `strs_test_coverage_mode` | StRS test-coverage rule. Choose `linked-swrs` or `linked-swrs-and-validation-test`; the default is `linked-swrs`. |
| `lifecycle.field` | Frontmatter field that holds the lifecycle state, `req_lifecycle` by default, so it never collides with the OKF `status` that okfreq generates from it. The accepted values are the `enum` of that field in `tiers/_schema/base.schema.yaml`; their meanings are in {ref}`okfreq-lifecycle-states`. A schema you write by hand must use the same name for the property and its `required` entry; `okfreq init` always generates `req_lifecycle`, with its `x-okf-status-projection` mapping, because it runs before you can edit `config.yml`. A legacy `lifecycle.values` list is still read and takes precedence over the schema. |
| `markers` | Implementation/test marker keywords and the regular expression used to recognise IDs. The entire match is the requirement ID. |
| `generated_fields` | Fields `update-coverage` may regenerate. Supported values are `derived_by`, `supersedes`, `implemented_in_files`, `tested_in_files`, `default_owner_email`, `status` and `verified` (see {ref}`okfreq-okf-projection`); unsupported values fail explicitly. A configuration that lists the fields explicitly keeps that list: add `supersedes` to maintain the backlink of `superseded_by`, and `default_owner_email` to write each requirement's configured owner. |
| `retired_ids` | IDs that were deleted with `okfreq retire` and must never be allocated again. Optional list of ID strings, written by `okfreq retire`; `okfreq new` numbers after the highest of the existing and retired IDs, `okfreq validate` rejects a document with a listed ID, and `okfreq import`/`config-merge` take the union of both lists. |
| `scopes` | Per-scope ID token, requirement subfolder, source/test ownership, and optional ownership overrides (`owner_email`, `tiers.<tier>.approval_lock`, `tiers.<tier>.owner_email`). Keep `source_dirs` and `test_dirs` separate. |

A scope entry may name individual files as well as directories, and it may point
at non-Python deliverables. When a requirement is satisfied by shipped prompt or
data content rather than by executable code, add that location to the scope and
place the marker in the file itself instead of forcing a misleading code marker.

### StRS test-coverage modes

The configured mode affects only the stakeholder-level test coverage shown in
generated reports. It does not change SwRS source coverage or SwRS test-link
coverage.

With the default mode:

```yaml
strs_test_coverage_mode: linked-swrs
```

an StRS is covered when it derives at least one SwRS and every linked SwRS has a
configured `@tests_req` marker. With the stricter mode:

```yaml
strs_test_coverage_mode: linked-swrs-and-validation-test
```

the same linked-SwRS rule must be satisfied and at least one configured test
file must directly define a validation test for the StRS:

```python
# @tests_req StRS-CORE-001
```

The marker establishes that a validation test is defined. `okfreq` does not
parse test-runner results, so it cannot infer whether that test executed or
passed. StRS source coverage is not computed; StRS requirements are reported
in a separate stakeholder table without a source column.

Set `id_token` when the identifier spelling differs from the frontmatter scope
name, such as `scope: core` with `id_token: CORE`. Set `folder` to group newly
created requirements below their configured tier, producing paths such as
`tiers/swrs/core/SwRS-PROJECT-CORE-001.md`. Both settings are optional; without
them, `okfreq new` preserves the supplied scope token and writes directly into
the tier folder for backward compatibility.

(okfreq-ownership-and-approval)=

## Ownership and approval

Some requirements must not change without their owner's agreement. Two settings
describe this, per tier and optionally per scope:

- `approval_lock`: whether a requirement of this tier may be `approved`, that is,
  frozen by its owner. `okfreq init` writes `true` for StRS and `false` for SwRS, so
  the policy is visible. When it is absent or `null`, a top tier (no
  `derives_from`) is lockable and a derived tier is not.
- `owner_email`: who approves the requirements of this tier, and any change to
  them once approved.

A scope can belong to someone else, or need a different policy. Each value is
resolved from the first place that sets it:

1. `scopes.<scope>.tiers.<tier>.approval_lock` or `.owner_email`, where `null` counts
   as unset;
2. `scopes.<scope>.owner_email` (the owner only; there is no scope-wide lock);
3. `tiers.<tier>.approval_lock` or `.owner_email`.

In the example above, every StRS is lockable and owned by
`product-owner@example.org`; the `payments` scope is owned by
`payments-lead@example.org`, and its SwRS are lockable too, which is rare.

With `default_owner_email` in `generated_fields`, `okfreq update-coverage` writes
the resolved owner into each requirement and removes the field once no owner
applies. Without it in `generated_fields`, `default_owner_email` is not maintained:
`update-coverage` neither writes nor removes it. A requirement can name a different
owner with the authored field `owner_email`, which replaces `default_owner_email`.

`okfreq validate` and `okfreq lint` fail on an `approved` requirement when:

- the resolved `approval_lock` is `false`: keep it `proposed`, or ask the owner to
  enable the lock for that tier or scope;
- `approved_by` or `approved_at` is missing, or `approved_at` is not an ISO 8601 datetime with a UTC offset. The message tells a coding agent that
  approval is the owner's decision. If the owner agreed (for example during
  planning), the agent records the owner's email and today's date, then requests
  the owner's review of the file on the pull or merge request; otherwise it
  restores the previous state.

okfreq cannot see who agreed: it checks that the agreement is recorded. Make the
recorded agreement binding with a review rule on the requirement files, such as a
`CODEOWNERS` entry naming the owner, so the merge waits for the owner's approval.
A malformed `approval_lock` (not a boolean) or `owner_email` (not an email
address) is reported with its dotted path in `config.yml`.

## Merging configuration

Configuration changes must be explicit. Use `okfreq config-merge FILE --path .`
to merge a compatible source configuration. Existing values are retained when
they conflict; conflicts are reported so the caller can decide what to change.
Unknown keys are preserved. This allows producer-specific metadata and future
settings without losing information.

For compatibility with configurations written before 0.16.0, a legacy `levels`
key is renamed `tiers` on both sides before merging. A legacy `lifecycle.values`
list is not imported into a configuration that names `lifecycle.field`; it is
reported as the conflict `lifecycle.values`.

Do not flatten scope mappings into one global source/test list. Scope ownership
is part of traceability evidence. Review the result with `okfreq scope .` and
validate it with `okfreq validate .`.

## Extending tiers and fields

Add a tier under `tiers` with a unique folder and prefix. For example, an
architecture tier could derive from `StRS` and be a parent of `SwRS`. Authored
links use `derives_from`; reverse `derived_by` links are computed. Replacement
links follow the same direction: `superseded_by` is authored and `supersedes` is
computed, while `relates_to` is authored only.

Requirement documents may contain additional frontmatter fields because the
schema allows unknown properties. Add fields such as `team`, `safety_goal`, or
`external_reference` without changing the common identity fields. Preserve
unknown fields during generated updates and document any external ownership.

See the [`okfreq` frontmatter reference](okfreq-frontmatter.md) and the
[traceability tutorial](../tutorials/okfreq-traceability.md).
