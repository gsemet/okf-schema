# User Journey 2 — Install KB skills and guideline into a project

## Situation

A developer has just bootstrapped a knowledge base with `okfkb init` (or has an existing
KB). They now want the `record-finding` and `consolidate-knowledge-base` agent skills, plus
the `knowledge-base.guidelines.md` guideline, available inside their project so that Copilot
can discover and use them automatically.

## Current Pain

The skills and guideline currently live in a separate repository
(`copilot-session-usage`). To use them in a new project, a developer must manually locate
the right SKILL.md files, copy the directories, find the guideline, and remember to add a
reference to `AGENTS.md`. This is error-prone and not reproducible across projects.

## What Changes

The developer runs one command from their project root:

```
okfkb install .
```

The command detects whether `.agents/` or `.github/` exists, installs the skills under
`<base>/skills/`, places the guideline under `<base>/guidelines/`, and either creates a
minimal `AGENTS.md` or appends the guideline reference to an existing one.

Any files that already exist are skipped with a warning; `--force` allows overwriting.

After the command completes, the developer can immediately use the `record-finding` skill in
Copilot to dump findings, and `consolidate-knowledge-base` to review and promote them.

## Acceptance Test Ideas

- Running `okfkb install /tmp/target` creates `.agents/skills/record-finding/SKILL.md`,
  `.agents/skills/consolidate-knowledge-base/SKILL.md`, and
  `.agents/guidelines/knowledge-base.guidelines.md`.
- A new minimal `AGENTS.md` is created at `/tmp/target/AGENTS.md` referencing the guideline.
- Running `okfkb install /tmp/target` a second time prints skip warnings for each file and
  does not overwrite them.
- Running `okfkb install /tmp/target --force` overwrites all files.
- If `AGENTS.md` already contains a reference to the guideline, the install command does not
  duplicate the line.
- If `.github/` exists but `.agents/` does not, skills are installed under `.github/`.
