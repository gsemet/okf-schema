# OKF-KB Design Choices

`okf-schema` provides an *opinionated* instantiation of OKF as a knowledge base (through `okfkb`,
an alias for `okf-schema kb`).

This article explains the philosophy, design choices, and trade-offs behind the structure.

**Core vision**: A ready-to-use KB framework optimized for **agent-driven experimental findings traceability**
at scale in HW debugging, scientific projects, and complex engineering teams.

For step-by-step guidance on using okfkb, see:

- [Setup OKF-KB](../how-to/setup-okfkb.md) — Quick reference and command reference
- [HW Debugging Workflow Tutorial](../tutorials/okfkb-hw-debugging-workflow.md) — Real-world automotive debugging example

```{image} ../_static/generic-vs-okfkb-kb.svg
:alt: Comparison of generic knowledge base graph structure (left, chaotic) with OKF-KB stratified layers (right, organized)
:width: 100%
```

**OKF-KB organizes the elements in stratified layers**, with findings at the bottom rising through validation to principles at the top.

---

## What is a Knowledge Base?

A knowledge base is a structured, interlinked collection of markdown files containing
observations, hypotheses, validated concepts, and principles. Its purpose is to serve
as an **external memory for coding agents** when they engage with a problem domain.

Unlike a flat repository of findings or a wiki, a KB must:

1. **Encode confidence levels** — distinguish raw observations from validated concepts
2. **Support contradictions** — allow conflicting findings to coexist without requiring immediate resolution
3. **Enable navigation by tier** — agents must quickly find the right level of abstraction
4. **Preserve immutability** — historical records should not be rewritten
5. **Front-load metadata** — agents decide whether to read deep based on frontmatter alone

okfkb addresses all five by design.

---

## Knowledge Lifecycle

In okfkb, every document has a *tier* that reflects its maturity and confidence level:

