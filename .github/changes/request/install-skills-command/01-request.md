# Install packaged agent skills

## Original request

Add an `install-skills` command in `okf-schema` with these requirements:

- Package the skills inside the Python wheel and access them through
  `importlib.resources`.
- Add `okf-schema install-skills` to install the `okf-schema` skill.
- Add `okfkb install-skills` to install the `okfkb-*` skills.
- Add `okfreq install-skills` to install the `okfreq-*` skills.
- Default to the Copilot installation path `~/.copilot/skills`, equivalent to
  `--agent-copilot`, while allowing other agent kinds later.
- When a path is provided, create the skill folders there.
- Add `--local-copilot` for `.github/skills`.
- Add `--local-agents` for `.agents/skills`.
- Update the `okf-schema`, `okfreq`, and `okfkb` skills to explain how to
  install the CLI with `uv tool install`.

## Interview scope

The interview clarified skill-family ownership, destination semantics,
replacement and failure behavior, migration of the existing `okfkb`
installer, command output, wheel resources, and documentation expectations.
No implementation was performed during the interview.