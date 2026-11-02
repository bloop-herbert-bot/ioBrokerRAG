"""Build an index into a staging directory; a finished build is switched atomically."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import time
from pathlib import Path

import numpy as np

from . import chunking, privacy, sources, store

ROOT = Path(__file__).resolve().parent.parent
BATCH = 16


def collect(config: dict, repos_dir: Path, skip_sync: bool, only: list[str] | None):
    for entry in config["repos"]:
        if only and entry["repo"] not in only:
            continue
        root = sources.sync_repo(entry, repos_dir) if not skip_sync else repos_dir / entry["repo"].split("/")[-1]
        for f in sources.iter_files(entry, root, config):
            text = f.full_path.read_text(encoding="utf-8", errors="replace")
            if sources.is_minified(text):
                continue
            parts = chunking.chunk_markdown(text) if f.kind == "doc" else chunking.chunk_code(text)
            for heading, body in parts:
                yield f, heading, body


def write_chunks(config: dict, repos_dir: Path, staging: Path, skip_sync: bool, only, limit: int | None) -> int:
    con = store.create(staging / "chunks.db")
    terms = privacy.load_terms(ROOT / "privacy.local.txt")
    count, blocked, seen = 0, 0, set()
    for f, heading, body in collect(config, repos_dir, skip_sync, only):
        if privacy.find_hits(body, terms):
            blocked += 1
            continue
        fingerprint = hash((f.language, body))
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        count += 1
        con.execute("INSERT INTO chunks VALUES (?,?,?,?,?,?,?,?,?)",
                    (count, f.repo, f.path, f.commit, f.license, f.language, f.kind, heading, body))
        if limit and count >= limit:
            break
    con.execute("INSERT INTO chunks_fts(chunks_fts) VALUES ('rebuild')")
    con.execute("INSERT INTO meta VALUES ('blocked_private', ?)", (json.dumps(blocked),))
    con.commit()
    con.close()
    print(f"chunks: {count}, blocked by privacy list: {blocked}", flush=True)
    return count


def embed_all(staging: Path, count: int) -> None:
    """Resumable: the vector file grows in row order, so a restart continues at its end."""
    import sqlite3
    from .models import EMBED_MODEL, Embedder, OllamaEmbedder
    url = os.environ.get("IOB_RAG_OLLAMA")
    embedder = OllamaEmbedder(url) if url else Embedder()
    batch = 64 if url else BATCH
    path = staging / "vectors.f32"
    width = embedder.dim * 4
    done = path.stat().st_size // width if path.exists() else 0
    if path.exists():
        os.truncate(path, done * width)   # an interrupted write leaves a partial row
    con = sqlite3.connect(staging / "chunks.db")
    started = time.time()
    with path.open("ab") as out:
        for step, start in enumerate(range(done, count, batch), 1):
            rows = con.execute("SELECT heading, text FROM chunks WHERE id > ? ORDER BY id LIMIT ?", (start, batch)).fetchall()
            out.write(embedder.encode([f"{h}\n{t}".strip() for h, t in rows]).tobytes())
            out.flush()
            finished = start + len(rows)
            if step % 25 == 0:
                rate = (finished - done) / max(time.time() - started, 1)
                print(f"embedded {finished}/{count}, {rate:.1f}/s, rest {(count - finished) / max(rate, .01) / 3600:.1f} h", flush=True)
    np.save(staging / "ids.npy", np.arange(1, count + 1))
    con.execute("INSERT OR REPLACE INTO meta VALUES ('dim', ?)", (json.dumps(embedder.dim),))
    con.execute("INSERT OR REPLACE INTO meta VALUES ('embed_model', ?)", (json.dumps(EMBED_MODEL),))
    con.execute("INSERT OR REPLACE INTO meta VALUES ('built_at', ?)", (json.dumps(time.strftime("%Y-%m-%dT%H:%M:%S%z")),))
    con.commit()
    con.close()


def switch(index_dir: Path, staging: Path) -> None:
    live = index_dir / "live"
    old = index_dir / "previous"
    shutil.rmtree(old, ignore_errors=True)
    if live.exists():
        live.rename(old)
    staging.rename(live)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-sync", action="store_true")
    parser.add_argument("--resume", action="store_true", help="continue embedding an unfinished staging build")
    parser.add_argument("--only", nargs="*", help="limit to these repositories")
    parser.add_argument("--limit", type=int, help="stop after this many chunks, for tests")
    parser.add_argument("--chunks-only", action="store_true")
    parser.add_argument("--no-switch", action="store_true")
    args = parser.parse_args()
    config = sources.load_config(ROOT / "sources.json")
    index_dir = ROOT / "index"
    staging = index_dir / "staging"
    if args.resume:
        import sqlite3
        count = sqlite3.connect(staging / "chunks.db").execute("SELECT count(*) FROM chunks").fetchone()[0]
    else:
        shutil.rmtree(staging, ignore_errors=True)
        staging.mkdir(parents=True)
        count = write_chunks(config, ROOT / "data" / "repos", staging, args.skip_sync, args.only, args.limit)
    if args.chunks_only:
        return
    embed_all(staging, count)
    if not args.no_switch:
        switch(index_dir, staging)
        print("index switched", flush=True)


if __name__ == "__main__":
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    main()
