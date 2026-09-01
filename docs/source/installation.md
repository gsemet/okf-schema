# Installation

**okf-schema** is published to PyPI and can be installed with any Python package manager.

## With uv (recommended)

```bash
uv tool install okf-schema
```

## With pip

(it is not recommended to install a CLI, `uv` is always to be preferred when available)

```bash
pip install okf-schema
```

## Verify the installation

```bash
okf-schema --version
```

## Upgrade (uv)

```bash
uv tool install --upgrade okf-schema
```

## Using OKF-Schema as a library

Install as a Python library for programmatic use:

```bash
uv add okf-schema
```

## Install the agent skills manually

The Python package installs the `okf-schema`, `okfkb`, and `okfreq` commands.
The agent skills are currently distributed in the repository and are not yet
included in the PyPI package. Copy the skills you need into your project's
agent configuration before following an agent-assisted tutorial.

Clone or download the repository, then copy complete skill directories. Each
directory must keep its `SKILL.md` file and any `references/` files beside it:

```bash
mkdir -p .agents/skills
cp -R /path/to/okf-schema/skills/okf-schema .agents/skills/
cp -R /path/to/okf-schema/skills/okfkb .agents/skills/
cp -R /path/to/okf-schema/skills/okfkb-record-findings .agents/skills/
cp -R /path/to/okf-schema/skills/okfkb-distill .agents/skills/
cp -R /path/to/okf-schema/skills/okfkb-gardening .agents/skills/
cp -R /path/to/okf-schema/skills/okfreq .agents/skills/
cp -R /path/to/okf-schema/skills/okfreq-gardening .agents/skills/
```

Use `.agents/skills/` when your agent supports it. If the project already uses
`.github/skills/` instead, copy the directories there; do not maintain the same
skill in both locations. Restart or reload the agent session after copying so
it discovers the new skills.

You do not need every skill:

- `okf-schema` covers generic bundle authoring and validation.
- `okfkb` routes knowledge work; `okfkb-record-findings` captures one
  observation, while `okfkb-distill` and `okfkb-gardening` consolidate batches.
- `okfreq` covers requirement authoring and implementation;
  `okfreq-gardening` audits an existing requirements base.

Invoke a skill by naming it in your request. For example:

> Use `okfkb-record-findings` to record this observation in the current
> knowledge base: exporting 10,000 rows took 4.8 seconds with version 1.4 and
> the sample customer data set.

The agent uses the skill to gather context, edit the correct files, and run the
project-prescribed checks. Review its changes before committing them. The CLI
remains available for deterministic operations such as `validate`, `lint`, and
`update`.

## Next steps

- [Getting Started](tutorials/getting-started) — create your first bundle in under 10 minutes.
- [How-To Guides](how-to/index) — task-oriented recipes for common workflows.
