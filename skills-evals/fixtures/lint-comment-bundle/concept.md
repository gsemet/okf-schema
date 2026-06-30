---
# Core metadata for this concept
type: concept
# Title should be concise and descriptive
title: Comment Preservation Test
# Description explains the purpose of this concept
description: >
  A concept designed to test whether the okf-schema linter
  preserves YAML comments while converting block-style lists
  to inline notation.
# Tags categorize this concept for discovery
tags: [linting, comments, yaml]
# Timestamp records when this concept was created
timestamp: 2026-06-30T12:00:00Z
---

# Comment Preservation Test

This concept file contains YAML comments in its frontmatter.
When `okf-schema lint` runs, it should:

1. Convert the block-style `tags` list to inline notation (`tags: [linting, comments, yaml]`)
2. Preserve all `#` comments in the frontmatter
3. Keep the `description` field intact

If comments are lost, the linter is not using ruamel.yaml round-trip mode correctly.
