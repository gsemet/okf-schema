---
type: concept
title: Function Calling
description: >
  A capability that allows LLMs to output structured tool calls instead of
  free-form text, enabling reliable integration with external APIs.
category: LLM
maturity: production
author_email: dave@example.com
complexity: beginner
tags: [function-calling, api, structured-output]
related_tools: [OpenAI-API, Anthropic-API]
timestamp: "2026-06-29"
links: [concepts/react-pattern.md, papers/toolformer.md]
backlinks: [concepts/react-pattern.md, papers/attention-is-all-you-need.md,
    papers/toolformer.md, tools/ollama.md]
---

# Function Calling

Function calling lets developers define schemas for external tools and have
the model decide when and how to invoke them based on user input.

This capability is a building block for agent patterns such as
[ReAct](../concepts/react-pattern.md) and is explored in the
[Toolformer](../papers/toolformer.md) research.
