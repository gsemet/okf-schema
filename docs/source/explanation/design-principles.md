# Design Principles

OKF-Schema is built on a small set of principles that guide every design
decision.

## 1. Self-describing bundles

A knowledge base should explain its own structure. By requiring JSONSchema
files in `_schema/`, OKF-Schema makes bundles self-describing: any tool (or
agent) can read the schemas and understand what fields are expected, what
types they should have, and which are required.

This is the opposite of implicit conventions or out-of-band documentation.

## 2. Agent-first ergonomics

OKF is designed for agentic workflows. Every decision (from compact inline
frontmatter to machine-parseable CLI output) is optimized for tools that
read, write, and validate concepts programmatically.

* **Compact frontmatter** — Agents often load only the first 20–50 lines.
  Inline YAML lists keep critical metadata visible.
* **Structured CLI output** — Every command exits with a non-zero status on
  failure and produces predictable output.
* **Index files** — `index.md` files give agents a table of contents without
  requiring filesystem traversal.

## 3. Progressive disclosure

A large knowledge base is overwhelming if presented all at once. OKF-Schema
encourages progressive disclosure:

* `index.md` files in each directory provide a local table of contents
* `log.md` files provide a chronological history of changes
* Cross-links between concepts let readers navigate depth-first, exploring
  only what interests them

## 4. Validation as a gate

Validation is not an afterthought: it is a gate that prevents malformed data
from entering the system. By running `okf-schema validate --strict` in CI,
you guarantee that every concept on the main branch conforms to the schema.

This is especially important for agent-generated content: agents can produce
incorrect frontmatter, and validation catches these errors before they
propagate.

## 5. Human edits are sacred

Automation should assist, not overwrite. The `lint` command uses
`ruamel.yaml` in round-trip mode, which preserves:

* Comments
* Key order
* Quote styles
* Blank lines

This means you can run `lint` safely without worrying about losing
human-written context.

## 6. Graph over hierarchy

A knowledge base is a graph of interlinked concepts, not a folder hierarchy.
OKF-Schema encourages dense cross-linking through:

* `backlinks` — discover which concepts link to a given target
* `graph` — build the full link graph for analysis
* Relative links — `../tables/orders.md` works regardless of where the bundle
  is mounted

Folders are for namespacing, not for organizing meaning. The meaning lives in
the links.
