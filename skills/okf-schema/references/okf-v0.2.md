# Open Knowledge Format (OKF) — Version 0.2

**Version 0.2 — Stable**

OKF 0.2 is a backward-compatible minor bump of OKF 0.1. Existing 0.1 bundles remain
conformant; 0.2 makes provenance, trust, lifecycle, and attestation first-class fields
and renames two legacy constructs.

For the full authoritative specification, see the upstream
[OKF SPEC](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md).

---

## Key Changes from 0.1

### Renamed fields

| OKF 0.1          | OKF 0.2              | Notes                              |
|------------------|----------------------|------------------------------------|
| `timestamp`      | `generated.at`       | `generated.by` also recommended    |
| body `# Citations` | `sources` frontmatter + footnotes | Structural migration   |

### New first-class frontmatter families

#### `generated` — provenance timestamp and producer

```yaml
generated:
  at: "2026-08-10T14:00:00Z"   # ISO 8601 datetime; required when block present
  by: "human:alice"             # actor string; optional but recommended
```

#### `sources` — provenance list

```yaml
sources:
  - resource: "https://example.com/paper.pdf"  # required
    id: paper-1                                  # optional; used in footnotes [^paper-1]
    title: "Example Paper"
    author: "Alice"
usage_window: "2025-01-01/2026-01-01"           # optional ISO 8601 interval
```

Footnotes in the body reference source IDs:

```markdown
This claim is supported.[^paper-1]

[^paper-1]: See sources frontmatter entry `id: paper-1`.
```

#### `verified` — trust attestation list

```yaml
verified:
  - by: "human:alice"          # actor string; required; human: prefix drives trust tier
    at: "2026-08-10"           # ISO 8601 date; required
    method: "peer-review"      # optional
```

A bare mapping is automatically normalized to a one-element list.

#### `status` — lifecycle state

```yaml
status: draft    # draft | stable | deprecated  (default: stable)
stale_after: "2027-01-01"   # ISO 8601 date; triggers W11 when today ≥ this date
```

---

## Trust Tiers (derived from `verified`)

| Tier               | Condition                                           |
|--------------------|-----------------------------------------------------|
| `unverified`       | No well-formed `verified` entries                   |
| `machine-confirmed`| All well-formed `by` entries use non-`human:` prefix |
| `human-reviewed`   | At least one well-formed `by` entry uses `human:` prefix |

Malformed actor strings never promote the tier (W10 warning emitted instead).

---

## Attested Computation (deferred)

The `runtime`, `parameters`, `computation`, `executor`, `receipt`, `attester`,
and `# Computation` body section are part of OKF 0.2 §10 and are explicitly
deferred from `okf-schema` 0.2 support.

---

## Validation Codes (0.2 additions)

| Code | Severity | Description |
|------|----------|-------------|
| E8   | Error    | `generated` block present but `at` field missing |
| E9   | Error    | `sources` entry missing required `resource` field |
| E10  | Error    | `verified` entry missing required `by` or `at` field |
| W8   | Warning  | Deprecated `timestamp` field; use `generated.at` instead |
| W9   | Warning  | Deprecated body `# Citations` section; use `sources` frontmatter |
| W10  | Warning  | Malformed actor string in `verified[].by` |
| W11  | Warning  | File is stale (`stale_after` date has passed) |
| W12  | Warning  | Footnote reference `[^id]` with no matching `sources[].id` |
| W13  | Warning  | Broken path in path-form `resource` or `sources[].resource` |
