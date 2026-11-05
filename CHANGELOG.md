# Changelog

## 0.4.0
- Adapter documentation from the ioBroker Latest repository: `tools/sync_adapters.py` generates `sources.adapters.json` (README, `docs/`, CHANGELOG of every adapter with an allowed license). English `adapterref` copies in ioBroker.docs are skipped for indexed adapters, translations stay.
- License policy in `sources.json` (`allow` / `review` / `deny`), applied by the generator and by `tools/check_sources.py`; documented in `CONTRIBUTING.md`. This installation indexes `review` sources too (`index_review: true`), copyleft documentation is read locally only.
- Incremental rebuild: repositories whose remote tip equals the indexed commit are not fetched, chunks with unchanged text take their vector from the live index. `--full` or `FULL=1` for a complete rebuild.
- `/query` names the adapter for results from adapter repositories; general questions are not drowned by adapter READMEs (same penalty as for `adapterref`).

## 0.3.0
- Requires Python 3.12 or 3.13 (numpy 2.5 dropped 3.11).
- The `@iobroker/ai-gui` tool accepts an optional token for a service with `IOB_RAG_TOKEN`.
- The rebuild script reads `IOB_RAG_OLLAMA` from `/etc/default/iobroker-rag` instead of a built-in address.

## 0.2.0
- MCP endpoint, optional token, CORS, tool for `@iobroker/ai-gui`.
- Tested weekly rebuild with automatic switch.

## 0.1.0
- Hybrid search with BGE-M3, BM25 and reranker over an allowlist of public repositories.
