# okf-schema

[![GitHub](https://img.shields.io/badge/GitHub-okf--schema-181717?logo=github)](https://github.com/gsemet/okf-schema)

**okf-schema** is a CLI tool and Python library for working with
[OKF (Open Knowledge Format) bundles](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md).

OKF is a markdown-based knowledge format where each concept is a markdown file with YAML
frontmatter. This package provides validation against JSONSchema, formatting while preserving
comments, and bundle management utilities. See this official, draft
[spec](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md).

OKF-Schema is highly opinionated: it enforces a stricter model than the spec, and it is not
guaranteed that every valid OKF bundle will pass `okf-schema` validation.

However, OKF-Schema bundles are OKF-compliant. See
[OKF-Schema vs. OKF Spec](reference/okf-schema-vs-spec) for details.

Links to source code: [gsemet/okf-schema](https://github.com/gsemet/okf-schema)

::::{grid} 1 1 2 2
:gutter: 3

:::{grid-item-card} 📦 Installation
:link: installation
:link-type: doc

How to install `okf-schema`.
:::

:::{grid-item-card} 🚀 Getting Started
:link: tutorials/getting-started
:link-type: doc

Create your first bundle and learn the core workflow in under 10 minutes.
:::

:::{grid-item-card} 🕸️ Tutorials
:link: tutorials/index
:link-type: doc

Build a fictional data-platform knowledge base, see how cross-links form a
navigable graph, and query it from the CLI and Python API.
:::

:::{grid-item-card} 📖 How-To Guides
:link: how-to/index
:link-type: doc

Task-oriented recipes: validate in CI, write custom schemas,
migrate existing docs, and more.
:::

:::{grid-item-card} 📚 Reference
:link: reference/index
:link-type: doc

Complete API and CLI documentation.
Look up commands, functions, and data models.
:::

:::{grid-item-card} 💡 Design Principles
:link: explanation/design-principles
:link-type: doc

Understand the design philosophy behind OKF-Schema
and how it relates to the OKF specification.
:::

::::

```{toctree}
:maxdepth: 2
:hidden:

Installation <installation>
Tutorials <tutorials/index>
How-To <how-to/index>
Reference <reference/index>
Design Principles <explanation/design-principles>
Changelog <changelog>
```
