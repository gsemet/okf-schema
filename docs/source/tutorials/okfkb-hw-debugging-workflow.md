# Case Study: Debugging a Hardware Boot Failure with OKF-KB

This case study shows how an engineering team uses OKF-KB over several sessions.
It is a narrative example, not a command-by-command introduction. Complete
[Record Your First Finding](okfkb-first-finding.md) first.

## Case study

An automotive controller intermittently hangs during startup, especially in
cold conditions. The team needs to separate measurements from guesses, find the
cause, and preserve the result for future engineers.

Four hardware terms appear in the story:

- **MCU:** the controller running the boot software;
- **PLL:** circuitry that produces a stable clock signal;
- **DDR:** memory that depends on that stable clock; and
- **TCXO:** the oscillator that supplies the initial timing reference.

## Session 1: Accumulate evidence

The team records each bounded observation as a separate Finding. It does not
rewrite earlier Findings when understanding changes.

After each test or inspection, an engineer describes exactly what happened to
the coding agent and asks it to use `/okfkb-record-findings` skill. The skill captures
one immutable observation at a time and runs the knowledge-base checks. The
engineer reviews the generated Finding before committing it.

### Initial observation

At room temperature, 2 of 20 power-on cycles stall during startup. The first
Finding records the board, temperature, power supply, trace position, and small
sample size. Its confidence is low.

The engineer tells the agent:

> Use `/okfkb-record-findings` skill to record one Finding. On the development board,
> 2 of 20 power-on cycles stalled for about 500 ms at 25 C with a 12 V supply.
> The trace stalled after peripheral initialization. Use low confidence because
> the sample is small. Record only the observation, not a root-cause theory.

The agent creates and validates a Finding similar to this excerpt:

```yaml
type: Finding
title: Boot initialization sometimes stalls for about 500 ms
confidence: low
context: 2 failures in 20 cycles at 25 C on the development board.
tags: [boot, initialization]
kb_status: active
```

### Temperature correlation

The next test varies temperature. Failures occur in 8 of 20 cycles at 0 C, 2
of 20 at 25 C, and none at 50 C. The second Finding links to the first and has
medium confidence: the trend is repeatable, but it does not yet identify a
cause. The engineer gives those measurements to the agent and again asks it to
use `/okfkb-record-findings` skill, this time linking the new Finding to the initial
observation.

### Direct measurement

An engineer measures PLL lock time:

| Temperature | Lock time |
| --- | ---: |
| 25 C | about 200 microseconds |
| 0 C | about 800 microseconds |
| -10 C | about 950 microseconds |

This high-confidence Finding establishes that the clock becomes ready later in
cold conditions. The engineer asks the agent to use `/okfkb-record-findings` skill and
includes the measurement method, signals observed, temperatures, values, and
equipment. Those details make the Finding reproducible and justify the higher
confidence.

### Source inspection

The bootloader contains a fixed 400-microsecond wait instead of checking the
PLL-ready signal. This fourth Finding connects source evidence to the measured
timing. The engineer asks the agent to use `/okfkb-record-findings` skill, points it to
the exact source location, and asks it to link the new Finding to the PLL timing
measurement:

```yaml
type: Finding
title: Bootloader waits 400 microseconds without checking PLL lock
confidence: high
derived_from: []
links:
  - findings/<pll-lock-measurement>.md
kb_status: active
```

The evidence now supports a coherent explanation: in cold conditions, the
bootloader starts DDR initialization before the clock is stable.

## Session 2: Consolidate understanding

The team explicitly asks the `okfkb-gardening` workflow to review the
accumulated evidence. The workflow weighs evidence quality, independence,
counter-evidence, and reuse value. It does not promote knowledge merely because
a particular number of Findings exists.

Because the measurements and source inspection agree, gardening creates a
Concept that records the stable explanation:

```yaml
type: Concept
title: Cold PLL lock time exceeds the bootloader wait
description: The fixed wait lets DDR initialization start before the clock is stable.
derived_from:
  - findings/<initial-stall>
  - findings/<temperature-correlation>
  - findings/<pll-lock-measurement>
  - findings/<fixed-wait-source-inspection>
kb_status: active
```

The Concept authors `derived_from`. After `okfkb update .`, each source Finding
receives the reciprocal generated `derives_to` edge. This keeps the evidence
trail navigable in both directions.

Gardening also creates:

- a **Structure** describing the boot sequence and timing dependencies; and
- an **Outcome** to replace the fixed wait with bounded polling and validate
  it across the required temperature range.

The evidence suggests a general rule: hardware readiness should be checked,
not assumed through fixed delays. Gardening only proposes this as a Principle.
Principles are governance decisions, so the firmware architect and engineering
team must explicitly agree before the document is created. If the team wants to
review every proposed mutation, it asks the agent to use `okfkb-distill`
instead of the autonomous gardening workflow.

## Session 3: Validate the fix

The bootloader is changed to poll the PLL-ready signal with a safety timeout.
The team runs 100 power-on cycles at -10 C and observes no failures. It records
that result as a new high-confidence Finding rather than editing the original
failure observations. An engineer gives the test conditions and result to the
agent and asks it to use `/okfkb-record-findings` skill again.

During the next gardening pass:

- the validation Finding is added to the Concept's evidence;
- the Concept body records the implemented fix and tested boundary; and
- the Outcome moves from `planned` to `done`.

The Concept remains `active` because its explanation is still valid. The fact
that the incident is fixed belongs in its content and linked evidence.

## Resulting knowledge graph

```text
Findings: observations, measurements, source inspection, fix validation
    ↓ derived_from / derives_to
Concept: cold PLL lock exceeds the fixed bootloader wait
    ├── Structure: boot sequence and timing dependencies
    ├── Outcome: implement and validate bounded PLL polling
    └── Principle: poll hardware readiness (human-approved)
```

A new engineer can start from the active Concept, follow `derived_from` to
inspect the measurements, and see the completed Outcome. They do not need to
reconstruct the investigation from chat logs or source history.

## Patterns demonstrated

1. Findings preserve observations without being rewritten into conclusions.
2. Confidence follows evidence quality, not narrative certainty.
3. Stable Concepts cite the Findings from which they were derived.
4. Contradictory evidence remains visible and can change lifecycle metadata.
5. Principles require human agreement even when an agent proposes them.
6. Outcomes connect accepted knowledge to planned and completed work.

## Continue learning

- [Maintain an OKF-KB with Agent Skills](../how-to/maintain-okfkb-with-skills.md)
  explains capture, interactive distillation, and autonomous gardening.
- [Set Up an OKF-KB](../how-to/setup-okfkb.md) provides the command reference
  for initialization and navigation.
- [OKF-KB Design Choices](../explanation/okfkb-choices.md) explains promotion,
  lifecycle, and governance in depth.
