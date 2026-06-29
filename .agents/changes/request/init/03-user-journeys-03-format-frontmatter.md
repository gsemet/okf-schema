# User Journey: Format frontmatter consistently

## Situation

Alex's team has been editing OKF concept files with different editors, resulting in inconsistent frontmatter formatting. Some files have nested lists that should be flat, and comments are scattered inconsistently.

## Current pain

Manually fixing frontmatter across dozens of files is repetitive and error-prone. Standard YAML formatters don't preserve comments, which are important for OKF concept documentation.

## What changes

Alex runs `okf-schema format ./my-kb/bundle` and all concept files are updated in-place. Nested lists in frontmatter are flattened, formatting is normalized, and all existing comments are preserved thanks to `ruamel.yaml`. Alex can also use `--check` in CI to ensure formatting compliance without modifying files.

## Acceptance test ideas

- Running `format` on a bundle with nested lists flattens them while preserving comments.
- Running `format --check` on a conformant bundle exits 0.
- Running `format --check` on a non-conformant bundle exits 1.
- Running `format --diff` shows the diff without modifying files.
- Frontmatter comments are preserved after formatting.
