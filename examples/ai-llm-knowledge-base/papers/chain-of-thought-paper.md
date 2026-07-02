---
type: paper
title: "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models"
description: >
  Demonstrates that prompting LLMs with step-by-step reasoning examples
  significantly improves performance on arithmetic and symbolic tasks.
authors: [Jason Wei, Xuezhi Wang, Dale Schuurmans, Maarten Bosma, Brian Ichter,
    Fei Xia, Ed Chi, Quoc Le, Denny Zhou]
year: 2022
venue: NeurIPS
url: https://arxiv.org/abs/2201.11903
tags: [chain-of-thought, reasoning, prompting]
bibtex_key: wei-2022-cot
timestamp: "2026-06-29"
links: [concepts/react-pattern.md]
backlinks: []
---

# Chain-of-Thought Prompting Elicits Reasoning in Large Language Models

The authors show that simply adding "Let's think step by step" to prompts
can unlock emergent reasoning capabilities in sufficiently large models.

Chain-of-thought reasoning is a core component of agent frameworks like
[ReAct](../concepts/react-pattern.md).
