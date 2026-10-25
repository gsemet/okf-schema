# Python API Reference

The `okf_schema.api` module provides a clean, typed Python interface for all okf-schema operations.

## Schema-declared file links

File-link semantics belong to the base API, not to either opinionated layer.
Use `validate_bundle(..., check_links=True)` to check a generic OKF, OKFKB, or
OKFREQ bundle against its own annotated schemas. Checking is disabled by default
and never rewrites documents or installs annotations into existing schemas.

```python
from okf_schema.api import validate_bundle

report = validate_bundle("knowledge", check_links=True, project_root=".")
for finding in report.errors + report.warnings:
   print(finding.code, finding.path, finding.message)
```

A parser that already has frontmatter and a schema can call the same checker
directly. Annotate a scalar for one link or string `items` for a list of links:

```python
from pathlib import Path
from okf_schema.api import check_file_links

schema = {
   "properties": {
      "evidence": {
         "type": "array",
         "items": {
            "type": "string",
            "x-okf-link": {
               "resolution": "bundle-relative-stem",
               "syntax": "plain",
            },
         },
      }
   }
}
diagnostics = check_file_links(
   {"evidence": ["observations/cache-run"]},
   schema,
   Path("bundle/concepts/cache.md"),
   bundle_root=Path("bundle"),
)
```

This checks `bundle/observations/cache-run.md`. Missing targets produce `E10`;
an unavailable bundle root produces `W15` rather than silently approving the
link. The return values are `FileLinkDiagnostic` objects with `severity`,
`code`, `message`, and `field_path` (for example, `evidence[0]`).
See [Write a custom schema](../how-to/write-custom-schema.md) for all resolution
modes and plain/wikilink syntax, [KB setup](../how-to/setup-okfkb.md) for
Finding evidence, and [requirement frontmatter](okfreq-frontmatter.md) for
implementation and test evidence.

Use `inspect_file_links` when a consumer needs successful resolutions as well as
diagnostics. It returns one `FileLinkResult` per applicable annotated value,
including the resolved path, parsed query/fragment/label, and `valid`, `invalid`,
or `unavailable` status:

```python
from okf_schema.api import inspect_file_links

results = inspect_file_links(
   {"evidence": ["observations/cache-run"]},
   schema,
   Path("bundle/concepts/cache.md"),
   bundle_root=Path("bundle"),
)
for result in results:
   print(result.field_path, result.status, result.resolved_path)
```

`check_file_links` is the compatibility-oriented projection that returns only
the `E10` and `W15` diagnostics. Neither function scans headings, marker lines,
or test results; navigation metadata remains advisory for downstream consumers.

```{eval-rst}
.. autofunction:: okf_schema.api.inspect_file_links
```

```{eval-rst}
.. autoclass:: okf_schema.api.FileLinkResult
   :members:
```

```{eval-rst}
.. autoclass:: okf_schema.api.FileLinkDiagnostic
   :members:
```

## Schema loading diagnostics

`validate_bundle` and `validate_markdown_files` report schema files that yield no
schema: `Report.infos` receives `I1` for an empty file and `Report.warnings`
receives `W17` for an unparsable or non-mapping file (see
[validation codes](validation-codes.md)). Informational findings never make a
report non-conformant. Use the loader directly to get the same findings:

```python
from pathlib import Path
from okf_schema.validator import load_schema_database_with_diagnostics

schemas, diagnostics = load_schema_database_with_diagnostics(Path("bundle/_schema"))
for finding in diagnostics:
   print(finding.code, finding.path, finding.message)
```

`load_schema_database` keeps its signature and returns only the mapping, skipping
such files silently.

```{eval-rst}
.. autofunction:: okf_schema.validator.load_schema_database_with_diagnostics
```

## Bundle operations

```{eval-rst}
.. autofunction:: okf_schema.api.validate_bundle
```

```{eval-rst}
.. autofunction:: okf_schema.api.format_bundle
```

```{eval-rst}
.. autofunction:: okf_schema.api.lint_bundle
```

```{eval-rst}
.. autofunction:: okf_schema.api.list_bundle
```

```{eval-rst}
.. autofunction:: okf_schema.api.show_bundle
```

```{eval-rst}
.. autofunction:: okf_schema.api.index_bundle
```

```{eval-rst}
.. autofunction:: okf_schema.api.search_bundle
```

```{eval-rst}
.. autofunction:: okf_schema.api.stats_bundle
```

```{eval-rst}
.. autofunction:: okf_schema.api.graph_bundle
```

```{eval-rst}
.. autofunction:: okf_schema.api.backlinks_bundle
```

```{eval-rst}
.. autofunction:: okf_schema.api.validate_markdown_files
```

```{eval-rst}
.. autofunction:: okf_schema.api.rewrite_superseded_links
```

```{eval-rst}
.. autofunction:: okf_schema.api.update_bundle
```

## Result types

```{eval-rst}
.. autoclass:: okf_schema.api.UpdateResult
   :members:
```

```{eval-rst}
.. autoclass:: okf_schema.api.SupersededRewrite
   :members:
```

```{eval-rst}
.. autoclass:: okf_schema.api.DeferredRewrite
   :members:
```

### Result identities and inspection lifetime

`value_identity` is an escaped JSON Pointer: `/a.b` identifies a literal dotted
key, `/a/b` identifies a nested key, and `/attachments/0` identifies an array
item. `~` and `/` in keys escape as `~0` and `~1`; the document root is the empty
string. Use this identity for editor state and matching results; `field_path`
remains a human-readable label such as `attachments[0]` and is not a unique key.

A local `$ref` and its siblings both constrain union applicability. Only the
selected `then` or `else` branch contributes conditional annotations. A literal
null character in a target produces `E10` rather than interrupting inspection.

Filename-stem resolution indexes Markdown candidates once per bundle in an
inspection or validation campaign. The index is discarded after the call, so a
later call observes added files and newly ambiguous names. There is no global
cache and callers do not need to invalidate editor state.
