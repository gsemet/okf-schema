# Getting Started

This guide walks you through creating, navigating, and maintaining an
OKF knowledge bundle. It assumes you have already installed `okf-schema`;
see the [CLI Reference](../reference/cli.md) for installation instructions.

---

## Create a new bundle

Use the `init` command to scaffold a bundle with the required directory
structure and a base schema:

```bash
okf-schema init my-knowledge-base
```

This creates:

```
my-knowledge-base/
└── bundle/
    ├── index.md          # Bundle root listing
    ├── log.md            # Chronological update history
    └── _schema/
        └── _base.schema.yaml   # Default JSONSchema for frontmatter
```

The `_base.schema.yaml` enforces the minimum OKF contract: every concept
must have a `type` field. You can extend it or add domain-specific schemas
in `_schema/`: they are auto-discovered at validation time.

---

## Add your first concept

A **concept** is a single markdown file with YAML frontmatter. Create one
with the `new` command:

```bash
okf-schema new --path my-knowledge-base/bundle \
               --name tables/orders \
               --type "BigQuery Table" \
               --title "Customer Orders"
```

This produces `my-knowledge-base/bundle/tables/orders.md`:

```markdown
---
type: BigQuery Table
title: Customer Orders
description: ""
tags: []
---

```

Fill in the body with structured content: a schema section, examples,
citations, or free-form prose. Keep each concept focused on a single
unit of truth.

---

## Navigate the bundle

### List everything

```bash
okf-schema list --path my-knowledge-base/bundle
```

### See bundle statistics

```bash
okf-schema stats --path my-knowledge-base/bundle
```

### Show a specific concept

```bash
okf-schema show --path my-knowledge-base/bundle tables/orders
```

### Inspect backlinks

Discover which concepts link to a given file:

```bash
okf-schema backlinks --path my-knowledge-base/bundle tables/orders
```

### Generate or refresh index files

`index.md` files provide progressive disclosure: a table of contents for
each directory. Generate them automatically:

```bash
okf-schema index --path my-knowledge-base/bundle
```

---

## Validate and lint

Before committing changes, ensure the bundle is conformant:

```bash
# Standard validation
okf-schema validate --path my-knowledge-base/bundle

# Strict mode — warnings become errors
okf-schema validate --path my-knowledge-base/bundle --strict
```

Normalize frontmatter formatting (flatten nested lists, inline block
style):

```bash
okf-schema lint --path my-knowledge-base/bundle
```

Run both in sequence before every commit to keep the bundle clean.

---

## Maintain the bundle

### Log changes

Update `log.md` at the root (or in any subdirectory) with a dated entry:

```markdown
## 2026-07-02

* **Creation**: Added [orders table](tables/orders.md) for sales analytics.
* **Update**: Linked orders to [customers](tables/customers.md) via `customer_id`.
```

This creates an audit trail that humans and agents can scan to understand
the evolution of the knowledge base.

### Cross-link aggressively

Use relative links (`../tables/customers.md` or `./orders.md`) to connect
related concepts. A dense graph of small, interlinked documents is more
useful than a few monolithic pages.

### Validate in CI

Add a check to your continuous integration pipeline:

```bash
okf-schema validate --path my-knowledge-base/bundle --strict
```

This prevents malformed or incomplete concepts from reaching the main
branch.

---

## Design principles for a healthy knowledge base

### Prefer small chunks of truth

Each concept should describe one thing — a table, a metric, a playbook,
an API endpoint. When a concept grows beyond a few screenfuls, split it
into linked sub-concepts. Small documents are easier to read, validate,
and update.

### Connect everything

A knowledge base is a graph, not a folder hierarchy. Every concept
should link to related concepts: a table links to its dataset, a metric
links to the tables it queries, a playbook links to the resources it
operates on. Dense cross-linking makes the bundle navigable by both
humans and agents.

### Let agents maintain the bundle

OKF is designed for agentic workflows. Use agents to:

* **Generate** concepts from source code, APIs, or databases.
* **Validate** that frontmatter is complete and links are not broken.
* **Index** directories automatically when the structure changes.
* **Lint** frontmatter to keep formatting consistent.

The CLI is built for automation — every command exits with a non-zero
status on failure and produces machine-parseable output.

### Challenge and confirm data

Treat the knowledge base as a living document, not a static archive:

* **Challenge**: Periodically ask whether a concept is still accurate.
  Does the schema match the current table? Does the playbook still
  reflect the on-call procedure?
* **Confirm**: When an agent or human verifies a concept, update the
  `timestamp` field and add a note to `log.md`.
* **Infirm**: When a concept becomes obsolete, do not delete it
  immediately. Mark it with `status: deprecated` and link to its
  replacement. This preserves historical context.
