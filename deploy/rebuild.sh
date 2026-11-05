#!/bin/bash
# Rebuild into staging, test it on a spare port, switch only after the test passed.
# Incremental by default: unchanged repositories are not fetched, unchanged chunks keep their vectors.
# FULL=1 fetches and embeds everything (after a model change, or once a month).
set -euo pipefail
cd /opt/iobroker-rag
export HF_HOME=/opt/iobroker-rag/hf HF_HUB_OFFLINE=1 TOKENIZERS_PARALLELISM=false
# Set IOB_RAG_OLLAMA=http://<gpu-host>:11434 in /etc/default/iobroker-rag to embed on a GPU; without it the build runs on the CPU.
[ -f /etc/default/iobroker-rag ] && . /etc/default/iobroker-rag
export IOB_RAG_OLLAMA
MIN_HITS="${MIN_HITS:-25}"
MODE=""
[ "${FULL:-0}" = "1" ] && MODE="--full"
if [ -f index/staging/chunks.db ]; then
    .venv/bin/python -m iobroker_rag.build --resume --no-switch $MODE
else
    .venv/bin/python -m iobroker_rag.build --no-switch $MODE
fi
IOB_RAG_INDEX=index/staging .venv/bin/uvicorn iobroker_rag.server:app --host 127.0.0.1 --port 8399 &
TEST=$!
trap 'kill $TEST 2>/dev/null || true' EXIT
for _ in $(seq 1 60); do curl -sf -m 2 localhost:8399/health >/dev/null && break; sleep 3; done
.venv/bin/python eval/run.py http://127.0.0.1:8399 "$MIN_HITS"
kill $TEST; trap - EXIT; wait $TEST 2>/dev/null || true
.venv/bin/python -c "
from pathlib import Path
from iobroker_rag.build import switch
switch(Path('index'), Path('index/staging'))"
