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

## Install the agent skills

The skills are included in the package and installed by the command that owns
each skill family. Run the commands for the families you want to use:

```bash
okf-schema install-skills
okfkb install-skills
okfreq install-skills
```

By default, skills are installed globally under `~/.copilot/skills`. To install
them in the current project instead, choose the directory supported by your
agent:

```bash
# GitHub Copilot project skills
okf-schema install-skills --local-copilot
okfkb install-skills --local-copilot
okfreq install-skills --local-copilot

# Agent Skills project directory
okf-schema install-skills --local-agents
okfkb install-skills --local-agents
okfreq install-skills --local-agents
```

An explicit destination can be used when the project has its own skill
directory:

```bash
okf-schema install-skills ./vendor/agent-skills
```

The commands install these families:

- `okf-schema` covers generic bundle authoring and validation.
- `okfkb` includes knowledge-base authoring, findings, and consolidation skills.
- `okfreq` includes requirements authoring and requirements-maintenance skills.

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
