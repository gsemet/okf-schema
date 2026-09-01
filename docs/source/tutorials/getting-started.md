# Create and Validate Your First OKF Bundle

In this tutorial, you will create an OKF bundle, add one document, and validate
it. An **OKF bundle** is a directory of Markdown documents whose YAML
frontmatter follows a schema.

**Time:** about 5 minutes

**Prerequisite:** Follow the [installation guide](../installation.md) to install
`okf-schema`. To work with a coding agent, also manually add the `okf-schema`
skill to your project.

## Create a bundle

Run:

```bash
okf-schema init my-knowledge-base
```

The command creates the bundle and its starter schema:

```text
my-knowledge-base/
└── bundle/
    ├── index.md
    ├── log.md
    └── _schema/
        └── _base.schema.yaml
```

`index.md` lists the bundle contents. `log.md` records important changes.
Files in `_schema/` define which frontmatter fields are valid.

## Add one document

Each knowledge item is one Markdown file. Create a document about an API
endpoint:

```bash
okf-schema new --path my-knowledge-base/bundle \
    --name api/health-check \
    --type "API Endpoint" \
    --title "Health Check"
```

The new file contains:

```markdown
---
type: API Endpoint
title: Health Check
description: ""
tags: []
---
```

Open `my-knowledge-base/bundle/api/health-check.md` and add a short body below
the frontmatter:

```markdown
# Health Check

`GET /health` reports whether the service is ready to receive requests.
```

Keep each document focused on one subject. It can grow later as you learn more.

You can ask a coding agent to author the content instead:

> Use the `okf-schema` skill to complete `api/health-check.md`. Describe only
> the `GET /health` endpoint, keep the document concise, and validate the bundle
> when finished.

The skill helps the agent preserve valid frontmatter and use the bundle's local
schema instead of inventing a format.

## Inspect the bundle

List the documents:

```bash
okf-schema list --path my-knowledge-base/bundle
```

Inspect the document and its frontmatter:

```bash
okf-schema show --path my-knowledge-base/bundle api/health-check
```

Refresh the generated indexes:

```bash
okf-schema index --path my-knowledge-base/bundle
```

## Validate your work

Run the validator before committing bundle changes:

```bash
okf-schema validate --path my-knowledge-base/bundle
```

Then normalize the frontmatter and generated link metadata:

```bash
okf-schema lint --path my-knowledge-base/bundle
```

Use strict validation when warnings should also fail the command:

```bash
okf-schema validate --path my-knowledge-base/bundle --strict
```

You now have a bundle containing one indexed, validated knowledge document.

## If validation fails

Read the first diagnostic and open the named file. Common causes are:

- missing `---` delimiters around YAML frontmatter;
- a missing required field such as `type` or `title`;
- invalid YAML indentation; or
- a field whose value does not match its schema.

Fix that diagnostic and run `validate` again. Later diagnostics may be effects
of the first malformed field.

## Next steps

- [Link Two Documents and Explore Backlinks](knowledge-graph.md) adds the first
  relationship to your bundle.
- [CLI Reference](../reference/cli.md) lists every command and option.
- [Write a Custom Schema](../how-to/write-custom-schema.md) explains how to
  validate project-specific document types.
- [Design Principles](../explanation/design-principles.md) explains why OKF
  favors small, connected documents.
