# Migrate Existing Documentation

Convert an existing documentation folder into a validated OKF bundle.

## 1. Scaffold the bundle structure

```bash
okf-schema init my-docs
```

## 2. Move markdown files into namespaced folders

OKF-Schema requires concepts to live in subdirectories. Reorganize:

```text
# Before
my-docs/
  README.md
  setup.md
  api.md

# After
my-docs/bundle/
  guides/
    setup.md
  reference/
    api.md
```

## 3. Add frontmatter to each concept

Every `.md` file needs YAML frontmatter with at least a `type` field:

```markdown
---
type: guide
title: Setup Guide
description: How to install and configure the project.
tags: [setup, installation]
---

# Setup Guide

...existing content...
```

Use a script to bulk-add frontmatter:

```bash
for f in my-docs/bundle/**/*.md; do
  if ! grep -q "^---" "$f"; then
    echo -e "---\ntype: concept\n---\n\n$(cat "$f")" > "$f"
  fi
done
```

## 4. Write schemas for your types

Create `_schema/guide.schema.yaml`, `_schema/reference.schema.yaml`, etc.
See [Write a Custom Schema](write-custom-schema.md) for details.

## 5. Validate and iterate

```bash
okf-schema validate --path my-docs/bundle
```

Fix errors, add missing fields, and repeat until the bundle is conformant.

## 6. Generate index files

```bash
okf-schema index --path my-docs/bundle
```

This creates `index.md` files in every directory, giving you a navigable table of contents.

## See also

- [Write a Custom Schema](write-custom-schema) — defining schemas for your migrated types.
- [Bootstrap a Knowledge Base](bootstrap-knowledge-base) — starting fresh with the opinionated KB layout.
- [Validate in CI](validate-in-ci) — keeping the migrated bundle clean over time.
- [Getting Started](../tutorials/getting-started) — broader tutorial on OKF bundle creation.
