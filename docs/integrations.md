# Integrations

The service speaks two protocols on the same port.

## REST
`POST /query` with `{"question": "...", "top_k": 5}` returns `context` and `sources`. `GET /health` needs no token.

## MCP
Streamable HTTP at `/mcp`, one tool: `search_iobroker_docs(question, top_k)`. Example for a client configuration:

```json
{"mcpServers": {"iobroker-docs": {"type": "http", "url": "http://<host>:8321/mcp"}}}
```

## ioBroker editors (`@iobroker/ai-gui`)
`integrations/ai-gui/searchIoBrokerDocs.ts` is a tool for `createToolSet`. It is untested inside an editor so far.

```ts
createToolSet(ioBrokerReadTools(socket), searchIoBrokerDocsTool('http://<host>:8321'));
```

It runs in the browser: set `IOB_RAG_CORS` to the origin of the editor. A page served over HTTPS cannot call an HTTP service, so that setup needs a reverse proxy with TLS.

## Configuration
| Variable | Purpose |
|---|---|
| `IOB_RAG_TOKEN` | if set, every request except `/health` needs `Authorization: Bearer <token>` |
| `IOB_RAG_CORS` | comma separated origins allowed from a browser |
| `IOB_RAG_RERANK_POOL` | candidates for the reranker, fewer is faster |
| `IOB_RAG_INDEX` | index directory |
| `IOB_RAG_OLLAMA` | build embeddings through Ollama, e.g. on a GPU machine |
