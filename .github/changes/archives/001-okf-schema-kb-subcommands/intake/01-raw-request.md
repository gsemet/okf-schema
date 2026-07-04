# Change Request — okf-schema-kb-subcommands

**JIRA**: none
**Date**: 2026-07-03
**Source**: user-provided description

## Raw Description

I want `okf-schema kb` to be a set of subcommands specifically dedicated to setup, manage,
provide tools to agent for a special OKF bundle of type "knowledge base".
I want an alias `okfkb` = `okf-schema kb`.

First command `okfkb init` initializes the kind of structure you will find in
/Users/az02065/Projects/DevTools/copilot-session-usage/knowledge.

`okf-schema init` can take an optional parameter `--pattern kb`.
This is equivalent to `okfkb init [PATH]`.

A 'knowledge base' is a structure targeted for agent, where experimental findings can be
recorded and later analyzed and synthesized or rejected. The goal is to build the
traceability to perform any operation later.

I also want to bundle the following skills and guidelines from copilot-session-usage:
- `.github/skills/consolidate-knowledge-base`
- `.github/skills/record-finding`
- `.github/guidelines/knowledge-base.guidelines.md`

These should be installable as `okfkb-*` skills in a target project.
The guideline should be installed in the target project under
`.agents/guidelines/` (or `.github/guidelines/` if `.agents/` does not exist)
and referenced in AGENTS.md.

One copy of the skill source code and guidelines should be kept, allowing testing.
They must be properly packaged and loaded by importlib.
