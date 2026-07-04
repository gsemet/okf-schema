# Commit Message — okf-schema-kb-subcommands

## Squashed Commit Message

```
feat(kb): add okfkb CLI and knowledge-base subcommands

Add a `kb` subcommand group to the `okf-schema` CLI plus a standalone
`okfkb` alias. Implements:

- `okfkb init [PATH]` — scaffolds a KB folder layout with 8 YAML
  schemas, 8 content directories, index.md, and log.md.
- `okfkb install [PATH]` — deploys bundled skills and guideline into
  a target project and patches/creates AGENTS.md.
- `okf-schema init --pattern kb` — extensible init pattern backed by
  INIT_PATTERNS registry.

Bundled assets (13 files):
- 8 KB schema YAML files under data/kb/_schema/
- 2 skills (record-finding, consolidate-knowledge-base)
- 1 guideline (knowledge-base.guidelines.md)

New modules:
- src/okf_schema/kb/__init__.py
- src/okf_schema/kb/cli.py
- src/okf_schema/kb/scaffold.py
- src/okf_schema/kb/install.py
- src/okf_schema/kb/patterns.py

New tests (69 KB-specific tests, 463 total):
- tests/test_kb_scaffold.py
- tests/test_kb_install.py
- tests/test_kb_patterns.py
- tests/test_kb_cli.py

Updated:
- src/okf_schema/cli.py (register kb group, --pattern flag)
- pyproject.toml (okfkb entry point)
- README.md (Knowledge Base section)
- docs/source/reference/kb-commands.md

Coverage: 96.55% (threshold 96%). All linters and type checkers pass.
```

## Commit Trailers

```
Craftsman-Commit-Type: Coding
```
