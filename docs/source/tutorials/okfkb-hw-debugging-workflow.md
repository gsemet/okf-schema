# OKF-KB in Practice: HW Debugging Workflow

**Real-world scenario**: Debugging a boot timing issue on an automotive SoC (MCU) board.
This tutorial shows how a team uses [OKF-KB](../explanation/okfkb-choices.md)
to capture observations, investigate contradictions,
and build stable knowledge over a multi-week debugging campaign.

```{image} ../_static/okfkb-hw-debugging-overview.png
:alt: OKF-KB debugging overview — debug sessions feed a stratified pyramid (findings → concepts → structures → principles), navigated with search/get/read/query
:width: 100%
```

> This example demonstrates **agent-driven findings creation**, **knowledge promotion**,
> and **team consensus** in a realistic HW debugging context.

## Where the Agent Skills Help

This tutorial uses the skills as a lifecycle, not as aliases for CLI commands:

| Skill | Role in the campaign |
|---|---|
| `okfkb` | Recognizes durable discoveries, chooses the correct layer, routes Finding capture, and navigates existing knowledge before new investigation. |
| `record-finding` | Captures each bounded empirical observation quickly without rewriting earlier evidence. |
| `consolidate-knowledge-base` | Offers an interactive review when engineers want to confirm each contradiction or promotion. |
| `okfkb-gardening` | Runs an explicitly requested, zero-prompt batch pass after Findings accumulate: repairs the graph, consolidates semantic knowledge, opens investigations, and validates. |
| `okf-schema` | Performs deterministic index, lint, schema-validation, and query operations underneath those workflows. |

The key boundary is governance: gardening may autonomously maintain Findings,
Hypotheses, Experiments, Concepts, Structures, Playbooks, and Outcomes, but it
only **proposes** Principles. A human team must agree before a Principle changes.

## Scenario: Boot Initialization Timeout on Automotive MCU

**Context**:

- Target: AURIX TC3xx automotive microcontroller
- Board: Renault Ampere development board
- Issue: Boot initialization sometimes hangs after ~500ms
- Frequency: ~5% of power-on cycles, intermittent
- Impact: Vehicle startup reliability affected in cold weather

**Team**:

- 2 HW engineers (debugging)
- 1 firmware architect (oversight)
- GitHub Copilot (agent, running inference on local debug logs)

## Week 1: Initial Observations (Findings Accumulation)

### Monday, 2026-07-01 — First Observation

Engineer runs a test at room temperature (25°C). The `okfkb` skill recognizes a
non-trivial empirical discovery and routes it to `record-finding`, which creates
Finding #1:

```bash
# Agent discovers timing anomaly in trace logs
okfkb new-finding "Boot initialization hangs ~500ms, sometimes recovers"
```

**Finding: 2026.07.01-09.30-boot-hangs-500ms.md**

```yaml
---
type: Finding
title: Boot initialization hangs ~500ms, sometimes recovers
description: Intermittent boot initialization stalls near 500ms at room temperature.
confidence: low
context: >
  Board: Ampere dev, AURIX TC3xx target.
  Temperature: 25°C ambient.
  Power supply: 12V nominal.
  Observed in trace: timing stall after peripheral init phase,
  variable recovery (0-100ms delay).
timestamp: 2026-07-01T09:30:00Z
tags: [boot, initialization, timeout]
links: []
backlinks: []
status: active
---
```

**Agent narrative**:

```
Boot trace shows expected sequence:
1. CPU release → PLL lock → memory init (all OK)
2. Peripheral init (watchdog, serial, GPIO)
3. [ANOMALY] ~490ms unexplained stall before DDR ready signal
4. Either timeout→reboot OR spontaneous recovery after random delay

Reproduced 2/20 power cycles at lab conditions.
Not a hard hang; watchdog has not triggered yet.
Confidence: low — too few datapoints, timing is variable.
```

### Tuesday, 2026-07-02 — Temperature Stress Test

Engineer runs thermal chamber test at 0°C. **Agent creates Finding #2**, linking to #1:

```bash
okfkb new-finding "Boot timeout occurs more frequently at 0°C"
```

**Finding: 2026.07.02-11.00-temperature-sensitivity.md**

```yaml
---
type: Finding
title: Boot timeout occurs more frequently at 0°C
description: Boot hangs become substantially more frequent as ambient temperature falls.
confidence: medium
context: >
  Thermal chamber: -10°C to +70°C sweep.
  At 0°C: boot hang observed in 8/20 cycles (40%).
  At 25°C: boot hang in 2/20 cycles (10%).
  At 50°C: no failures in 20 cycles.
  Correlation is clear.
timestamp: 2026-07-02T11:00:00Z
tags: [boot, temperature, thermal]
links:
  - findings/2026.07.01-09.30-boot-hangs-500ms.md
backlinks: []
status: active
---
```

