# Record Your First Finding in OKF-KB

OKF-KB is an opinionated OKF bundle for evidence-based knowledge. It stores raw
observations as **Findings** before they are turned into stable explanations or
team rules. Keeping the observation separate prevents an early guess from
silently becoming accepted knowledge.

In this tutorial, you will create a knowledge base and record one Finding.

**Time:** about 10 minutes

**Prerequisite:** Follow the [installation guide](../installation.md) to install
`okf-schema` and manually add the `okfkb`, `okfkb-record-findings`, and
`okf-schema` skills to your project.

## Create the knowledge base

```bash
mkdir my-kb
cd my-kb
okfkb init
```

The command creates indexes and folders for several knowledge layers:

```text
my-kb/
├── index.md
├── log.md
├── findings/
├── hypotheses/
├── experiments/
├── concepts/
├── structures/
├── principles/
├── playbooks/
└── outcomes/
```

You only need `findings/` for this tutorial.

## Tell the agent what you observed

Imagine that users report slow exports. A timing measurement shows that a
10,000-row export took 4.8 seconds. Tell your coding agent:

> Use `okfkb-record-findings` to record one Finding in the current knowledge
> base: exporting 10,000 rows took 4.8 seconds. I measured it locally with
> version 1.4 and the sample customer data set. The measurement is repeatable,
> so use high confidence. Do not infer a root cause.

The skill tells the agent to preserve the observation, tested context, and
limits without turning a guess into stable knowledge. The agent creates the
timestamped Finding, completes its body, and runs the checks prescribed by the
project.

You can perform the deterministic file-creation step yourself instead:

```bash
okfkb new-finding . \
    --title "Exporting 10,000 rows takes 4.8 seconds" \
    --confidence high \
    --context "Measured locally with version 1.4 and the sample customer data set."
```

The command creates a timestamped file under `findings/`. Its frontmatter is
similar to:

```yaml
type: Finding
title: Exporting 10,000 rows takes 4.8 seconds
description: Exporting 10,000 rows takes 4.8 seconds
confidence: high
context: Measured locally with version 1.4 and the sample customer data set.
tags: []
links: []
backlinks: []
kb_status: active
```

The title states what was observed. The context records the conditions under
which it was true. Confidence describes the evidence, not how strongly someone
believes the explanation.

If you used the command directly, open the created file and complete its body
with the measurement procedure, result, and limits. Alternatively, ask the
agent to use `okfkb-record-findings` to complete it. Do not add a root-cause
claim unless you observed evidence for it.

## Update and validate

If the agent has already run the project checks, review their output. Otherwise,
refresh indexes and generated graph fields:

```bash
okfkb update .
```

Then validate the knowledge base:

```bash
okfkb validate .
```

You now have one indexed, validated observation. Later Findings may support an
explanation, contradict this observation, or show that it only applies in a
specific environment. The original Finding remains an evidence record.

## Inspect the result

Search for the Finding:

```bash
okfkb search "10,000 rows" --tier findings
```

Use the returned path to read the complete document:

```bash
okfkb get findings/<timestamp>-exporting-10-000-rows-takes-4-8-seconds.md
```

Replace the placeholder with the filename created on your machine.

## If validation fails

Check that you ran the command from the knowledge-base root and that the
Finding still contains its generated fields. Keep the timestamped filename and
required frontmatter fields created by `new-finding`.

## Next steps

- [Hardware Debugging Case Study](okfkb-hw-debugging-workflow.md) follows
  several Findings through investigation, consolidation, and validation.
- [Set Up an OKF-KB](../how-to/setup-okfkb.md) lists the knowledge layers and
  navigation commands.
- [Maintain an OKF-KB with Agent Skills](../how-to/maintain-okfkb-with-skills.md)
  covers recurring capture and consolidation workflows.
- [Why an Opinionated Knowledge Base?](../explanation/okfkb-choices.md)
  explains the model and governance boundaries.
