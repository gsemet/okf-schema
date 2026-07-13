# Navigation and maintenance

Navigate top-down and maintain the graph after knowledge changes.

## Reading path

1. Read `AGENTS.md` and linked KB rules.
2. Read `log.md` for recent semantic changes when it is maintained by the
   project.
3. Read `index.md` and stable tiers: Principles, Concepts, and Structures.
4. Use narrow search/query operations to locate relevant nodes.
5. Fetch individual Findings only when evidence, context, or historical
   evolution is needed.
6. Stop when the current task has enough trustworthy context.

Do not dump whole Findings folders into context. The stratification exists to
avoid paying evidence-level reading cost for every question.

## Navigation tools

When available:

- `read` loads a stable tier for broad understanding;
- `search` locates likely nodes by text and metadata;
- `query` filters by fields or traverses relationships;
- `get` fetches one exact node.

Use the `okf-schema` skill or project command reference for exact CLI syntax.
Prefer the project's installed CLI and conventions over copied commands.

## Graph maintenance

After KB mutations:

- ensure relationship paths resolve;
- maintain reciprocal contradiction/supersession metadata where supported;
- refresh generated links, backlinks, and indexes with project-prescribed tools;
- keep frontmatter compact and schema-valid;
- preserve unknown extension fields and YAML comments;
- add `log.md` entries only for significant semantic events: promotion,
  contradiction, supersession, deprecation, or material revision.

Routine formatting, indexing, and no-op gardening runs do not deserve semantic
log entries.

## Validation discovery

Never assume every KB uses the same `just`, `make`, or shell targets. Read the
nearest `AGENTS.md`, project guidelines, task runner, and scripts to discover the
required maintenance sequence. The expected outcome is the project's own clean
validation bar, commonly zero errors and warnings.

If checks fail after a mutation, repair the cause and rerun the relevant checks.
Report unresolved failures and preserve the resulting diff unless local project
rules require rollback.

## Recurring maintenance

Use `okfkb-gardening` only when explicitly invoked. It performs zero-prompt
autonomous review and may update all KB layers except Principles. It reports the
full result in chat and writes only significant semantic events to `log.md`.