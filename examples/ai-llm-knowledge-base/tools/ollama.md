---
type: tool
title: Ollama
vendor: Ollama Inc.
description: >
  A lightweight tool for running open-source LLMs locally with a simple
  command-line interface.
license: MIT
language: Go
maturity: beta
url: https://ollama.com
tags: [local-llm, inference, cli]
timestamp: "2026-06-29"
links: [concepts/function-calling.md, concepts/rag.md]
backlinks: []
---

# Ollama

Ollama bundles model weights, configuration, and data into a single package
managed through a Docker-like CLI for local experimentation.

Running models locally is useful for prototyping [RAG](../concepts/rag.md)
pipelines and testing [function-calling](../concepts/function-calling.md)
capabilities without API costs.
