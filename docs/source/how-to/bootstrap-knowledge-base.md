# Bootstrap an Opinionated Knowledge Base

`okfkb` scaffolds and manages a specific kind of OKF bundle: an **opinionated
knowledge base** designed for agent-driven findings traceability. This guide
walks through creating, populating, and integrating one into a project.

## Prerequisites

Install `okf-schema`:

```bash
pip install okf-schema
```

Verify the `okfkb` entry point is available:

```bash
okfkb --help
```

---

## Step 1 — Scaffold the KB

```bash
okfkb init my-project/knowledge/
```

This creates the canonical layout inside `my-project/knowledge/`:

```
knowledge/
├── _schema/          # 8 bundled JSONSchema files
├── concepts/
├── experiments/
├── findings/         # ← where new-finding writes files
├── guides/
├── ideas/
├── principles/
├── reference/
├── structures/
├── index.md          # table of contents
└── log.md            # chronological changelog
```

If the directory already exists and is non-empty, use `--force`:

```bash
okfkb init my-project/knowledge/ --force
```

---

## Step 2 — Record your first Finding

A **Finding** is an immutable, dated observation. Use `new-finding` to generate
a schema-valid file:

```bash
okfkb new-finding my-project/knowledge/ \
  --title "Redis eviction rate spikes under load" \
  --confidence medium \
  --context "Observed on 2026-07-04 during load test at 800 RPS; eviction_ratio hit 0.94."
```

This writes `findings/2026.07.04-14.30-redis-eviction-rate-spikes-under-load.md`
with all required OKF frontmatter pre-filled.

Open the file and complete the Observation, Evidence, and Implications sections.

```bash
# Optional: add tags for better searchability
okfkb new-finding my-project/knowledge/ \
  --title "TLS handshake timeout" \
  --confidence high \
  --context "mTLS timeout under IPv6 on GKE cluster." \
  --tags "tls,network,timeout"
```

---

## Step 3 — Refresh index and validate

After adding files, update the cross-link index and check conformance:

```bash
okf-schema index   --path my-project/knowledge/
okf-schema lint    --path my-project/knowledge/
okf-schema validate --strict --path my-project/knowledge/
```

- **`index`** scans all markdown files, computes backlinks, and updates `index.md`.
- **`lint`** normalises YAML frontmatter without changing values.
- **`validate --strict`** checks all files against the bundled schemas.

---

## Step 4 — Install KB tooling into your project

`install-skills` deploys the bundled `record-finding` and
`consolidate-knowledge-base` agent skills, plus the `knowledge-base.guidelines.md`
guideline, into the project's `.agents/` directory:

```bash
okfkb install-skills my-project/
```

It also creates or patches `my-project/AGENTS.md` with a reference to the
installed guideline, so coding agents pick it up automatically.

---

## Step 5 — Add to CI (recommended)

Add a validation step so schema drift is caught before merge:

```yaml
# .github/workflows/validate.yml
- name: Validate knowledge base
  run: |
    pip install okf-schema
    okf-schema validate --strict --path knowledge/
```

---

## Typical workflow

```
day 1   okfkb init knowledge/
day 2+  okfkb new-finding knowledge/ --title "..." --confidence medium --context "..."
        # edit the generated file to fill in Observation / Evidence / Implications
        okf-schema index --path knowledge/
        okf-schema validate --strict --path knowledge/
        git add knowledge/ && git commit -m "docs: record finding ..."
```

---

## Next steps

- [KB Commands reference](../reference/kb-commands) — full option reference for every command.
- [Why an opinionated KB?](../explanation/opinionated-knowledge-base) — design rationale and
  how agents traverse the graph.
- [Validate in CI](validate-in-ci) — automate schema checks in your pipeline.
