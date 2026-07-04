# Lint Before Commit

Keep frontmatter formatting consistent across your team by running `lint`
before every commit.

## What the linter does

The `okf-schema lint` command normalizes YAML frontmatter while preserving
human edits:

* **Flattens nested lists** — `[[a, b], c]` becomes `[a, b, c]`
* **Converts block-style to inline** — Multi-line lists become compact `[a, b, c]`
* **Preserves comments** — Inline and block comments are kept intact
* **Preserves key order** — Frontmatter keys stay in their original sequence

## Check mode

See which files would change without modifying anything:

```bash
okf-schema lint --path my-bundle/bundle --check
```

Exits with code 1 if any file needs formatting. Use this in CI to enforce
consistency.

## Diff mode

Preview changes as a unified diff:

```bash
okf-schema lint --path my-bundle/bundle --diff
```

## Pre-commit hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: okf-lint
        name: Lint OKF frontmatter
        entry: okf-schema lint --path knowledge-base/bundle --check
        language: system
        pass_filenames: false
        files: ^knowledge-base/.*\.md$
```

## Why compact frontmatter matters

Coding agents often load only the first 20–50 lines of a file. Compact,
inline frontmatter ensures the `type`, `title`, and `tags` fields are
visible in the agent's context window, improving routing and search
accuracy.

## See also

- [Validate in CI](validate-in-ci) — pair linting with validation in your pipeline.
- [Building a Knowledge Graph](../tutorials/knowledge-graph) — how `lint` materialises links into frontmatter.
- [CLI Reference](../reference/cli.md) — full `lint` command options.
- [Design Principles](../explanation/design-principles) — why compact frontmatter and human-edit preservation matter.
