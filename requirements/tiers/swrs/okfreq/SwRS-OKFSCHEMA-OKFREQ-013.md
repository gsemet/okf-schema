---
type: SwRS
id: SwRS-OKFSCHEMA-OKFREQ-013
uuid: 154e57ca-1275-4960-880c-4d5439ac2875
title: Resolve requirement ownership and guard approvals
description: When requirements are validated or regenerated, okfreq SHALL read
  tiers (or the legacy levels key) and the lifecycle field from configuration,
  take the accepted lifecycle values from the base schema, generate
  default_owner_email from the tier and scope owner settings, and reject an
  approved requirement whose tier and scope do not allow approval or that lacks
  approved_by and approved_at, with a message telling a coding agent to obtain
  and record the owner's agreement.
project: okf-schema
scope: okfreq
req_lifecycle: proposed
status: stable
origin: native
tier: SwRS
derives_from:
- StRS-OKFSCHEMA-OKFREQ-001
annotation_exemption: false
exemption_reason:
derived_by: []
implemented_in_files:
- src/okf_schema/okfreq/core.py
tested_in_files:
- tests/test_okfreq.py
default_owner_email: gaetan@xeberon.net
---

## Resolve requirement ownership and guard approvals

### Normative behavior

When requirements are validated or regenerated, okfreq SHALL read tiers (or the legacy levels key) and the lifecycle field from configuration, take the accepted lifecycle values from the base schema, generate default_owner_email from the tier and scope owner settings, and reject an approved requirement whose tier and scope do not allow approval or that lacks approved_by and approved_at, with a message telling a coding agent to obtain and record the owner's agreement.

### Scenario: Read the new and the legacy configuration names

- GIVEN a `config.yml` with `tiers` and `lifecycle.field`, or the legacy `levels`
  and `lifecycle.values`
- WHEN any okfreq command loads it
- THEN both forms work; a file that declares both `tiers` and `levels` fails with a
  message to keep `tiers` only; `okfreq init` writes the new names and states
  `approval_lock: true` for StRS and `false` for SwRS explicitly

### Scenario: Merge a configuration that uses the other names

- GIVEN a destination and an imported `config.yml`, one with `tiers` and the other
  with the legacy `levels`
- WHEN `okfreq import` or `okfreq config-merge` runs
- THEN `levels` is renamed `tiers` on both sides before merging and the result keeps
  `tiers` only; an imported legacy `lifecycle.values` list is not imported into a
  destination that names `lifecycle.field`, and `lifecycle.values` is reported as a
  conflict; an imported file that declares both `tiers` and `levels` is refused

### Scenario: Use a custom lifecycle field name

- GIVEN `lifecycle.field: state` and a hand-written base schema whose property and
  `required` entry are named `state` (`okfreq init` always generates `req_lifecycle`)
- WHEN `okfreq validate`, `okfreq new`, `okfreq supersede` or `okfreq archive` runs
- THEN each reads or writes `state`, and no `req_lifecycle` field is written

### Scenario: Take the lifecycle values from the base schema

- GIVEN no legacy `lifecycle.values` list
- WHEN `okfreq validate` checks a requirement's lifecycle
- THEN the accepted values are the `enum` of the configured lifecycle field in
  `tiers/_schema/base.schema.yaml`, and a legacy `values` list still wins

### Scenario: Generate the default owner

- GIVEN `default_owner_email` listed in `generated_fields` and an `owner_email` set
  under `scopes.SCOPE.tiers.TIER`, `scopes.SCOPE` or `tiers.TIER`
- WHEN `okfreq update-coverage` runs
- THEN each requirement gets the first owner found in that order, and the field is
  removed once no owner applies; an authored `owner_email` is left untouched
- AND the scope is matched case-insensitively, an unknown scope uses the tier
  settings, and a `null` `approval_lock` counts as unset: the scope setting falls
  back to the tier setting, then to the default (a tier without `derives_from` is
  lockable, a derived tier is not)

### Scenario: Guard an approved requirement

- GIVEN a requirement with `req_lifecycle: approved`
- WHEN `okfreq validate` or `okfreq lint` runs
- THEN it fails when the resolved `approval_lock` is false, or when `approved_by` or
  `approved_at` is missing or is not an ISO 8601 datetime with a UTC offset; the message names the owner and tells a coding agent
  not to decide alone, to record the owner's agreement and to request the owner's
  review of the file, or else to restore the previous state
- AND a `deprecated` or `superseded` requirement may keep its `approved_by` and
  `approved_at` as history

### Scenario: Reject malformed ownership settings

- GIVEN an `approval_lock` that is not a boolean or an `owner_email` that is not an
  email address, in a tier or a scope
- WHEN `okfreq validate` runs
- THEN it reports the dotted `config.yml` path of the setting

### Verification notes

- Method: test
- Criteria: `tests/test_okfreq.py` ownership and lifecycle tests pass, and
  `okfreq validate --check-links` passes on this repository's own bundle.

<!-- okf:links:start -->
### Links

<!-- Generated from the frontmatter relations; edit them instead. -->

- Derives from:
  - [StRS-OKFSCHEMA-OKFREQ-001](../../strs/okfreq/StRS-OKFSCHEMA-OKFREQ-001.md): Maintain auditable software requirements
<!-- okf:links:end -->
