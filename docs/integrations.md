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
`integrations/ai-gui/searchIoBrokerDocs.ts` is a tool for `createToolSet` of `@iobroker/ai-gui` 0.0.5.

```ts
createToolSet(ioBrokerReadTools(socket), searchIoBrokerDocsTool('http://<host>:8321', '<token>'));
```

It runs in the browser: set `IOB_RAG_CORS` to the origin of the editor. A page served over HTTPS cannot call an HTTP service, so that setup needs a reverse proxy with TLS. The second argument is optional and is sent as `Authorization: Bearer` for a service with `IOB_RAG_TOKEN`. Every user of the editor can read that token, so it keeps other clients on the network away, not the editor's users.

Tested so far (2026-11-03): the file compiles against the published types, `createToolSet(...).run('search_iobroker_docs', ...)` returns the rendered context with and without token, and a page in WebKit reaches the service when its origin is in `IOB_RAG_CORS` and is blocked by the preflight when it is not. Not yet tested inside a real editor build of `admin`, `javascript` or `vis-2`.

## Configuration
| Variable | Purpose |
|---|---|
| `IOB_RAG_TOKEN` | if set, every request except `/health` needs `Authorization: Bearer <token>` |
| `IOB_RAG_CORS` | comma separated origins allowed from a browser |
| `IOB_RAG_RERANK_POOL` | candidates for the reranker, fewer is faster |
| `IOB_RAG_CORE_BOOST` | penalty for code and unrelated adapter READMEs, default 2, 0 turns it off |
| `IOB_RAG_INDEX` | index directory |
| `IOB_RAG_OLLAMA` | build embeddings through Ollama, e.g. on a GPU machine |
