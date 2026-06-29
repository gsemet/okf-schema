---
type: concept
title: ReAct Pattern
description: >
  A reasoning and acting paradigm where an LLM interleaves thought traces
  with tool calls to solve complex multi-step problems.
category: AI Agent
maturity: beta
author_email: carol@example.com
complexity: advanced
tags: [agents, reasoning, tool-use, react]
related_tools: [LangChain, AutoGPT]
timestamp: "2026-06-29"
---

# ReAct Pattern

ReAct (Reasoning + Acting) prompts the model to generate both reasoning
traces and actionable steps, enabling dynamic interaction with external tools.

See also [Function Calling](../concepts/function-calling.md) for the underlying
mechanism that enables tool use, and the [Toolformer](../papers/toolformer.md)
paper for a self-supervised approach to learning tool use.