**Agent narrative**:

```
Strong correlation with temperature.
At 0°C, failure rate jumps to 40%. This suggests either:
1. Oscillator frequency drift at low temp
2. Peripheral timing margin erosion (clock distribution, DDR setup)
3. Watchdog timeout threshold not adjusted for temperature

Confidence: medium — reproducible trend, clear correlation.
```

### Wednesday, 2026-07-03 — Oscillator Measurement

Engineer measures PLL lock time vs. temperature. **Agent creates Finding #3**:

```bash
okfkb new-finding "PLL lock time increases from 200µs to 800µs at low temperature"
```

**Finding: 2026.07.03-14.20-pll-temp-drift.md**

```yaml
---
type: Finding
title: PLL lock time increases from 200µs to 800µs at low temperature
description: Direct measurement shows PLL lock time approaching its limit at low temperature.
confidence: high
context: >
  Measured via logic analyzer on FRAC_RDY and PLL_LOCK signals.
  At 25°C: PLL lock time ~200µs (within spec).
  At 0°C: PLL lock time ~800µs (spec limit: 1000µs, but close).
  At -10°C: PLL lock time ~950µs (near spec boundary).
  Temperature coefficient: ~10µs/°C.
timestamp: 2026-07-03T14:20:00Z
tags: [pll, oscillator, temperature]
links:
  - findings/2026.07.02-11.00-temperature-sensitivity.md
  - findings/2026.07.01-09.30-boot-hangs-500ms.md
backlinks: []
status: active
---
```

**Agent narrative**:
```
Root cause emerging: PLL is within spec, but operating near the edge.
The ~500ms boot stall correlates with slow PLL lock.
If boot sequence firmware has fixed timeout (instead of polling PLL_LOCK),
and firmware timeout < actual PLL lock time, watchdog triggers.

Confidence: high — direct measurement with oscilloscope proof.
```

### Thursday-Friday — Follow-up: Firmware Analysis

Architect reviews bootloader code. **Agent creates Finding #4** (contradiction/refinement):

```bash
okfkb new-finding "Bootloader has hardcoded PLL wait timeout of 400µs, not polling"
```

**Finding: 2026.07.05-10.15-bootloader-timeout-hardcoded.md**

```yaml
---
type: Finding
title: Bootloader has hardcoded PLL wait timeout of 400µs, not polling
description: Source inspection reveals a fixed wait shorter than measured cold PLL lock times.
confidence: high
context: >
  Bootloader source (Ampere repo, BootInit.S line 427):
    WAIT 400µs    // Static delay, NOT event-driven
  TCXO stabilization time: 300µs spec,
  but measured 600-950µs in practice at low temps.

  Bootloader does NOT poll PLL_LOCK signal.
  It just waits 400µs then proceeds to DDR init.
  If PLL not ready, DDR init fails, firmware hangs.
timestamp: 2026-07-05T10:15:00Z
tags: [bootloader, firmware, pll, timeout]
links:
  - findings/2026.07.03-14.20-pll-temp-drift.md
  - findings/2026.07.02-11.00-temperature-sensitivity.md
status: active
---
```

**Agent narrative**:

```
ROOT CAUSE FOUND:
Bootloader timeout (400µs) is too short for low-temperature conditions.
PLL lock time at 0°C: 600-800µs > 400µs timeout.
Bootloader proceeds to DDR init while PLL still locking.
DDR init fails → firmware hangs → watchdog eventually triggers.

Watchdog then resets MCU. On reboot, if PLL happens to lock faster
(thermally transient), boot succeeds — explaining intermittency.

This is a DESIGN BUG, not a hardware defect.
Confidence: high — source code proof + measurements validate.
```

## Week 2: Skill-Assisted Consolidation

### Monday, 2026-07-08 — Autonomous Gardening Pass

Four related Findings have accumulated. The team explicitly asks:

> Garden this OKFKB.

`okfkb-gardening` reads the project rules and local schemas, establishes a
validation baseline, clusters the Findings, and judges that the measurements
and source evidence converge. Without pausing for questions, it promotes the
stable explanation into a Concept, creates supporting Structure and Outcome
documents, refreshes graph metadata, and validates the result.

