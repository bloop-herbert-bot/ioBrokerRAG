# ioBroker RAG

Local search over public ioBroker documentation and source code, for humans and AI assistants. It runs on your own hardware; no question leaves the machine.

## How it works
- `sources.json` is an allowlist. Only those public repositories are indexed, each with a checked license.
- Search combines vectors (BGE-M3) and BM25 keywords, then reranks the best candidates.
- Every result names repository, file, commit and license.

The index is built locally and is not distributed. `privacy.local.txt` can list terms that must never enter an index; that file stays out of Git.

## Use
```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m iobroker_rag.build
.venv/bin/uvicorn iobroker_rag.server:app --host 127.0.0.1 --port 8322
curl -X POST localhost:8322/query -H 'Content-Type: application/json' -d '{"question":"How do I set a state with ack?","top_k":5}'
```

The server also speaks MCP at `/mcp`. See [integrations](docs/integrations.md) and [operations](docs/operations.md).

## Tests
```bash
pip install -r requirements-dev.txt
pytest
```
`eval/run.py` measures search quality against a running server.

## Contributing
See [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md).

## License
MIT. Indexed content stays under the license of its source repository.
