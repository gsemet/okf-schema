---
type: concept
title: Retrieval-Augmented Generation
description: >
  A technique that enhances LLM outputs by retrieving relevant documents
  from an external knowledge store and injecting them into the prompt.
category: LLM
maturity: production
author_email: bob@example.com
complexity: intermediate
tags: [rag, retrieval, llm, knowledge-base]
related_tools: [LangChain, LlamaIndex, OpenAI-API]
timestamp: "2026-06-29"
---

# Retrieval-Augmented Generation

RAG combines parametric knowledge (the model's weights) with non-parametric
knowledge (external documents) to reduce hallucinations and improve factual accuracy.

Popular frameworks for building RAG pipelines include [LangChain](../tools/langchain.md)
and [LlamaIndex](https://www.llamaindex.ai).
