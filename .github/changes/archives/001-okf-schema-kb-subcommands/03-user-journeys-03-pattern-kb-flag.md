# User Journey 3 — Use `okf-schema init --pattern kb`

## Situation

A developer already knows and uses `okf-schema init <name>` to create generic OKF bundles.
They want to bootstrap a knowledge base but prefer to stay in the familiar `okf-schema`
command namespace rather than learning a new entry point.

## Current Pain

`okf-schema init` only creates a minimal generic OKF bundle. There is no way to request a
specialised scaffold variant without switching to a different command. The developer either
has to remember `okfkb` as a separate tool or manually copy the KB structure.

## What Changes

`okf-schema init` gains an optional `--pattern <name>` flag. Running:

```
okf-schema init my-knowledge --pattern kb
```

produces exactly the same scaffold as `okfkb init my-knowledge` — with all 8 KB schemas and
8 content directories. The base behaviour of `okf-schema init <name>` (no `--pattern`) is
completely unchanged.

If an unknown pattern name is provided (e.g., `--pattern typo`), a clear error lists the
available patterns.

## Acceptance Test Ideas

- `okf-schema init my-kb --pattern kb` produces the same output as `okfkb init my-kb`.
- `okf-schema init my-kb` (no `--pattern`) behaves exactly as before — produces the minimal
  generic bundle.
- `okf-schema init my-kb --pattern unknown` exits with a non-zero code and prints:
  "Unknown pattern 'unknown'. Available patterns: kb".
- The `--pattern` flag is listed in `okf-schema init --help` output.
