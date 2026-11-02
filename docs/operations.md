# Operations

Requirements: about 6 GB RAM and 16 GB disk with reranker. The embedding step takes about one second per chunk without GPU, or about 20 minutes in total on a GPU through Ollama.

1. Copy the repository to `/opt/iobroker-rag`, create the venv, download the models once into `hf/`.
2. Install `deploy/iobroker-rag.service` and `deploy/iobroker-rag-rebuild.timer`.

The rebuild writes to `index/staging`, tests it on a spare port with `eval/run.py` and switches only if the test passes. The previous index stays in `index/previous`. To go back, swap `index/live` and `index/previous` and restart the service.

Put private terms into `privacy.local.txt` (never committed). They block chunks during the build, and `tools/check_release.py` checks tracked files before a push.
