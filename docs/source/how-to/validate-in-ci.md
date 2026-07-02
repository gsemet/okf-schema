# Validate in CI

Ensure every commit to your knowledge base passes validation before merging.

## GitHub Actions

```yaml
name: Validate OKF Bundle

on:
  push:
    paths:
      - "knowledge-base/**"
  pull_request:
    paths:
      - "knowledge-base/**"

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv tool install okf-schema
      - run: okf-schema validate --path knowledge-base/bundle --strict
```

## GitLab CI

```yaml
validate-okf:
  image: python:3.12-slim
  script:
    - uv tool install okf-schema
    - okf-schema validate --path knowledge-base/bundle --strict
  rules:
    - changes:
        - knowledge-base/**
```

## Strict vs. lenient mode

| Flag | Behavior | Best for |
|------|----------|----------|
| *(none)* | Errors fail, warnings pass | Development branches |
| `--strict` | Warnings become errors | Main branch, releases |

Use `--strict` in CI for your default branch to guarantee a clean bundle.
