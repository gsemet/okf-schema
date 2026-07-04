# Building a Knowledge Graph

This tutorial walks through a **fictional** OKF bundle for a data-platform
team. You will see how cross-links between concepts create a navigable
knowledge graph, how `okf-schema lint` materialises those links into
frontmatter metadata, and how to query the graph from both the CLI and the
Python API.

---

## The scenario

Imagine you are the data-platform team at *Acme Corp*. Your knowledge base
covers tables, datasets, ingestion jobs, metrics, and runbooks. Concepts are
small — one per table, one per job, one per metric — and they are densely
linked.

Here is the bundle layout:

```
acme-knowledge/
├── index.md
├── log.md
├── tables/
│   ├── index.md
│   ├── orders.md
│   ├── customers.md
│   └── products.md
├── datasets/
│   ├── index.md
│   └── sales-dwh.md
├── jobs/
│   ├── index.md
│   ├── ingest-orders.md
│   └── ingest-customers.md
├── metrics/
│   ├── index.md
│   ├── daily-revenue.md
│   └── customer-lifetime-value.md
└── runbooks/
    ├── index.md
    └── freshness-alert.md
```

---

## Concept bodies: where links live

Links are ordinary markdown links in the body. The surrounding prose gives
meaning to the relationship.
Links and backlinks will later appear in the `links` and `backlinks` frontmatter
fields after running `okf-schema lint`.

Let's see how these excerpts from three newly created concepts:

### `tables/orders.md`

```markdown
---
type: BigQuery Table
title: Customer Orders
description: One row per completed order across all channels.
tags:
  - sales
  - core
---

# Schema

| Column        | Type   | Description                              |
|---------------|--------|------------------------------------------|
| `order_id`    | STRING | Globally unique order identifier.        |
| `customer_id` | STRING | Foreign key into [customers](customers.md). |
| `product_id`  | STRING | Foreign key into [products](products.md). |

# Joins

Joined with [customers](customers.md) on `customer_id`.
Joined with [products](products.md) on `product_id`.

# Downstream

Part of the [sales-dwh](datasets/sales-dwh.md) dataset.
```

### `metrics/daily-revenue.md`

````markdown
---
type: Metric
title: Daily Revenue
description: Sum of order totals per calendar day.
tags: [sales, kpi]
---

# Definition

```sql
SELECT DATE(placed_at) AS day, SUM(total_usd) AS revenue
FROM `orders`
GROUP BY 1
```
````

---

## Running `lint` to materialise the graph

After authoring the concepts, run:

```bash
okf-schema lint --path acme-knowledge/bundle
```

`okf-schema` scans every body, extracts internal links, resolves them to
bundle-relative paths, flattens lists and updates the frontmatter fields.

### Result: `tables/orders.md`

```markdown
---
type: BigQuery Table
title: Customer Orders
description: One row per completed order across all channels.
tags: [sales, core]
links: [datasets/sales-dwh.md, tables/customers.md, tables/products.md]
backlinks:
  [datasets/sales-dwh.md, jobs/ingest-orders.md, metrics/customer-lifetime-value.md,
   metrics/daily-revenue.md, tables/customers.md, tables/products.md]
---

# Schema

| Column        | Type   | Description                              |
|---------------|--------|------------------------------------------|
| `order_id`    | STRING | Globally unique order identifier.        |
| `customer_id` | STRING | Foreign key into [customers](customers.md). |
| `product_id`  | STRING | Foreign key into [products](products.md). |

# Joins

Joined with [customers](customers.md) on `customer_id`.
Joined with [products](products.md) on `product_id`.

# Downstream

Part of the [sales-dwh](datasets/sales-dwh.md) dataset.
```

Notice:

* **`links`** — The three concepts `orders.md` links *to*:
  `customers.md`, `products.md`, and `sales-dwh.md`.
* **`backlinks`** — The six concepts that link *here*:
  `sales-dwh.md`, `ingest-orders.md`, `customer-lifetime-value.md`,
  `daily-revenue.md`, `customers.md`, and `products.md`.

Both lists are sorted alphabetically so diffs stay minimal when a single
link is added or removed.

## See also

