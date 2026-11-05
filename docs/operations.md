# Operations

Requirements: about 6 GB RAM and 16 GB disk with reranker. The embedding step takes about one second per chunk without GPU, or about 20 minutes in total on a GPU through Ollama.

1. Copy the repository to `/opt/iobroker-rag`, create the venv, download the models once into `hf/`.
2. Install `deploy/iobroker-rag.service` and `deploy/iobroker-rag-rebuild.timer`.
3. Optional: put `IOB_RAG_OLLAMA=http://<gpu-host>:11434` into `/etc/default/iobroker-rag` so the weekly rebuild embeds on a GPU.

The rebuild writes to `index/staging`, tests it on a spare port with `eval/run.py` and switches only if the test passes. The previous index stays in `index/previous`. To go back, swap `index/live` and `index/previous` and restart the service.

Put private terms into `privacy.local.txt` (never committed). They block chunks during the build, and `tools/check_release.py` checks tracked files before a push.

## Sources

`sources.json` is the hand-made core list. `sources.adapters.json` is generated from the ioBroker Latest repository:

    GITHUB_TOKEN=$(gh auth token) tools/sync_adapters.py

About 1,700 GitHub API calls, 80 seconds with a token (the anonymous limit of 60 calls per hour is not enough). Run it before a build when the adapter list should follow the Latest repository, and commit the result. `tools/check_sources.py` verifies both files against GitHub and the license policy (see `CONTRIBUTING.md`). Repositories whose license the policy denies are listed under `skipped` with a link; nothing of them is indexed.

State on 2026-11-05: 839 adapters in Latest, 819 listed (795 `allow`, 24 `review`, not indexed by default), 20 skipped (15 denied licenses, 5 already in `sources.json`).

## Incremental rebuild

Every build without `--full` is incremental:

1. `git ls-remote` for every repository already in the live index (8 in parallel). Repositories whose tip equals the indexed commit are not fetched; the existing checkout is used. 810 repositories take about 55 seconds.
2. Chunks are always written from scratch, so deleted files and removed repositories do not survive. The log lists `changed`, `new`, `removed` and `unreachable` repositories; an unreachable one keeps its old checkout.
3. Every chunk whose heading and text are unchanged takes its vector from the live index (SHA-1 of the text). Only new or changed chunks are embedded. `meta.embedding` in `chunks.db` records how many were embedded and how many reused.

`--full` (or `FULL=1 deploy/rebuild.sh`) fetches and embeds everything; needed after a change of the embedding model, which otherwise disables the reuse automatically (model name and dimension are compared).

Checkouts are sparse: only the included directories and the root files are downloaded (`--filter=blob:none --sparse`). Existing full checkouts keep working.

### Numbers

Measured on 2026-11-05 on a 4-core machine without GPU, sample of 40 adapter repositories drawn at random from the `allow` list:

| | sample (40 repositories) | projected for 819 |
|---|---|---|
| chunks | 1,317 | about 27,000 |
| checkout on disk | 177 MB sparse (323 MB full clone) | about 3.6 GB (7 GB) |
| clone + chunk, first run | 69 s | about 25 minutes |

The core index has about 62,000 chunks, of which the English `adapterref` copies for adapters now indexed from their own repository disappear. Expect an index of roughly 80,000 chunks. Embedding the new chunks once takes about 10 minutes on a GPU through Ollama, or about 8 hours on the CPU; afterwards a weekly incremental run embeds only what changed.

Still to measure on the production machine after the first full build: total build time with all adapters, RAM during the build, size of the weekly change set and the time of an incremental run. `eval/run.py` with both question sets before and after.
