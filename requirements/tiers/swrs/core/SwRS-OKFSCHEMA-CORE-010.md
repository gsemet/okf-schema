---
type: SwRS
id: SwRS-OKFSCHEMA-CORE-010
uuid: ed4105d8-1145-4f3a-94cf-0a41aa80c5ca
title: Stay inside the bundle
description: When a user shows a concept or prints its trust tier, okf-schema
  SHALL refuse, without reading it, a concept path whose real path, symbolic
  links followed, is outside the bundle.
project: okf-schema
scope: core
req_lifecycle: proposed
status: stable
origin: native
tier: SwRS
derives_from:
- StRS-OKFSCHEMA-CORE-002
annotation_exemption: false
exemption_reason:
owner: okf-schema maintainers
verification_method: test
verification_criteria: Focused regression tests and the complete project
  preflight pass.
documentation_files:
- docs/source/reference/cli.md
agent_skill_files:
- skills/okf-schema/SKILL.md
scenarios:
- id: S1
  title: Refuse a concept path that leaves the bundle
- id: S2
  title: Refuse a symbolic link that leaves the bundle
- id: S3
  title: Keep paths that stay inside
derived_by: []
implemented_in_files:
- src/okf_schema/api.py
tested_in_files:
- tests/test_api.py
- tests/test_cli_remaining.py
- tests/test_edge_cases.py
default_owner_email: gaetan@xeberon.net
---

## Stay inside the bundle

### Normative behavior

When a user shows a concept or prints its trust tier, okf-schema SHALL refuse, without reading it, a concept path whose real path, symbolic links followed, is outside the bundle.

### Scenario S1: Refuse a concept path that leaves the bundle

- GIVEN a concept path such as `../outside.md` or `../outside`, a Windows drive
  path outside the bundle, on Windows a name starting with `\` (a path from the
  root of the drive) outside the bundle, or `.` when a file named like the bundle
  folder with `.md` added sits beside the bundle
- WHEN the user shows it or prints its trust tier
- THEN okf-schema reports
  `Concept path is outside the bundle: PATH (bundle: BUNDLE)`, naming the concept
  path and the bundle, exits 2 on the CLI, raises `FileNotFoundError` in the API,
  and reads nothing outside the bundle

### Scenario S2: Refuse a symbolic link that leaves the bundle

- GIVEN a symlinked file inside the bundle whose target is outside it, or a file
  reached through a symlinked directory that points outside
- WHEN the user shows it or prints its trust tier
- THEN the same refusal as S1 applies and the target is not read

### Scenario S3: Keep paths that stay inside

- GIVEN `sub/../concept-a.md`, an absolute disk path inside the bundle, or a
  symlink inside the bundle whose target is inside
- WHEN the user shows it or prints its trust tier
- THEN the concept is shown as before

### Boundaries and known issues

- Known issue: `validate`, `list`, `index`, `backlinks` and `lint` still follow
  symbolic links whose target is outside the bundle.
- An absolute concept path is recognized as a disk path inside the bundle when
  one of its folders, symbolic links followed, is the real path of `--path`,
  symbolic links followed. On a case-insensitive file system such as macOS,
  following links does not change letter case, so an absolute path whose bundle
  part is spelled in another case than the real path of `--path` is not
  recognized; it is read from the bundle root and reported as not found.
- A concept path starting with `/` that is not a disk path inside the bundle is
  read from the bundle root, so on POSIX an absolute path outside the bundle is
  searched in the bundle and never read. On Windows a concept path starting with
  `\` keeps its Windows meaning, a path from the root of the drive, and is
  refused when it is outside the bundle.

### Verification notes

- Method: public API and CLI tests of `show` and `trust`.
- Criteria: a path, Windows drive path or symlink whose real path is outside the
  bundle is refused without being read; a POSIX absolute path outside the bundle
  is searched in the bundle and never read; a `..` path, an absolute disk path or
  a symlink whose real path stays inside works.

<!-- okf:links:start -->
### Links

<!-- Generated from the frontmatter relations; edit them instead. -->

- Derives from:
  - [StRS-OKFSCHEMA-CORE-002](../../strs/core/StRS-OKFSCHEMA-CORE-002.md): Maintain and inspect OKF bundles
<!-- okf:links:end -->
