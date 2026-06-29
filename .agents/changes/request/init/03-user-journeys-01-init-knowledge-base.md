# User Journey: Initialize a new knowledge base

## Situation

Alex is a developer who wants to start documenting their team's infrastructure knowledge using the OKF format. They have heard about `okf-schema` and want to create a new knowledge base from scratch.

## Current pain

Without a standardized tool, Alex would need to manually create the directory structure, remember the required files (`index.md`, `log.md`), and ensure the frontmatter format is correct. This is error-prone and time-consuming.

## What changes

Alex runs `okf-schema init my-kb` and immediately gets a properly structured OKF bundle with `my-kb/bundle/` (containing `index.md` and `log.md`) and `my-kb/schema/` directories. They can start adding concept files right away without worrying about structure.

## Acceptance test ideas

- Running `okf-schema init kb` creates `kb/bundle/index.md`, `kb/bundle/log.md`, and `kb/schema/`.
- Running `okf-schema init kb` when `kb/` already exists exits with code 1 and an informative message.
- The generated `index.md` has the correct minimal structure for a bundle root.
- The generated `log.md` has no frontmatter and is ready for date-stamped entries.