- [Getting Started](getting-started) — foundational tutorial on creating and navigating bundles.
- [Lint Before Commit](../how-to/lint-before-commit) — automating frontmatter consistency.
- [Design Principles](../explanation/design-principles) — why OKF-Schema treats knowledge as a graph.
- [Why an Opinionated Knowledge Base?](../explanation/opinionated-knowledge-base) — how links and backlinks work in the KB model.
- [CLI Reference](../reference/cli.md) — `lint`, `index`, `backlinks`, and `graph` commands.

---

## Navigating the graph from the CLI

### Show all outgoing links

```bash
okf-schema show --path acme-knowledge/bundle tables/orders
```

The rendered output includes the `links` frontmatter field, giving you an
instant neighbourhood map.

### Discover backlinks

```bash
okf-schema backlinks --path acme-knowledge/bundle tables/orders
```

Output:

```
tables/orders.md ← datasets/sales-dwh.md
tables/orders.md ← jobs/ingest-orders.md
tables/orders.md ← metrics/customer-lifetime-value.md
tables/orders.md ← metrics/daily-revenue.md
tables/orders.md ← tables/customers.md
tables/orders.md ← tables/products.md
```

This answers the question *"If I change the orders table schema, what else
needs review?"* in one command.

### Build the full adjacency list (Python API)

The full link graph is available through the Python API (see
[API Reference](../reference/api.md)):

```python
from okf_schema import graph_bundle
import json

graph = graph_bundle("acme-knowledge/bundle")
print(json.dumps(graph, indent=2))
```

Output (excerpt):

```json
{
  "tables/orders.md": [
    "datasets/sales-dwh.md",
    "tables/customers.md",
    "tables/products.md"
  ],
  "tables/customers.md": [
    "metrics/customer-lifetime-value.md",
    "tables/orders.md"
  ],
  "metrics/daily-revenue.md": [
    "datasets/sales-dwh.md",
    "tables/orders.md"
  ]
}
```

---

## Querying the graph from Python

The same operations are available programmatically.

### Full graph

```python
from okf_schema import graph_bundle

graph = graph_bundle("acme-knowledge/bundle")

for concept, neighbours in graph.items():
    print(f"{concept} → {neighbours}")
```

### Backlinks for a single concept

```python
from okf_schema import backlinks_bundle

results = backlinks_bundle("acme-knowledge/bundle", ["tables/orders.md"])
for r in results:
    print(f"{r.target} ← {r.source}  (context: {r.context!r})")
```

### Custom graph analysis

Because `graph_bundle` returns a plain dictionary, you can run any graph
algorithm on it:

```python
from okf_schema import graph_bundle

graph = graph_bundle("acme-knowledge/bundle")

# Find concepts with no outgoing links (leaf nodes)
leaves = [c for c, n in graph.items() if not n]
print("Leaf concepts:", leaves)

# Find the most referenced concept (highest in-degree)
in_degree: dict[str, int] = {}
for neighbours in graph.values():
    for n in neighbours:
        in_degree[n] = in_degree.get(n, 0) + 1

hub = max(in_degree, key=in_degree.get)
print(f"Most referenced: {hub} ({in_degree[hub]} backlinks)")
```

---

## Graph statistics at a glance

Running `okf-schema stats` on the bundle produces a summary that includes
link density:

```bash
okf-schema stats --path acme-knowledge/bundle
```

Typical output:

```
Concepts:        10
Directories:      5
Links:           18
Backlinks:       18
Avg links/concept: 1.8
```

A healthy knowledge graph has an average link count well above 1.0. If the
average is close to zero, the bundle is a collection of isolated documents
rather than a connected graph.

---

## Design tips for a navigable graph

1. **Link early, link often**
   Every time you mention another concept by name, turn it into a markdown
   link. The lint step will do the bookkeeping.

2. **Use relative paths for portability**
   Write `../tables/orders.md` or `./customers.md` rather than
   `/tables/orders.md`. Relative paths survive when a subdirectory is copied
   or symlinked into another bundle.

3. **Let `lint` run in CI**
   Add `okf-schema lint --path acme-knowledge/bundle --check` to your CI
   pipeline. It fails if `links` or `backlinks` are out of sync with the
   body, catching stale metadata before it reaches the main branch.

4. **Prefer small concepts over monolithic pages**
   A 500-line page with ten embedded links is less useful than ten 50-line
   pages with two links each. Small concepts keep the graph granular and
   navigable.

5. **Review backlinks before refactoring**
   Before renaming or deleting a concept, run `okf-schema backlinks` to see
   every file that depends on it. Update or redirect those links first.
