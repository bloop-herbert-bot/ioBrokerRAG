# Changelog

## 0.3.0
- Requires Python 3.12 or 3.13 (numpy 2.5 dropped 3.11).
- The `@iobroker/ai-gui` tool accepts an optional token for a service with `IOB_RAG_TOKEN`.
- The rebuild script reads `IOB_RAG_OLLAMA` from `/etc/default/iobroker-rag` instead of a built-in address.

## 0.2.0
- MCP endpoint, optional token, CORS, tool for `@iobroker/ai-gui`.
- Tested weekly rebuild with automatic switch.

## 0.1.0
- Hybrid search with BGE-M3, BM25 and reranker over an allowlist of public repositories.