The promotion does not depend mechanically on “four” Findings. The skill weighs
evidence quality, independence, scope, counter-evidence, and reuse value. Had
the cause remained ambiguous, it would have created a Hypothesis and Experiment
instead of forcing a Concept.

```bash
# Create concept consolidating all findings
cat > concepts/boot-pll-startup-margin.md << 'EOF'
---
type: Concept
title: Boot Initialization Timing Margin: PLL Lock at Low Temperature
description: Cold PLL lock time exceeds the bootloader's fixed wait and causes intermittent boot failure.
derived_from:
  - findings/2026.07.01-09.30-boot-hangs-500ms.md
  - findings/2026.07.02-11.00-temperature-sensitivity.md
  - findings/2026.07.03-14.20-pll-temp-drift.md
  - findings/2026.07.05-10.15-bootloader-timeout-hardcoded.md
links:
  - structures/boot-sequence-architecture.md
  - principles/firmware-timeouts-must-be-polled.md
  - outcomes/fix-bootloader-pll-polling.md
backlinks: []
status: active
---

# Concept: Boot Initialization Timing Margin: PLL Lock at Low Temperature

## Summary

The AURIX TC3xx bootloader uses a hardcoded 400µs wait for PLL lock.
Under low-temperature conditions (0–-10°C), actual PLL lock time increases
to 600–950µs due to TCXO frequency drift. This margin violation causes boot
initialization to fail intermittently, with frequency increasing as temperature drops.

## Evidence

- **Measurement**: PLL lock time: 200µs @ 25°C → 950µs @ -10°C (5×margin erosion)
- **Source code**: Bootloader implements static WAIT, not event-polling
- **Thermal correlation**: Failure rate 10% @ 25°C, 40% @ 0°C, 0% @ 50°C
- **Intermittency**: Watchdog recovery on subsequent boot attempts explains sporadic success

## Root Cause

Bootloader timeout specification does not account for temperature-dependent oscillator drift.
No polling of PLL_LOCK signal; instead, hardcoded delay assumes worst-case PLL lock time.
Specification assumed lab conditions (25°C) only.

## Fix Required

Replace hardcoded WAIT with event-driven polling of PLL_LOCK signal.
Add minimum timeout of 1200µs (worst case: -10°C + margin).
EOF

okfkb update concepts/boot-pll-startup-margin.md
```

### Gardening Creates Supporting Documents

**Structure Document** (system composition):

```bash
cat > structures/boot-sequence-architecture.md << 'EOF'
---
type: Structure
title: Boot Sequence Architecture
description: Boot phases and timing dependencies from CPU release to application start.
status: active
derived_from:
  - findings/2026.07.03-14.20-pll-temp-drift.md
  - findings/2026.07.05-10.15-bootloader-timeout-hardcoded.md
links:
  - concepts/boot-pll-startup-margin.md
  - concepts/ddr-initialization-flow.md
  - concepts/watchdog-timing-budget.md
backlinks: []
---

# Boot Sequence Architecture

## Phases

1. **CPU Release** (immediate)
   - MCU power-up, internal reset release

2. **PLL Lock** ← Critical path for timing
   - TCXO stabilization (300µs spec, measured 600-950µs at low temp)
   - PLL feedback lock (~50µs, stable)
   - Total: 200µs @ 25°C, 950µs @ -10°C

3. **Memory Initialization**
   - DDR controller init (requires stable PLL clock)
   - DDR training (if enabled)
   - Total: ~1ms

4. **Peripheral Init**
   - Watchdog, UART, GPIO config
   - Total: ~100µs

5. **Application Start**
   - Jump to firmware (FBL/SBL/app)

## Current Bottleneck

PLL lock phase has insufficient margin at low temperature.
See `concepts/boot-pll-startup-margin.md` for details.
EOF

okfkb update structures/boot-sequence-architecture.md
```

### Gardening Proposes a Principle

The same evidence suggests a normative rule: hardware-readiness delays should
be event-driven rather than hardcoded. Gardening includes the proposed wording,
rationale, and supporting Findings in its final chat report, but does not write
the Principle.

The firmware architect and engineers explicitly agree with the proposal. Only
then is the **Principle document** created:

