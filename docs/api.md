# REST API

API version 1. The machine-readable schema is served at `/openapi.json`, an interactive page at `/docs`.

## Stability

The fields and value meanings below are the contract for API version 1. `GET /health` reports `api_version`.

- **Compatible changes** keep the API version: new optional request fields, new response fields, new endpoints. Clients must ignore response fields they do not know.
- **Breaking changes** raise `api_version` and are announced in the [changelog](../CHANGELOG.md). Examples: removing or renaming a field, changing its type or meaning, a stricter request limit.
- **Request fields must be known.** An unknown request field is rejected with 422, so a misspelt field is not silently replaced by a default.

## Authentication

If the server sets `IOB_RAG_TOKEN`, every request except `GET /health` needs `Authorization: Bearer <token>`. Without a token or with a wrong token the server answers 401. Browser access needs `IOB_RAG_CORS`, see [integrations](integrations.md).

## `POST /query`

Searches the index and returns the best chunks.

Request:

```json
{"question": "Wie setze ich einen State mit ack=true?", "top_k": 3, "rerank": true, "include_prompt": false}
```

| Field | Type | Default | Meaning |
|---|---|---|---|
| `question` | string, 2–2000 characters | required | Question in natural language, German or English |
| `top_k` | integer, 1–20 | 5 | Number of results |
| `rerank` | boolean | true | Rerank the candidates with the cross-encoder. Better order, about 3 s instead of about 0.3 s on a CPU. |
| `include_prompt` | boolean | false | Also return a ready prompt with the context and the question |

Response:

```json
{
  "context": "[Source: ioBroker.docs/docs/en/adapterref/iobroker.javascript/javascript.md § ... > setState | doc | MIT | relevance: 0.74]\n### setState\n...",
  "sources": [
    {
      "file": "ioBroker.docs/docs/en/adapterref/iobroker.javascript/javascript.md",
      "repo": "ioBroker/ioBroker.docs",
      "type": "doc",
      "language": "en",
      "adapter": "iobroker.javascript",
      "section": "The following functions can be used in scripts: > setState",
      "relevance": 0.739,
      "score": 9.58,
      "license": "MIT",
      "license_status": "allow",
      "commit": "8cfdf355c84fb6145b5bd507c40f5ab57fa8b14b"
    }
  ],
  "query_time_ms": 3051.2,
  "total_results": 1
}
```

| Field | Type | Meaning |
|---|---|---|
| `context` | string | All results rendered as text for a prompt. Each result starts with a `[Source: file § section \| type \| license \| relevance: x]` header, results are separated by `---`. |
| `sources` | list | The results, best first. Fields below. |
| `query_time_ms` | number | Search time on the server |
| `total_results` | integer | Number of entries in `sources` |
| `prompt` | string | Only present with `include_prompt: true` |

Fields of each entry in `sources`:

| Field | Type | Meaning |
|---|---|---|
| `file` | string | Repository name and path, e.g. `ioBroker.docs/docs/en/admin.md` |
| `repo` | string | GitHub repository, `owner/name` |
| `type` | string | `doc` for documentation, `code` for source code |
| `language` | string | `de` or `en` |
| `adapter` | string | `iobroker.<name>` for adapter documentation (copy in ioBroker.docs or the adapter's own repository), otherwise the repository name |
| `section` | string | Heading path of the chunk inside the file, empty if none |
| `relevance` | number, 0–1 | Cosine similarity of question and chunk in the embedding space. Comparable across queries. |
| `score` | number | Ranking score of this query. With reranker: reranker score minus the penalty for code and unrelated adapter READMEs. Without reranker: fusion score `1/(61+rank)`. Only for ordering within one response. |
| `license` | string | SPDX id of the source repository's license, e.g. `MIT`, `Apache-2.0` |
| `license_status` | string | Verdict of the license policy in `sources.json` for that id: `allow` (permissive), `review` (e.g. GPL, AGPL; indexed only by installations with `index_review: true`) or `deny` |
| `commit` | string | Indexed commit of the source repository |

A client that may only pass on permissively licensed text keeps the entries with `license_status == "allow"`.

Errors: 422 with a `detail` list for an invalid request (missing or too short question, `top_k` out of range, wrong type, unknown field, invalid JSON); 401 for a missing or wrong token.

## `GET /health`

```json
{"status": "ok", "version": "0.4.0", "api_version": 1, "documents": 67660, "model": "BAAI/bge-m3", "built_at": "2026-11-05T19:09:48+0100"}
```

`documents` is the number of chunks in the live index, `built_at` the build time of that index. Needs no token.

## `GET /stats`

```json
{"total_documents": 67660, "collections": {"ioBroker/ioBroker.docs": 30883, "ioBroker/ioBroker.js-controller": 6368}}
```

Chunks per source repository.

## MCP

Streamable HTTP at `/mcp` with the tool `search_iobroker_docs(question, top_k)`. It returns the rendered `context`, see [integrations](integrations.md). The MCP tool is not part of this REST contract.
