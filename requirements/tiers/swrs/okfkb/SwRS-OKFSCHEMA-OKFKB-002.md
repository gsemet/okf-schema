---
type: SwRS
id: SwRS-OKFSCHEMA-OKFKB-002
uuid: 56c42668-10b7-4119-a083-1d257fd94b0d
title: Scaffold and install knowledge bases
description: The okfkb layer scaffolds knowledge bases with type-aligned tier
  folders and installs their supporting guidance.
project: okf-schema
scope: okfkb
lifecycle: draft
origin: native
tier: SwRS
derives_from:
- StRS-OKFSCHEMA-OKFKB-001
annotation_exemption: false
exemption_reason:
derived_by: []
implemented_in_files:
- src/okf_schema/okfkb/patterns.py
- src/okf_schema/okfkb/cli.py
- src/okf_schema/okfkb/scaffold.py
- src/okf_schema/okfkb/install.py
- src/okf_schema/skill_installer.py
tested_in_files:
- tests/test_integration.py
- tests/test_kb_cli.py
- tests/test_kb_install.py
- tests/test_kb_patterns.py
- tests/test_kb_scaffold.py
- tests/test_skill_installer.py
---

## EARS Expression

### Normative behavior

When a user initializes or installs an `okfkb` knowledge base, the CLI SHALL
create the configured bundle structure and supporting agent guidance without
overwriting existing authored files.

### Scenario: Scaffold a new knowledge base

- GIVEN an empty target directory
- WHEN the user initializes an `okfkb` knowledge base
- THEN the target contains the required schemas, type-aligned layer
  directories, indexes, and guidance needed for subsequent knowledge
  operations, including `playbooks/` for `Playbook` documents

### Scenario: Install into existing content

- GIVEN a target containing authored files
- WHEN supporting `okfkb` guidance is installed
- THEN existing authored files remain unchanged and only missing managed assets
  are added

### Verification notes

- Method: automated scaffold and installation tests in temporary directories.
- Criteria: a fresh bundle validates, and installation preserves pre-existing
  file bytes.