```bash
cat > principles/firmware-timeouts-must-be-polled.md << 'EOF'
---
type: Principle
title: Firmware Timeouts Must Be Event-Driven, Not Hardcoded
description: Hardware readiness must be polled with a bounded safety timeout rather than assumed through fixed delays.
rationale: Fixed delays fail under temperature, voltage, and process variation.
authority: firmware architect and engineering team, 2026-07-08
supported_by:
  - findings/2026.07.03-14.20-pll-temp-drift.md
  - findings/2026.07.05-10.15-bootloader-timeout-hardcoded.md
---

# Principle: Firmware Timeouts Must Be Event-Driven, Not Hardcoded

## Policy

All firmware delays that depend on hardware readiness must:
1. Poll the readiness signal (e.g., PLL_LOCK, DDR_READY)
2. Have a safety timeout (max wait time) as fallback only
3. Not assume fixed timing for events subject to temperature/voltage/process variation

## Rationale

Hardcoded delays become timing bombs under environmental stress:
- Temperature extremes (automotive: -40°C to +85°C)
- Supply voltage variation (cold-start, load transients)
- Manufacturing process corner variations

See `concepts/boot-pll-startup-margin.md` for cautionary example.

## Effective Immediately

All new bootloader code must follow this pattern.
EOF

okfkb update principles/firmware-timeouts-must-be-polled.md
```

**Outcome Document** (planned deliverable):

```bash
cat > outcomes/fix-bootloader-pll-polling.md << 'EOF'
---
type: Outcome
title: Fix Bootloader PLL Initialization to Use Event Polling
description: Replace the fixed PLL wait with bounded event-driven polling and validate it thermally.
derived_from:
  - concepts/boot-pll-startup-margin.md
status: planned
deliverable: Bootloader change and thermal validation evidence by 2026-07-22.
---

# Outcome: Fix Bootloader PLL Initialization

## Requirement

Replace hardcoded PLL wait (400µs) with:
1. Poll PLL_LOCK signal
2. Timeout: 1200µs (worst case -10°C + 20% margin)
3. Fallback: reboot if timeout

## Acceptance Criteria

- Boot success rate ≥99.9% across full temperature range (-10°C to +70°C)
- At least 50 successful boot cycles per temperature point
- Bootloader code review by architect
- Integration into main branch by 2026-07-22

## Assignee

Firmware team (Renault Ampere)
EOF

okfkb update outcomes/fix-bootloader-pll-polling.md
```

### Index, Validate, and Review

```bash
# Refresh indexes, links, backlinks, and frontmatter
okfkb update .

# Strictly validate all documents
okfkb validate .

# Review significant semantic changes
cat log.md
```

The gardening skill discovers the equivalent project-prescribed commands from
`AGENTS.md`; it does not assume every repository uses these exact invocations.

## Week 3: Implementation & Validation

### Tuesday, 2026-07-15 — Implementation Complete

Engineer submits bootloader fix (event-driven PLL polling). **Agent creates validation finding**:

```bash
okfkb new-finding "Bootloader fix validated: 100 boot cycles at -10°C, 0 failures"
```

**Finding: 2026.07.15-16.45-fix-validation.md**

```yaml
---
type: Finding
title: Bootloader fix validated: 100 boot cycles at -10°C, 0 failures
description: Thermal validation records zero boot failures after event-driven PLL polling was introduced.
confidence: high
context: >
  Test: Thermal chamber -10°C sustained, 100 power-on cycles.
  Result: 100% success rate (previously ~60% failure at -10°C).
  Fix: Bootloader now polls PLL_LOCK instead of hardcoded 400µs wait.
  Actual timeout: ~1100µs (within new 1200µs spec).
timestamp: 2026-07-15T16:45:00Z
tags: [boot, validation, fix-verified]
links:
  - outcomes/fix-bootloader-pll-polling.md
  - concepts/boot-pll-startup-margin.md
backlinks: []
status: active
---
```

### Wednesday, 2026-07-16 — Refresh Living Knowledge

The team invokes gardening again. The validation Finding does not rewrite any
earlier Finding. Instead, gardening updates the living Concept in place, adds
the new Finding to `derived_from`, records the fix and validation boundary in
the Concept body, and moves the Outcome from `planned` to `done`.

```bash
okfkb update .
okfkb validate .
```

Concepts remain `active` while they describe valid understanding; “the incident
was fixed” belongs in their content and linked evidence, not in an unsupported
`resolved` status.

## What Happened in the KB

### Findings Layer (Raw Evidence)

```text
findings/
├── 2026.07.01-09.30-boot-hangs-500ms.md              ← Initial observation
├── 2026.07.02-11.00-temperature-sensitivity.md       ← Correlation identified
├── 2026.07.03-14.20-pll-temp-drift.md                ← Measurement proof
├── 2026.07.05-10.15-bootloader-timeout-hardcoded.md  ← Root cause found
└── 2026.07.15-16.45-fix-validation.md                ← Fix verified
```

