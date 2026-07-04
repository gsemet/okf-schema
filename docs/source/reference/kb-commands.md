# Knowledge Base Commands

The `kb` subcommand group (also available as the standalone `okfkb` command) provides tools
for managing OKF knowledge-base bundles — an opinionated bundle type designed for
agent-facing experimental findings.

```bash
okfkb init [PATH]       # Scaffold a new knowledge base
okfkb install [PATH]    # Install skills and guidelines
```

`okfkb` is a standalone alias; `okf-schema kb <cmd>` and `okfkb <cmd>` are strictly equivalent.

---

## `okfkb init`

Scaffold a canonical knowledge-base folder layout with 8 content directories,
8 schema YAML files, `index.md`, and `log.md`.

```bash
okfkb init [PATH]
```

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `PATH` | — | `.` (current directory) | Destination directory for the new knowledge base. |

| Option | Description |
|--------|-------------|
| `--force` | Overwrite an existing non-empty directory. |

**Scaffolded layout:**

```
<PATH>/
├── _schema/
│   ├── Base.schema.yaml
│   ├── Concept.schema.yaml
│   ├── Experiment.schema.yaml
│   ├── Finding.schema.yaml
│   ├── Playbook.schema.yaml
│   ├── Principle.schema.yaml
│   ├── Reference.schema.yaml
│   └── Structure.schema.yaml
├── concepts/
├── experiments/
├── findings/
├── guides/
├── ideas/
├── principles/
├── reference/
├── structures/
├── index.md
└── log.md
```

The same scaffold is available through the `--pattern` flag on `okf-schema init`:

```bash
okf-schema init my-kb --pattern kb
```

---

## `okfkb install`

Deploy the bundled `record-finding` and `consolidate-knowledge-base` skills, plus the
`knowledge-base.guidelines.md` guideline, into a target project directory.
Patches or creates `AGENTS.md` to reference the installed guideline.

```bash
okfkb install [PATH]
```

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `PATH` | — | `.` (current directory) | Target project root. |

| Option | Description |
|--------|-------------|
| `--force` | Overwrite existing skill/guideline files (default: skip). |

**Install behaviour:**

- Detects whether `PATH/.agents/` or `PATH/.github/` exists; prefers `.agents/`; falls back
  to `.github/`; creates `.agents/` if neither exists.
- Copies skills to `<base>/skills/` and the guideline to `<base>/guidelines/`.
- Existing files are skipped (with a warning) unless `--force` is passed.
- `AGENTS.md` patching is always idempotent — the guideline reference is never duplicated.

---

## `okf-schema kb`

The `kb` subcommand group is also registered directly on the top-level `okf-schema` CLI:

```bash
okf-schema kb --help
okf-schema kb init [PATH]
okf-schema kb install [PATH]
```

This is identical to `okfkb`; use whichever form is more convenient.