| Tier | Purpose | When to Write | Confidence |
|------|---------|---------------|------------|
| **findings/** | Raw observations from debugging/experimentation | Agent detects anomaly, records via `okfkb new-finding` | Falsifiable |
| **hypotheses/** | Testable propositions derived from findings | Propose explanation for contradiction | Medium |
| **experiments/** | Planned investigations to test hypotheses | Design test; record expected outcome | Intended |
| **concepts/** | Stable understanding promoted from findings | Multiple findings converge; confidence High | High |
| **structures/** | Cross-cutting system patterns spanning multiple concepts | Architect describes subsystem | High |
| **principles/** | Durable, team-agreed standards and "directions" | Human decision; replaces ad-hoc convention | Policy |
| **outcomes/** | Planned projects or deliverables to build from knowledge | Track what you'll *build* from KB | Commitment |
| **reference/** | External sources: papers, links, third-party docs | Archive findings backed by citations | External |
| **guides/** | Operational how-to notes (orthogonal to other tiers) | Record repeatable processes | Procedural |

The key insight: **each tier answers a different question an agent might ask** —
"What did we observe?", "What's stable enough to rely on?", "What's still open?", "What must we build?"

```{image} ../_static/okfkb-hw-debugging-overview.png
:alt: OKF-KB debugging overview — debug sessions feed a stratified pyramid (findings → concepts → structures → principles), navigated with search/get/read/query
:width: 100%
```

---

## Findings: Agent-Driven Discovery

Findings are the foundational tier. They are **created by agents**, not humans.

They are immutable and timestamped.
They are the raw observations that agents record during debugging or experimentation.

Findings should be understood as the **local truth as this specific time with the available data**.
They are not "corrected" retroactively; instead, new findings may contradict older ones,
and the KB preserves the historical record.

### Agent Workflow

When an agent (GitHub Copilot, Cursor, Claude Code) detects an anomaly or completes
an investigation, it will record a new finding:

```bash
# 1. Create a new finding (timestamps and paths auto-generated)
okfkb new-finding "Cache eviction ratio exceeds threshold"

# 2. Agent edits the finding markdown and frontmatter
# (agent sets confidence, links to related docs, adds context)

# 3. Lint and update links/backlinks
okfkb update
```

### Why Agents Create Findings

Humans debugging a complex HW platform can find several mistakes and discover
several observations per session.

At the end of each session, agents record findings of this investigation.

The KB grows with:

- Exact timestamps (when was this observation made?)
- Full context (how was the system configured when this happened?)
- Confidence levels (how sure is the agent about this observation?)
- Immediate links (what other findings or concepts does this relate to?)

This transforms the KB into a **living experimental log**, not a summative document.

### Findings are Immutable and Falsifiable

Once created, a finding's **body should never be edited**.

Instead:

- If contradicted by a newer finding, the older finding gets a `status: contradicted` frontmatter field
  and a pointer to the contradicting finding in `contradicted_by: [findings/2026.07.05-...md]`
- The historical record remains intact for audit and reproducibility
- Agents can then ask: "What's the evolution of our understanding of this cache behavior?"

This principle mirrors scientific lab notebooks: observations are historical records, not
living documents that get "corrected" retroactively.

### Dated Filenames: Chronological Signal

Findings use the naming pattern `YYYY.MM.DD-HH.MM-<slug>.md`:

```
findings/2026.07.04-14.30-cache-eviction-anomaly.md
findings/2026.07.03-09.15-boot-sequence-timing-issue.md
findings/2026.07.03-08.45-ddr-initialization-hang.md
```

Two reasons:

1. **Chronological sort order** — `ls findings/` shows observations in recording order;
   agents scan recent findings first without reading file content.
2. **Immutability signal** — a dated filename signals "this body is historical".
   If a human or agent later decides to *edit* a finding's body (which shouldn't happen),
   the dated filename is an instant red flag that something's wrong.

## Promotion: From Findings to Concepts

Over time, patterns emerge. When **multiple findings converge** on the same understanding,
it's time to promote that understanding to a **Concept**.

### Example: Cache Eviction

**Day 1–3: Raw Findings**

```text
findings/2026.07.01-10.30-cache-hit-rate-drops.md
  → confidence: low
  → context: 400 RPS, eviction_ratio 0.75

findings/2026.07.02-14.15-eviction-ratio-exceeds-0.9.md
  → confidence: medium
  → context: 600 RPS, eviction_ratio 0.94
  → links: [findings/2026.07.01-10.30-cache-hit-rate-drops.md]

findings/2026.07.03-09.00-root-cause-identified.md
  → confidence: high
  → context: LRU eviction policy + insufficient memory pool at 700+ RPS
  → links: [findings/2026.07.02-14.15-eviction-ratio-exceeds-0.9.md]
```

**Day 4: Promotion to Concept**

```text
concepts/cache-eviction-under-load.md
  ---
  type: Concept
  title: Cache LRU Eviction Becomes Aggressive Above 700 RPS
  confidence: high
  status: active
  promoted_from: [findings/2026.07.01-10.30-cache-hit-rate-drops.md, ...]
  links: [structures/cache-subsystem.md, principles/cache-tuning-policy.md]
  ---

  # Concept: Cache LRU Eviction Under Load

  When system load exceeds 700 RPS, the cache's LRU eviction policy
  becomes too aggressive due to insufficient memory allocation...
```

### Promotion Matters

Without this "compilation" step, agents re-read the same findings repeatedly,
unable to distinguish stable knowledge from open questions.

**With promotion to higher tier**, agents can navigate into the KB, understanding
naturally what is still being investigated vs. what is stable enough to rely on.

---

## Trade-offs: Why This Design Over Alternatives?

### Alternative 1: Flat Repository of Findings

**Pros**: Simple, no folder structure overhead
**Cons**:

- Agents can't distinguish raw observations from validated understanding
- No canonical path for promotion (finding → concept)
- Search becomes expensive; agent must read every file to find relevant context
- Confidence signals buried in prose, not frontmatter

**okfkb**: Tiers enable agents to target the right level of abstraction immediately.

### Alternative 2: Wiki with Manual Tags

**Pros**: Familiar to most teams
**Cons**:

- Tags are loose conventions, easily violated
- No immutability guarantee; findings get "cleaned up" retroactively
- Backlinks are manual and drift out of sync
- Timestamps optional, often missing

**okfkb**: Folder structure enforces tier discipline; frontmatter-first guarantees
agent consumption; indexed backlinks prevent link rot.

### Alternative 3: Spreadsheet or Database

**Pros**: Queryable; structured fields
**Cons**:

- Not suitable for prose + context (findings need narrative)
- Not version-controllable (can't audit changes)
- Markup for code/formulas awkward
- Agents have poor native support for querying databases

**okfkb**: Markdown + YAML frontmatter is agent-native; git-friendly;
and prose context is preserved. They are also auditable and diffable.

## Frontmatter-First: Optimizing for Agent Consumption

Coding agents (GitHub Copilot, Cursor, Claude Code) load files into context windows in chunks.
When a file is large, agents typically read the first 20–50 lines and decide whether to
read further. This means **the beginning of every file is prime real estate**.

okfkb exploits this by placing structured metadata at the very top:

```markdown
---
type: Finding
title: Cache eviction too aggressive
confidence: medium
context: >-
  Observed under 800 RPS load; eviction_ratio hit 0.94.
timestamp: 2026-07-04T14:30:00Z
tags: [cache, performance]
links: [findings/2026.07.03-09.00-root-cause-identified.md]
backlinks: [structures/cache-subsystem.md]
status: active
---

# Finding: Cache eviction too aggressive
...
```

An agent loading this file sees — **before reading a single word of prose** —
the document's type, confidence, context, timestamp, and how it relates to other documents.
This is vastly better than burying metadata in headings or relying on filename conventions.

---

## Links and Backlinks: Navigation Without the Filesystem

Every okfkb file carries two arrays in its frontmatter:

- **`links`** — bundle-relative paths that *this* document explicitly references
- **`backlinks`** — paths of documents that reference *this* one

When you run `okf-schema index --path my-kb/`, the tool:

1. Scans every markdown file for its `links` array
2. For each link `A → B`, appends `A`'s path to `B`'s `backlinks` field
3. Writes an `index.md` summary (table of contents)
4. Updates `log.md` with recent changes

**Why this matters for agents**: An agent reading `concepts/cache-subsystem.md` can immediately
navigate to all related findings, experiments, and principles via frontmatter fields alone.
No filesystem traversal needed. The graph is first-class data, not hidden in prose.

---

## log.md: Temporal Entry Point

`log.md` is a chronological running log of KB changes and decisions:

```markdown
## 2026-07-04

### New Findings
- `findings/2026.07.04-14.30-cache-eviction-anomaly.md`
  Agent recorded aggressive LRU eviction at 800 RPS.

### Promotions
- `concepts/cache-eviction-under-load.md` promoted from 3 converged findings.

### Decisions
- Team decided to tune LRU pool size (see `principles/cache-tuning-policy.md`).
```

Agents reading a new KB start with `log.md` to understand **what changed recently**
before diving into individual documents. This mirrors how developers use `CHANGELOG.md`
or git commit history, but optimized for prose context.

---

## Full Agent Reading Path

When an agent is given access to an okfkb, the typical traversal is:

```text
log.md                    ← What changed recently?
  ↓
index.md                  ← What tiers exist? Overview?
  ↓
findings/                 ← Raw observations (most recent first)
  2026.07.04-*.md
  2026.07.03-*.md
  ↓ (via links/backlinks)
hypotheses/               ← Testable ideas derived from findings
  ↓
experiments/              ← Planned investigations
  ↓
concepts/                 ← Stable, promoted understanding
  (cache-subsystem.md) ← which links to...
  ↓
structures/               ← System-level patterns
  ↓
principles/               ← Team standards & policies
  ↓
outcomes/                 ← Projects to build
```

At each step, `links` and `backlinks` guide navigation. The agent builds a mental graph
from frontmatter alone, then dives into prose where needed.

---

## Why a Fixed Folder Structure?

The tier folders (`findings/`, `concepts/`, `principles/`, etc.) are opinionated
*because the folder name IS the tier*.

**Without structure**, agents must infer the maturity of each document from prose or custom tags.
**With structure**, agents know instantly: `findings/` = raw obs, `concepts/` = stable knowledge.

This enables fast filtering: "Show me only stable concepts" vs. "Show me what we're still investigating"
without parsing a single document body.

---

## Active Navigation: `search` / `get` / `read` / `query`

A stratified, linked KB is only half the story — the other half is *how* an agent consumes it.
Rather than dumping whole tier folders into a context window, okfkb exposes the KB as a small
set of **navigation tools**, so the agent actively pulls the right granularity:

- **`search`** — coarse ranked retrieval ("where might the answer be?")
- **`get`** — exact fetch of one node ("show me exactly this")
- **`read`** — read a whole stable tier ("give me the settled understanding")
- **`query`** — structured selection and graph traversal ("select by criteria / follow links")

This mirrors how the tiers already answer different questions: an agent typically `read`s the
upper, stable tiers (`principles`, `concepts`) for the big picture, `query`s or `search`es to
locate relevant nodes, and only `get`s a specific finding when it needs evidence-level detail.
The design goal is the same as everywhere else in okfkb — **let the agent decide depth cheaply**,
descending to raw findings only when the higher tiers are insufficient.

### Why a two-flavor `query`

`query` deliberately supports two small styles instead of one large query language:

- A **filter DSL** over flat frontmatter (`type:finding confidence:>=high tag:pll`) — this
  covers the overwhelmingly common case: "select nodes by tier, confidence, status, and tags."
  Because confidence is *ordinal* (`low` < `medium` < `high` < `confirmed`), range operators
  like `>=high` fall out naturally.
- An **arrow traversal** (`finding[tag=pll] -> concept -> principle`) — a pocket-Cypher over
  the `links` / `backlinks` / `promoted_from` edges that already exist in frontmatter. `->`
  follows `links`, `<-` follows `backlinks`, `^` follows promotion. This turns the implicit
  knowledge graph into something an agent can *walk* ("from these findings, what concepts did
  they promote into, and what principles govern them?").

We chose this over a full `MATCH … RETURN` grammar (Cypher) or SQL `SELECT` because the two
lightweight forms cover ~80% of real navigation needs, require no graph database, and stay
readable to non-developers. The grammar is intentionally small and **experimental** — if the
arrow form proves too limiting, a fuller path grammar can be layered on later without changing
the underlying frontmatter model.

### Why tools, not just retrieval

The alternative — a single "retrieve relevant context" step that pre-selects evidence for the
agent — leaves the agent as a passive consumer of whatever the retriever picked. Exposing the
tiers as explicit tools keeps the agent in control of *which* abstraction level to consult and
*when it has enough*, which matches how these files are meant to be read: front-loaded metadata
first, prose only where needed. This active-navigation stance is corroborated by recent memory
research (e.g. NapMem's finding that tool-based, multi-granularity navigation outperforms passive
retrieval over the same sources — see `reference/`).

---

## Summary: Why This Design?

okfkb's design choices converge on a single goal: **enable agents to build understanding
from a KB as efficiently as a human would**.

- **Tiers** answer different questions (observations vs. stable knowledge)
- **Frontmatter-first** lets agents decide depth in 20 lines
- **Immutable findings** preserve experimental truth; contradictions coexist
- **Agent-driven creation** ensures findings are fresh and contextualized
- **Automatic backlinks** prevent link rot and enable graph navigation
- **Dated filenames** signal historical record integrity
- **log.md** provides temporal context on demand

Trade-offs: more structure upfront, but dramatically lower KB maintenance burden
and much higher agent productivity at scale.
