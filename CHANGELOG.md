## Unreleased

### BREAKING CHANGE

- okfreq bundles use req_lifecycle and approved_at.
Migrate an existing bundle:
1. Set lifecycle.field: req_lifecycle in config.yml and rename the
   lifecycle key of every requirement to req_lifecycle.
2. Replace approved_on with approved_at, an ISO 8601 datetime with a UTC
   offset, for example 2026-10-28T09:00:00+01:00.
3. In tiers/_schema/base.schema.yaml, rename the lifecycle property,
   add its x-okf-status-projection mapping, the status and verified
   properties and a link-projection label on each relation field (copy
   them from a fresh okfreq init).
4. Add status and verified to generated_fields, then run
   okfreq update-coverage and okfreq lint.
5. Rewrite log.md headings as "## YYYY-MM-DD", newest first.

### Feat

- **okfreq**: keep requirement bundles native OKF v0.2 bundles

## v0.16.0 (2026-10-28)

### Feat

- **okfreq**: requirement owners and owner-approved lifecycle

## v0.15.1 (2026-10-27)

## v0.15.0 (2026-10-26)

### Feat

- **okfreq**: list superseding requirements and relate requirements

### Refactor

- **okfreq**: keep a single requirements guideline

## v0.14.1 (2026-10-25)

### Fix

- **release**: attach only the package files to the GitHub release

## v0.14.0 (2026-10-25)

### Feat

- **okfreq**: set up a requirements baseline from one skill

### Fix

- **okfreq**: never reuse a requirement number
- **validate**: report W11 for datetime stale_after values
- **schema**: report empty and unparsable schema files

## v0.13.0 (2026-10-19)

### Feat

- **file-links**: expose resolvable frontmatter link results
- describe and check navigable file links in OKF bundles

### Fix

- **okfreq**: keep generated evidence paths stable across platforms

## v0.12.0 (2026-09-02)

### Feat

- **skills**: install packaged agent skills by family
- **okfkb**: maintain canonical derivation links

### Fix

- rework StRS requirement coverage

## v0.11.1 (2026-08-31)

### Fix

- refactor okfreq skill with base knowledge
- remove E7 error and reorder

## v0.11.0 (2026-08-30)

### Feat

- add ofkreq and requirements traceability

### Fix

- **okf**: accept root concepts and bundle attachments

## v0.10.0 (2026-08-10)

### Feat

- **okf**: implement OKF 0.2 compliance

## v0.9.0 (2026-07-13)

### Feat

- **okfkb**: add agent-guided knowledge maintenance

## v0.8.3 (2026-07-10)

### Fix

- bad rtd docs

## v0.8.2 (2026-07-10)

### Fix

- apply readthedocs lfs fix

## v0.8.1 (2026-07-10)

## v0.8.0 (2026-07-10)

### Feat

- **okfkb**: navigation cmds, superseded-link, gardening skill

## v0.7.1 (2026-07-06)

## v0.7.0 (2026-07-06)

### Feat

- add validate-md command and restructure README with 3 use cases

## v0.6.0 (2026-07-04)

### Feat

- okfkb new-finding command
- **kb**: add okfkb CLI and knowledge-base subcommands

### Fix

- rework kb structure

## v0.5.1 (2026-07-03)

### Fix

- fix example schema $ref

## v0.5.0 (2026-07-02)

### Feat

- links and backlinks appears in frontmatters
- define x-okd-summary to contain schema one-line description

## v0.4.1 (2026-07-02)

## v0.4.0 (2026-07-02)

### Feat

- add $ref support and default base schema

### Fix

- enhance the skill

## v0.3.0 (2026-07-01)

### Feat

- backlinks command to get links TO a given concept
- check no knowledge at root folder

### Fix

- update eval campaign

## v0.2.1 (2026-06-29)

### Fix

- **stats**: one line per tag/type with proper indentation

## v0.2.0 (2026-06-29)

### Feat

- initial okf-schema implementation
