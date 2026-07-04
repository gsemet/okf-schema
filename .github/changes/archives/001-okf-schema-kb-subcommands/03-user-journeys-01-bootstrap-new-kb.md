# User Journey 1 — Bootstrap a new knowledge base

## Situation

A developer (or AI agent operator) wants to create a structured space for capturing
experimental findings and building trustworthy, traceable knowledge. They have
`okf-schema` installed and want the canonical KB layout ready with correct schemas and
content directories in place.

## Current Pain

Without this feature, setting up a knowledge base means manually copying the folder
structure and schema files from a reference project (`copilot-session-usage/knowledge/`).
There is no standard way to do it, no validation that the structure is correct, and no
single command to get started.

## What Changes

The developer runs one command:

```
okfkb init knowledge/
```

In seconds they have:
- 8 YAML schema files under `knowledge/_schema/` defining the KB document types
  (Finding, Concept, Experiment, Principle, Structure, Playbook, Reference).
- 8 content directories (`concepts/`, `experiments/`, `findings/`, `guides/`, `ideas/`,
  `principles/`, `reference/`, `structures/`).
- A valid `index.md` and `log.md` at the root.

The result is immediately usable by the `record-finding` and `consolidate-knowledge-base`
skills, and it passes `okf-schema validate`.

## Acceptance Test Ideas

- Running `okfkb init /tmp/my-kb` creates the expected directory tree with no errors.
- All 8 schema files are present and non-empty under `/tmp/my-kb/_schema/`.
- All 8 content directories exist.
- `okf-schema validate --path /tmp/my-kb` exits 0.
- Running `okfkb init /tmp/my-kb` a second time (without `--force`) fails with a clear
  "already exists" error.
- Running `okfkb init /tmp/my-kb --force` succeeds and overwrites.
