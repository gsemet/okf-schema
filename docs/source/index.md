# okf-schema Documentation

**okf-schema** is a CLI tool and Python library for working with **OKF (Open Knowledge Format)** bundles.

OKF is a markdown-based knowledge format where each concept is a markdown file with YAML frontmatter. This package provides validation against JSONSchema, formatting while preserving comments, and a rich set of bundle management utilities.

## Quickstart

Install from PyPI:

```bash
pip install okf-schema
```

Initialize a new bundle:

```bash
okf-schema init my-bundle
```

Validate an existing bundle:

```bash
okf-schema validate --path my-bundle/bundle
```

Validate strictly (fail on warnings):

```bash
okf-schema validate --path my-bundle/bundle --strict
```

Lint frontmatter (flatten nested lists and convert block-style to inline):

```bash
okf-schema lint --path my-bundle/bundle
```

## Schema features

- **Auto-discovered schemas** — `_schema/*.schema.{yaml,json,json5}` are loaded automatically.
- **`$ref` resolution** — External schema files can be referenced with `$ref` paths relative to `_schema/`.
- **Default `_base.schema.yaml`** — Created automatically by `init`, documenting standard OKF fields.

## Contents

```{toctree}
:maxdepth: 2

api
cli
```

## Indices and tables

- {ref}`genindex`
- {ref}`modindex`
- {ref}`search`