### Concepts Layer (Consolidated Understanding)

```text
concepts/
└── boot-pll-startup-margin.md  ← Promoted from 4 converged findings
                                   (active, updated with fix evidence)
```

### Structures Layer (System Knowledge)

```text
structures/
└── boot-sequence-architecture.md  ← Reusable blueprint for future debugging
```

### Principles Layer (Team Standards)

```text
principles/
└── firmware-timeouts-must-be-polled.md  ← Inviolable rule going forward
```

### Outcomes Layer (Deliverables)

```text
outcomes/
└── fix-bootloader-pll-polling.md  ← Tracked from plan → complete
```

## Key Workflow Patterns Demonstrated

### 1. **Findings Accumulate Incrementally**

- Day 1: Observation (low confidence)
- Day 2: Correlation identified (medium confidence)
- Day 3: Root cause measurement (high confidence)
- Day 5: Source code proof (confirms understanding)

**Agent benefits**: Fresh timestamps, exact context, confidence progression visible.

### 2. **Promotion Triggers When Convergence Occurs**

After the Findings align, gardening promotes the stable understanding using
agent judgment about evidence quality, scope, and reuse value.

**Structure enables**: Evidence provenance and `log.md` leave an audit trail.
Interactive teams can use `consolidate-knowledge-base` instead when they want to
confirm each mutation.

### 3. **Contradictions Don't Break the Process**

If Day 6 brought contradictory evidence, the old findings would be marked:

```yaml
status: contradicted
contradicted_by: [findings/2026.07.06-new-finding.md]
```

Both remain immutable; agents can trace the evolution of understanding.

### 4. **Principles Capture Team Consensus**

Gardening proposes **"No more hardcoded firmware timeouts."** with supporting
evidence. The architect and team agree, making it a human-governed decision.
This becomes an inviolable rule (`principles/`), shaping future architecture decisions.

### 5. **Outcomes Track What We'll Build**

Fix is planned, executed, and marked complete — all linked to the KB concepts that justified it.

## Navigation Over Time

**At any point**, an agent (or human) loading this KB can ask:

- **"What do we know for sure?"** → Read active `concepts/` and follow their evidence links
- **"What's still uncertain?"** → Read `findings/` with low confidence; read `experiments/` for open questions
- **"What must we never do again?"** → Read `principles/`
- **"What are we building?"** → Read `outcomes/`, sorted by status

Instead of `cat`-ing folders by hand, the agent uses the KB **navigation tools** to pull
exactly the right granularity:

```bash
# "What do we know for sure?" — read the active semantic tier
okfkb read concepts --status active

# "What must we never do again?"
okfkb read principles --format titles

# Find the high-confidence evidence behind the boot issue
okfkb query "type:finding confidence:>=high tag:pll status:active"

# Fetch the stable synthesis and inspect its derived_from evidence
okfkb get concepts/boot-pll-startup-margin.md --format frontmatter

# Coarse search, then drill into one exact node
okfkb search "pll lock time" --tier findings
okfkb get findings/2026.07.03-14.20-pll-temp-drift.md
```

**One week later**, a new engineer joins. They read:

1. `log.md` — recent decisions
2. `index.md` — KB structure
3. `concepts/boot-pll-startup-margin.md` — the stable understanding
4. `findings/` links from concept — the evidence trail

No need to re-investigate. The KB preserved context, confidence, and reasoning.

## Scaling This Workflow

**One month, multiple features**:

```text
findings/ → 40+ raw observations
hypotheses/ → 8 testable propositions
experiments/ → 3 active investigations
concepts/ → 6 stable understandings
principles/ → 2 team decisions
outcomes/ → 4 planned features (2 in_progress, 1 done)
```

**Log.md** becomes essential: team reads it every Monday to see what shifted.
**Backlinks** help agents jump from "Does DDR init depend on PLL?" directly to the answer.

## Next Steps

For hands-on practice:

1. Create an empty KB: `okfkb init my-project-kb`
2. Make the `okfkb` skill available and investigate one real problem
3. Let it route durable observations to `record-finding`
4. After several Findings accumulate, explicitly invoke `okfkb-gardening`
5. Review any Principle proposal and make the human governance decision

See [Setup OKF-KB](../how-to/setup-okfkb.md) for commands.
See [Maintain an OKFKB with agent skills](../how-to/maintain-okfkb-with-skills.md)
for the recurring capture, consolidation, and gardening workflow.
See [OKF-KB Design Choices](../explanation/okfkb-choices.md) for philosophy.
