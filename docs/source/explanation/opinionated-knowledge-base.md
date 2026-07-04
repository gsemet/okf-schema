# Why an Opinionated Knowledge Base?

`okfkb` bundles an *opinionated* subset of OKF — a fixed folder structure, a
specific set of document types, and conventions about how files are named and
linked. This article explains the reasoning behind those choices.

**Goal**: provide a ready-to-use knowledge base structure that that is directly
applicable to agent-driven experimental findings traceability, and that can be
used at scale in scientific and engineering projects.

For instance, debugging on a HW platform often requires huge knowledge,
and previous experiences are really important. Letting the agent dumps
reports does not allow to easily build a source of experimental truth.

## What is a Knowledge Base?

A knowledge base is a collection of markdown files that contain structured
and highly interlinked information.

It is meant to be read by coding agents when when they start a new session
on a particular matter.

It is highly inspirated by the LLM Wiki movement we can see, for instance
with Karpathy's [LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f). But a successful structure is never
really given and explained.

My goal when provided this highly opinionated structure is to provide a ready-to-use example of how to set up this knowledge base, and how
to maintain and scale it.

## Key principles

- **Frontmatter-first** — See next section
- **Informational hierarchy** — Experiments, findings, concepts, principles
  are NOT on the same level. They need to be clearly linked together.
- **Links and backlinks** — Every document should be able to point to related documents, back and forth.

## What are findings?

When debugging, investigating on a non-trivial issues, or trying to understand a complex system, you often need to record observations and experimental results. These are called **findings**.

They are worthful because they are the raw material from which concepts and principles are derived. They are however **falsifiable**, meaning the understaning of a system at a moment MIGHT be invalidated later with new informations.

For example, let's say you are debugging a HW platform with multiple SoC with
specific timing and poor documentation. You might have an understanding of
what works well (flash, boot, initialisation,... ) and suddently you observe a new behaviour that contradicts your previous understanding. After a intense
debugging session, you understand why it happens, and you can now record this new understanding as a **finding**.

Later on another session, accessing this finding is important so it needs to
be indexed and linked so Coding Agent will load it naturally.

However, on another session you might end with a new behavior that contradicts
what you though (ex: the correct boot sequence if slightly different).
You will do the correction yourself but you need to "teach the coding agent".

You will record findings are findings, some might contradict others, and link
them to more general concepts and principles.

In a nutshell:

- **findings** are raw observations, they are the "what happened" and "why it happened" at a given time. The "why" should be understood as "at that specific
time, in this specific context, with the information available at this point, this is what we understood". They are **falsifiable information**. Findings
are **immutable**, even when contradicted by new findings. The frontmatter
will points to the contradicting findings. But **Findings are NOT corrected**.

- **Concepts** are more general, they are the "what is happening" and "why it is happening". They should be considered as true until a new finding, or several
concurrent findings, contradicts them. They will be **updated** to reflect
the new understanding.

- **Principles** are very general "directions" human gives. They are statements
that humans consider as true.

## Why OKF and markdown with frontmatter?

Coding agents (GitHub Copilot, Cursor, Claude Code, and similar tools) load
files into their context window in chunks. When a file is large, the agent
typically reads the first 20–50 lines and decides whether to read further.
This means **the beginning of every markdown file is prime real estate**.

OKF exploits this by placing YAML frontmatter at the very top:

```markdown
---
type: Finding
title: Cache eviction too aggressive
confidence: medium
context: >-
  Observed under 800 RPS load; eviction_ratio hit 0.94.
timestamp: 2026-07-04T14:30:00Z
tags: [cache, performance]
links: []
backlinks: [structures/cache-behaviour.md]
status: active
---

# Finding: Cache eviction too aggressive
...
```

An agent loading this file sees — before reading a single word of prose —
the document type, its confidence level, context, when it was recorded,
how it relates to other documents (`links`, `backlinks`), and whether it
is still active or has been contradicted. This is the opposite of burying
metadata in the body or relying on filename conventions.

---

## How `okfkb` maintains links and backlinks

Every KB file carries two arrays in its frontmatter:

- **`links`** — bundle-relative paths that *this* document explicitly references.
- **`backlinks`** — paths of other documents that reference *this* document.

`okf-schema index` computes backlinks automatically. When you run:

```bash
okf-schema index --path my-kb/
```

the tool:

1. Scans every markdown file for its `links` array.
2. For each link `A → B`, appends `A`'s path to `B`'s `backlinks` field.
3. Writes a summary to `index.md` (the bundle's table of contents).

This means an agent reading any file in the bundle can immediately navigate
to related documents without traversing the filesystem. Both directions of
every relationship are first-class frontmatter fields, visible in the first
screen of every file.

---

## Why a fixed folder structure?

The KB layout (`findings/`, `concepts/`, `experiments/`, `structures/`, …)
is opinionated because the folder name is the document's *tier* in a
knowledge lifecycle:

| Folder | Purpose |
|--------|---------|
| `findings/` | Raw, immutable observations — what happened, when, how confident |
| `experiments/` | Planned or in-progress investigations |
| `concepts/` | Stable, well-understood ideas promoted from findings |
| `structures/` | Cross-cutting patterns that span multiple concepts |
| `principles/` | Durable, high-confidence conclusions |
| `ideas/` | Unvetted hypotheses, not yet findings |
| `reference/` | External sources, papers, links |
| `guides/` | Operational how-to notes |

An agent that reads `index.md` sees this tier structure immediately and can
navigate to the right folder for its task — reading stable knowledge
(`concepts/`) vs. open questions (`experiments/`) vs. raw evidence
(`findings/`).

---

## Why dated filenames for Findings?

Findings use the pattern `YYYY.MM.DD-HH.MM-<slug>.md` for two reasons:

1. **Chronological sort order** — `ls findings/` returns observations in
   recording order. Agents can scan the most recent findings first without
   reading any file content.
2. **Immutability signal** — a dated filename signals that the file's *body*
   should not be edited after creation (only lifecycle frontmatter like
   `status` or `contradicted_by` is appended). This matches the OKF Finding
   contract: observations are historical records, not living documents.

---

## Why `log.md`?

`log.md` is a chronological entry point: a human-maintained running log of
additions and decisions. Agents reading a new KB start with `log.md` to get
temporal context — what changed recently — before diving into individual
documents.

This mirrors how developers use `CHANGELOG.md` or git commit history, but
inside the bundle and optimised for prose context.

---

## The full agent reading path

When a coding agent is given access to a KB, the typical traversal is:

```
index.md       ← table of contents, folder overview
log.md         ← what changed recently
findings/ ↓    ← raw evidence, most recent first
  2026.07.04-*.md
  2026.07.03-*.md
concepts/ ↓    ← stable, promoted knowledge
  cache-behaviour.md
  ...
```

At each step, the `links` and `backlinks` arrays guide the agent to related
documents without requiring it to enumerate the filesystem. The agent builds
a local graph from frontmatter alone — no special tooling required.

---

## Further reading

- [KB Commands reference](../reference/kb-commands) — CLI reference for `okfkb`.
- [Bootstrap a knowledge base](../how-to/bootstrap-knowledge-base) — step-by-step setup guide.
- [Design Principles](design-principles) — broader OKF-Schema design philosophy.
