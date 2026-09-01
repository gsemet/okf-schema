# Link Two Documents and Explore Backlinks

In this tutorial, you will connect two documents and let `okf-schema` generate
the reverse relationship. This creates the smallest useful knowledge graph.

**Time:** about 10 minutes

**Prerequisite:** Complete
[Create and Validate Your First OKF Bundle](getting-started.md). The commands
below use the bundle created there.

## Create a second document

The existing `api/health-check.md` document describes an endpoint. Add a
runbook that explains what to do when that endpoint reports a problem:

```bash
okf-schema new --path my-knowledge-base/bundle \
    --name runbooks/service-unavailable \
    --type Runbook \
    --title "Service Unavailable"
```

Open `my-knowledge-base/bundle/runbooks/service-unavailable.md` and add:

```markdown
# Service Unavailable

Check the [health endpoint](../api/health-check.md) before restarting the
service.
```

The ordinary Markdown link is the authored relationship. Its surrounding
sentence explains why the documents are related.

Instead of editing manually, tell your coding agent:

> Use the `okf-schema` skill to create a `Service Unavailable` runbook in the
> current bundle. Link it to `api/health-check.md`, explain why the operator
> follows that link, then lint and validate the bundle.

The prompt states the relationship's meaning; the skill handles valid paths,
frontmatter, and generated link metadata.

## Generate graph metadata

Run the linter:

```bash
okf-schema lint --path my-knowledge-base/bundle
```

The linter resolves internal links and updates two generated frontmatter
fields:

- `links` lists documents referenced by the current document.
- `backlinks` lists documents that reference the current document.

The runbook now has an outgoing link similar to:

```yaml
links: [api/health-check.md]
backlinks: []
```

The health-check document receives the reverse edge:

```yaml
links: []
backlinks: [runbooks/service-unavailable.md]
```

Do not edit these generated lists by hand. Edit Markdown links in document
bodies and run `lint` again.

## Follow the relationship

Ask which documents depend on the health-check document:

```bash
okf-schema backlinks --path my-knowledge-base/bundle api/health-check
```

This is useful before renaming, deleting, or substantially changing a document.
It shows which other knowledge may need review.

Inspect the runbook to see its outgoing links:

```bash
okf-schema show --path my-knowledge-base/bundle runbooks/service-unavailable
```

## Check the result

Refresh indexes and validate the bundle:

```bash
okf-schema index --path my-knowledge-base/bundle
okf-schema validate --path my-knowledge-base/bundle --strict
```

You now have a two-document graph with an authored link and a generated
backlink.

## If a link is unresolved

Check the path from the file containing the link. The runbook is one directory
below the bundle root, so it uses `../api/health-check.md`, not
`api/health-check.md`. Keep the `.md` suffix in Markdown body links.

Run `lint` after correcting the path, then validate again.

## Next steps

- [Lint Before Commit](../how-to/lint-before-commit.md) keeps graph metadata in
  sync automatically.
- [Python API Reference](../reference/api.md) covers custom graph analysis.
- [Design Principles](../explanation/design-principles.md) explains the graph
  model and guidance for document size and linking.
- [Record Your First Finding](okfkb-first-finding.md) introduces the optional
  opinionated OKF-KB workflow.
