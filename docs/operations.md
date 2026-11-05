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

First full build with all adapters, 2026-11-05, production machine (4 cores, 6 GB RAM, no GPU, embeddings through Ollama on a GPU host):

| | before (core only) | after (core + 819 adapters) |
|---|---|---|
| repositories | 15 | 834 (829 with chunks) |
| chunks | 61,903 | 67,660 (core 39,166, adapters 28,494) |
| of which ioBroker.docs | 53,928 | 30,883 (English `adapterref` copies dropped) |
| checkouts on disk | 2.3 GB | 3.5 GB (sparse) |
| index on disk | 551 MB | 302 MB |
| clone + chunk | | 29 min |
| embedding (GPU via Ollama, `--full`) | about 20 min | 27 min (67,660 vectors, 42/s) |
| build total incl. test and switch | | 59 min |
| RAM peak of the build | | 3.8 GB |

The index got smaller because the English adapter READMEs copied into ioBroker.docs were indexed once per adapter before and are now replaced by the original. The 24 `review` adapters are included on this installation (`index_review: true`).

Retrieval test (`eval/run.py`, top 5 with reranker), before → after:

| set | hits@1 | hits@5 | MRR |
|---|---|---|---|
| release set, 30 questions | 21 → 20 | 27 | 0.768 |
| practice set, 65 questions | 31 → 28 | 54 → 49 | 0.608 → 0.539 |

The adapter sources did not improve the practice set; five questions lost their top-5 hit. All of them are general questions (orphaned objects, disabling an instance, VIS bindings, error messages) whose answer lives in the core documentation and that are now answered with chunks of unrelated adapter READMEs, mostly the German `adapterref` copies and adapter `docs/` folders. Two variants were measured against the same index and rejected: a rerank pool that puts unpenalized chunks first (release 26/30, practice 47/65) and `IOB_RAG_CORE_BOOST=4` (release 27/30 with hits@1 19, practice 48/65 with hits@1 30, MRR 0.552). The reranker, not the candidate pool, prefers the adapter chunks; a quota per source type is the next thing to try.

Still to measure: size of a typical weekly change set and the time of an incremental run (first weekly timer run after this build).
