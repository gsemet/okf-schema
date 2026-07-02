# okf-schema

[![CI](https://github.com/gsemet/okf-schema/actions/workflows/ci.yml/badge.svg)](https://github.com/gsemet/okf-schema/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/codecov/c/github/gsemet/okf-schema)](https://codecov.io/gh/gsemet/okf-schema)
[![PyPI](https://img.shields.io/pypi/v/okf-schema)](https://pypi.org/project/okf-schema/)
[![Python Versions](https://img.shields.io/pypi/pyversions/okf-schema)](https://pypi.org/project/okf-schema/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Type checked](https://img.shields.io/badge/type%20checked-mypy%2Fty-blue.svg)](./)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Documentation](https://img.shields.io/badge/docs-readthedocs-blue)](https://okf-schema.readthedocs.io/en/stable/)

**okf-schema** is a CLI tool and Python library for working with **OKF (Open Knowledge Format)** bundles
with JSONSchema validation of the frontmatter metadata, and formatting capabilities while preserving comments.

OKF is a markdown-based knowledge format where each concept is a markdown file with YAML frontmatter.
See the [OKF specification](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md) for the full format definition.

📖 **Full documentation**: [okf-schema.readthedocs.io](https://okf-schema.readthedocs.io/en/stable/)

> [!IMPORTANT]
> OKF-schema is opinionated. It delivers a valid OKF bundle but is adds a structure on the frontmatter that
> is not allowed in OKF specification:
>
> ```raw
> Type values are **not** registered centrally. Producers SHOULD pick
> values that are descriptive and self-explanatory; consumers MUST
> tolerate unknown types gracefully (typically by treating them as
> generic concepts).
> ```
>
> In a strict OKF bundle, the `type` field is mandatory but can take any value and the validator needs
> to allow any field in the frontmatter.
>
> OKF-schema **requires** the type to be one of the registered types in the `_schema/` directory
> and validates the frontmatter against the corresponding schema.
> Additional properties may or may not be allowed depending on the schema definition.

## What `okf-schema` adds to OKF

Plain OKF only defines a folder of markdown files. `okf-schema` turns those files into a **validated, queryable knowledge base** by adding:

| Capability | What it does |
|-----------|--------------|
| **Schema-driven frontmatter validation** | Every concept's YAML frontmatter is checked against a JSONSchema. Invalid fields, missing required keys, or wrong types are reported as structured errors. |
| **Auto-discovered schemas** | Schemas live inside the bundle under `_schema/` (e.g. `_schema/concept.schema.yaml`). The `type` field in a concept's frontmatter tells `okf-schema` which schema file to load. A concept with `type: concept` is validated against `_schema/concept.schema.yaml`. Schemas can be written in **YAML**, **JSON**, or **JSON5** (JSON with comments and trailing commas). |
| **Bundle integrity checks** | Detects broken internal links, missing `index.md` files, malformed `log.md` entries, and reserved-file violations. |
| **Safe linting** | Normalizes YAML frontmatter by flattening nested lists and converting block-style to inline notation while preserving comments and custom quotes via `ruamel.yaml`. |
| **Analytics** | Bundle statistics. |

See a real schema definition in [`examples/ai-llm-knowledge-base/_schema/concept.schema.yaml`](examples/ai-llm-knowledge-base/_schema/concept.schema.yaml).

Example of structure

```raw
my-bundle/
├── _schema/
│   ├── concept.schema.yaml
│   ├── tool.schema.json
│   └── paper.schema.json5
├── concepts/
│   ├── rag.md
│   └── chain-of-thought.md
├── tools/
│   ├── langchain.md
│   └── llamaindex.md
├── papers/
│   ├── rag-paper.md
│   └── chain-of-thought-paper.md
├── index.md
└── log.md
```

The `type` field in each entity frontmatter determines which schema is used for validation.
For example, `type: concept` uses `_schema/concept.schema.yaml`, while `type: tool` uses `_schema/tool.schema.json`.

Schema extensions supported:

- `.schema.yaml` — YAML (human-friendly, supports comments and anchors)
- `.schema.json` — JSON (strict syntax, widely supported by editors)
- `.schema.json5` — JSON5 (JSON with comments, trailing commas, and unquoted keys)

### `$ref` support

Schemas can reference external files with `$ref`. The path is resolved relative to the `_schema/` directory:

```yaml
# _base.schema.yaml
$schema: "https://json-schema.org/draft/2020-12/schema"
type: object
properties:
  type:
    type: string
  title:
    type: string
required:
  - type
additionalProperties: true
```

```yaml
# concept.schema.yaml
$ref: _base.schema.yaml
properties:
  category:
    enum: [LLM, AI Agent, Coding Agent]
```

`$ref` works at any nesting level (top-level, inside `properties`, inside `items`, etc.). If the referenced file cannot be found, the `$ref` is preserved as-is and validation proceeds with the remaining schema content.

### Default `_base.schema.yaml`

When you run `okf-schema init`, a `_base.schema.yaml` is automatically created in `_schema/`. It documents the standard OKF frontmatter fields and can be used as a `$ref` target for your own schemas:

| Field | Required | Description |
|-------|----------|-------------|
| `type` | **Yes** | A short string identifying the kind of concept. |
| `title` | No | Human-readable display name. |
| `description` | No | One-line summary of the concept. |
| `resource` | No | URI of the underlying asset. |
| `tags` | No | List of short categorization strings. |
| `timestamp` | No | ISO 8601 datetime of last change. |

## Installation

```bash
uv tool install okf-schema
```

## Quickstart

```bash
# Initialize a new OKF bundle
okf-schema init my-bundle

# Update index.md files for all directories
okf-schema index --path my-bundle/bundle

# Lint frontmatter (flatten nested lists and convert block-style to inline)
okf-schema lint --path my-bundle/bundle

# Validate a bundle
okf-schema validate --path my-bundle/bundle
# or enforce strict validation (fail on warnings)
okf-schema validate --path my-bundle/bundle --strict

# List all concepts
okf-schema list --path my-bundle/bundle

# Find backlinks to a concept (extension is optional)
okf-schema backlinks --path my-bundle/bundle concepts/react-pattern
```

## CLI Reference

| Subcommand | Description |
|-----------|-------------|
| `init <name>` | Create a new OKF bundle directory structure |
| `new --path <dir> --name <name>` | Create a new concept file with frontmatter template |
| `validate --path <bundle>` | Validate bundle structure and frontmatter |
| `validate --path <bundle> --strict` | Validate and fail on warnings |
| `lint --path <bundle>` | Lint frontmatter: flatten nested lists and convert block-style to inline |
| `list --path <bundle>` | List all concepts in a bundle |
| `show --path <bundle> <concept>` | Show a single concept's frontmatter and body |
| `index --path <bundle>` | Regenerate all `index.md` files |
| `stats --path <bundle>` | Show bundle statistics |
| `backlinks --path <bundle> <target>...` | List concepts that link to the given target(s) |

## Recommended Workflow

Before packaging or distributing a bundle, run these three commands in order and fix all warnings:

```bash
okf-schema index --path my-bundle/bundle    # regenerate index.md files
okf-schema lint --path my-bundle/bundle     # flatten nested lists and convert block lists to inline
okf-schema validate --path my-bundle/bundle --strict # check structure, schema, and links; fail on warnings
```

Only zip or ship the bundle once `validate --strict` reports **zero errors and zero warnings**. Warnings such as missing `index.md` (W4), block-style lists (W7), or broken cross-links (W2) signal issues that will degrade the experience for downstream consumers.

## Example: AI & LLM Knowledge Base

The [`examples/ai-llm-knowledge-base/`](examples/ai-llm-knowledge-base/) directory contains a realistic knowledge base with **three concept types** — `concept`, `tool`, and `paper` — each validated by its own schema in `_schema/`.

### How `type` selects the schema

The `type` field in a concept's frontmatter determines which schema file is loaded. A file with `type: concept` is validated against `_schema/concept.schema.yaml`; `type: tool` against `_schema/tool.schema.json`; and `type: paper` against `_schema/paper.schema.json5`.

### Schema format support

`okf-schema` accepts schemas in three formats:

| Extension | Format | Notes |
|-----------|--------|-------|
| `.schema.yaml` | YAML | Human-friendly, supports comments and anchors |
| `.schema.json` | JSON | Strict syntax, widely supported by editors |
| `.schema.json5` | JSON5 | JSON with comments, trailing commas, and unquoted keys |

### Schema highlights

**`concept.schema.yaml`** — AI concepts with enums, email validation, and kebab-case regex:

```yaml
properties:
  category:
    enum: [LLM, AI Agent, Coding Agent, Prompt Engineering, Tooling, Evaluation]
  maturity:
    enum: [experimental, beta, production, deprecated]
  author_email:
    type: string
    format: email
  tags:
    type: array
    items:
      pattern: "^[a-z0-9-]+$"   # kebab-case only
```

**`tool.schema.json`** — Developer tools with URI validation and language enums:

```json
{
  "properties": {
    "license": {
      "enum": ["MIT", "Apache-2.0", "GPL-3.0", "Proprietary", "Other"]
    },
    "language": {
      "enum": ["Python", "JavaScript", "TypeScript", "Rust", "Go", "Java", "Multi-language"]
    },
    "url": { "type": "string", "format": "uri" }
  }
}
```

**`paper.schema.json5`** — Research papers with year bounds and venue enums:

```javascript
// JSON5 allows comments, trailing commas, and unquoted keys
{
  properties: {
    year: { type: "integer", minimum: 1950, maximum: 2030 },
    venue: {
      enum: ["NeurIPS", "ICML", "ICLR", "ACL", "EMNLP", "arXiv", "Other"]
    },
    bibtex_key: { pattern: "^[A-Za-z0-9_-]+$" },
  },
}
```

### Schema-aware index generation

Schemas can declare a `title` and an `x-okf-summary` extension field. When a
subdirectory contains concepts of a single type, `okf-schema index` uses these
values to produce richer `index.md` files:

| Field | Purpose | Used in |
|-------|---------|---------|
| `title` | Short heading for the concept type | Subdirectory `index.md` H1 |
| `x-okf-summary` | One-line description of the type | Subdirectory intro + root listing |
| `description` | Fallback when `x-okf-summary` is absent | Same places as above |

For example, `concept.schema.yaml` declares:

```yaml
title: "Concept"
x-okf-summary: "AI/LLM concepts such as techniques, patterns, or architectural ideas."
description: "Schema for AI/LLM concepts ..."
```

Running `okf-schema index` turns this into:

- A root `index.md` entry: `[concepts](./concepts/) — AI/LLM concepts such as...`
- A subdirectory `index.md` with `# Concept` as the heading and the summary as
  the first paragraph.

### Concept file example (`concepts/rag.md`)

```markdown
---
type: concept
title: Retrieval-Augmented Generation
description: >
  A technique that enhances LLM outputs by retrieving relevant documents
  from an external knowledge store and injecting them into the prompt.
category: LLM
maturity: production
author_email: bob@example.com
complexity: intermediate
tags: [rag, retrieval, llm, knowledge-base]
related_tools: [LangChain, LlamaIndex, OpenAI-API]
---

# Retrieval-Augmented Generation

RAG combines parametric knowledge (the model's weights) with non-parametric
knowledge (external documents) to reduce hallucinations...
```

### Validation in action

```bash
# Validates all concepts, tools, and papers against their respective schemas
okf-schema validate --path examples/ai-llm-knowledge-base

# Show bundle statistics
okf-schema stats --path examples/ai-llm-knowledge-base
```

## Python API

```python
from okf_schema.api import validate_bundle

report = validate_bundle("path/to/bundle")
for finding in report.findings:
    print(finding.level, finding.message)

# The _schema/ directory inside the bundle is auto-discovered.
# You can also pass an explicit schema_db path:
# report = validate_bundle("path/to/bundle", schema_db="path/to/schemas")
```

## Documentation

Documentation is available at [okf-schema/README.md](https://github.com/gsemet/okf-schema/blob/main/README.md).

## Evaluation

`okf-schema` includes an automated skill evaluation campaign in `skills-evals/` that validates the tool against a suite of fixture bundles. These evals verify that the validator correctly identifies conformant bundles, catches structural errors (E1–E6), reports warnings (W1–W7), and handles JSONSchema validation with both JSON and YAML schema databases.

| Eval | Description |
|------|-------------|
| `validate-conformant-bundle` | Validates a fully conformant OKF bundle (0 errors, 0 warnings) |
| `validate-non-conformant-bundle` | Validates a bundle with known errors (E1–E3) and warnings (W1–W7) |
| `create-okf-bundle` | Creates a new OKF bundle from scratch and validates it |
| `validate-with-schema-database` | Tests JSONSchema validation with `--schema-db` |
| `validate-with-yaml-schema-database` | Tests YAML schema file support in schema DB |

Run the eval campaign by asking in Copilot Chat `Execute instructions in skills-evals/eval.prompt.md`, or via Copilot-CLI:

```bash
# Trigger eval via Copilot-CLI
just copilot-cli-eval-okf-schema
# Open eval review in browser
just eval-view-okf-schema
```

The eval system supports A/B comparison (`with_skill` vs `without_skill`) across iteration directories. Results are rendered as an interactive HTML dashboard.

**Latest eval result:** [iteration-30.06.26-22.06](https://htmlpreview.github.io/?https://github.com/gsemet/okf-schema/blob/master/skills-evals/results/iteration-30.06.26-22.06/eval-result.html) — [skeptical review](skills-evals/results/iteration-30.06.26-22.06/skeptical-review.md)

## Contributing

See [CONTRIBUTING.md](https://github.com/gsemet/okf-schema/blob/main/CONTRIBUTING.md) for development setup and guidelines.

## License

MIT License — see [LICENSE](https://github.com/gsemet/okf-schema/blob/main/LICENSE) for details.
