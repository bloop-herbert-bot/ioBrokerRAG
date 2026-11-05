# ioBroker RAG

Local search over public ioBroker documentation and source code, for humans and AI assistants. It runs on your own hardware; no question leaves the machine.

## How it works
- `sources.json` is an allowlist. Only those public repositories are indexed, each with a checked license. `sources.adapters.json` adds the documentation of every adapter in the ioBroker Latest repository whose license the policy allows; it is generated, not maintained by hand.
- Search combines vectors (BGE-M3) and BM25 keywords, then reranks the best candidates.
- Every result names repository, file, commit and license.

The index is built locally and is not distributed. `privacy.local.txt` can list terms that must never enter an index; that file stays out of Git.

The REST API is compatible with [iobroker-rag](https://github.com/Skeletor-ai/iobroker-rag) by Jey-Cee, so existing clients keep working. The code is an independent implementation.

## Use
Requires Python 3.12 or 3.13, about 6 GB RAM and 16 GB disk. The models are downloaded on first use.

```bash
python3 -m venv .venv
.venv/bin/pip install torch --index-url https://download.pytorch.org/whl/cpu
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m iobroker_rag.build --quick
.venv/bin/uvicorn iobroker_rag.server:app --host 127.0.0.1 --port 8321
curl -X POST localhost:8321/query -H 'Content-Type: application/json' -d '{"question":"How do I set a state with ack?","top_k":5}'
```

`--quick` builds a small index for a first try. Without it, all sources are indexed: about 17 hours on a CPU, or about 20 minutes with `IOB_RAG_OLLAMA=http://<host>:11434` on a GPU machine with `ollama pull bge-m3`. Every later build is incremental: only repositories with a new commit are fetched, only changed chunks are embedded.

To connect an AI model, use any MCP client with `http://<host>:8321/mcp`. Details in [integrations](docs/integrations.md).

For long-term operation see [operations](docs/operations.md).

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
