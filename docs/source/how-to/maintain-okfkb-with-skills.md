# Maintain an OKFKB with agent skills

OKFKB combines deterministic CLI operations with agent skills that understand
how empirical knowledge matures. The CLI validates files and maintains indexes;
the skills decide whether an observation should become a Finding, when evidence
is stable enough for a Concept or Structure, and what must remain a human
choice.

## Choose the right skill

| Skill | Responsibility |
|---|---|
| `okf-schema` | CLI/API mechanics, schemas, conformance, frontmatter, links, indexing, and validation. |
| `okfkb` | Knowledge-lifecycle guidance and routing to the smallest appropriate workflow. |
| `record-finding` | Fast capture of one dated empirical Finding after an investigation. |
| `consolidate-knowledge-base` | Interactive contradiction and promotion review with human confirmation. |
| `okfkb-gardening` | Explicitly invoked, autonomous, zero-prompt batch maintenance. |

The repository skills are documented in
[`skills/README.md`](https://github.com/gsemet/okf-schema/blob/main/skills/README.md).
`record-finding` and `consolidate-knowledge-base` are bundled skills that can be
deployed into a project with `okfkb install-skills`.

## 1. Prepare the project

Initialize the KB and install its project-local capture and consolidation
workflows:

```bash
okfkb init knowledge
okfkb install-skills .
```

Ensure the project `AGENTS.md` points to its KB guidelines and prescribed
maintenance commands. The skills read these local rules before mutating the KB;
they do not assume every project uses the same `just`, `make`, or shell targets.

Make the repository-level `okfkb` and `okfkb-gardening` skills available through
your agent environment. The former teaches and routes; the latter performs the
periodic autonomous pass.

## 2. Capture discoveries while working

Use `okfkb` during debugging, investigation, or verification. At task completion
it assesses whether a discovery is empirical, non-trivial, reusable, bounded,
and absent from the KB. Valuable observations are routed to `record-finding`.

A Finding records the local truth at time $T$:

- what was observed;
- the environment and tested scope;
- confidence at capture time;
- evidence, caveats, and why it matters.

Its body and claim become immutable. A later correction is another Finding with
contradiction or supersession links; history is never rewritten.

## 3. Read from stable knowledge down to evidence

Avoid loading all Findings. Begin with the stable layers, then descend only when
needed:

```bash
okfkb read principles --format titles
okfkb read concepts --status active
okfkb search "pll lock time" --tier findings
okfkb get findings/2026.07.03-14.20-pll-temp-drift.md
```

Use `query` for metadata filtering and graph traversal. This keeps context small
while preserving access to evidence.

## 4. Consolidate after Findings accumulate

Choose one of two modes:

### Interactive consolidation

Invoke `consolidate-knowledge-base` when a human wants to review each proposed
contradiction, Experiment, or promotion before it is written.

### Autonomous gardening

Explicitly ask the agent to garden the KB, for example:

> Garden the OKFKB in `knowledge/`.

`okfkb-gardening` then runs without intermediate questions. It:

1. discovers the KB root, schemas, `AGENTS.md`, and required checks;
2. establishes a validation baseline;
3. repairs unambiguous link, backlink, redirect, and index issues;
4. reconciles Finding contradiction and supersession metadata;
5. creates Hypotheses and Experiments for unresolved questions;
6. creates or updates Concepts and Structures when evidence converges;
7. refreshes Playbooks and Outcomes when justified;
8. logs significant semantic changes;
9. validates, repairs failures, and reports the final state in chat.

Promotion is qualitative judgment, not a fixed Finding count. The agent considers
evidence quality, independence, scope, counter-evidence, uncertainty, and reuse
value.

## 5. Keep Principles human-governed

Neither `okfkb` nor gardening may create or change a Principle autonomously.
Gardening can report a proposal containing:

- proposed normative wording;
- rationale;
- supporting Finding IDs;
- expected impact;
- the explicit decision required from a human.

Only after a human agrees should the Principle be written or changed.

## 6. Validate using project rules

After mutations, the skill runs the commands prescribed by the target project's
`AGENTS.md` and linked guidelines. If its changes fail validation, it attempts
bounded repairs and reruns the checks. Unresolved failures remain visible in the
diff and final report; the skill must not claim success or overwrite unrelated
user work.

A healthy maintenance cycle ends with:

- immutable Findings preserved;
- disagreements represented explicitly;
- stable knowledge linked to its evidence;
- Principles changed only through human agreement;
- generated navigation refreshed;
- project-prescribed checks passing.

## When to garden

Run gardening after a meaningful batch of Findings, after an investigation
campaign, before handing the KB to another team, or when links and stable
knowledge appear stale. Do not run it automatically during unrelated work: the
workflow is autonomous after invocation, but invocation itself is explicit.
