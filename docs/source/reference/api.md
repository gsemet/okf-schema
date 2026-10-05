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
