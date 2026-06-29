# User Journey: Validate bundle quality

## Situation

Alex has been adding concept files to their OKF bundle for a few weeks. They want to ensure all files conform to the OKF specification and catch any issues before sharing the bundle with their team.

## Current pain

Manually checking every markdown file for correct frontmatter, valid types, broken links, and proper structure is tedious and easy to miss things. There's no automated way to verify conformance.

## What changes

Alex runs `okf-schema validate ./my-kb/bundle` and receives a comprehensive report listing all errors (e.g., missing frontmatter, unflatten lists) and warnings (e.g., broken links, missing recommended fields). They can fix issues systematically and re-run validation until the bundle is conformant.

## Acceptance test ideas

- A bundle with valid concepts passes validation with exit code 0.
- A bundle with missing frontmatter reports E1 errors.
- A bundle with unflatten lists in frontmatter reports E5 errors.
- A bundle with broken cross-links reports W2 warnings.
- Validation with `--schema-db` checks concepts against provided schemas and reports E4/W6.
- Exit code is 1 when errors exist, 0 when only warnings exist.
