"""Build an index into a staging directory; a finished build is switched atomically.

Incremental by default: repositories whose remote tip equals the indexed commit are not fetched again, and
chunks whose text is unchanged take their vector from the live index instead of being embedded again.
Chunks are always written from scratch, so deleted files and removed repositories simply do not reappear.
`--full` fetches and embeds everything, e.g. after a model change.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

from . import chunking, privacy, sources, store

ROOT = Path(__file__).resolve().parent.parent
BATCH = 16
QUICK = ["ioBroker/ioBroker.javascript", "ioBroker/adapter-core", "ioBroker/ioBroker", "ioBroker/create-adapter"]


def chunk_key(heading: str, text: str) -> str:
    return hashlib.sha1(f"{heading}\n{text}".strip().encode("utf-8")).hexdigest()


def indexed_commits(index: Path) -> dict[str, str]:
    """repo -> commit of the live index; empty when there is none."""
    db = index / "chunks.db"
    if not db.exists():
        return {}
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        return dict(con.execute("SELECT repo, max(commit_sha) FROM chunks GROUP BY repo").fetchall())
    finally:
        con.close()


def plan_sync(config: dict, repos_dir: Path, previous: dict[str, str], only, full: bool) -> dict:
    """Which repositories need a fetch. Unchanged = checkout present and remote tip equals the indexed commit."""
    plan = {"sync": set(), "unchanged": [], "changed": [], "new": [], "unreachable": [], "removed": []}
    wanted = {e["repo"] for e in config["repos"] if not only or e["repo"] in only}
    if not only:
        plan["removed"] = sorted(set(previous) - wanted)
    entries = [e for e in config["repos"] if e["repo"] in wanted]
    ask = [e for e in entries if not full and e["repo"] in previous and (sources.checkout_dir(e, repos_dir) / ".git").exists()]
    with ThreadPoolExecutor(8) as pool:        # one ls-remote per repository, 800 of them take a minute in parallel
        heads = dict(zip((e["repo"] for e in ask), pool.map(sources.remote_head, ask)))
    for entry in entries:
        repo = entry["repo"]
        if repo not in heads:
            plan["sync"].add(repo)
            plan["new" if repo not in previous else "changed"].append(repo)
            continue
        head = heads[repo]
        if head is None:
            plan["unreachable"].append(repo)    # keep the old checkout rather than lose the repository
        elif head == previous[repo]:
            plan["unchanged"].append(repo)
        else:
            plan["sync"].add(repo)
            plan["changed"].append(repo)
    return plan


def collect(config: dict, repos_dir: Path, to_sync: set[str] | None, only: list[str] | None):
    """to_sync None = sync everything (old behaviour); a set syncs only those repositories."""
    for entry in config["repos"]:
        if only and entry["repo"] not in only:
            continue
        if to_sync is None or entry["repo"] in to_sync:
            try:
                root = sources.sync_repo(entry, repos_dir)
            except subprocess.CalledProcessError as e:
                if not entry.get("generated"):
                    raise       # a hand-made source must be there
                print(f"skipped {entry['repo']}: git failed ({e.returncode}), e.g. branch renamed; regenerate the list", flush=True)
                continue
        else:
            root = sources.checkout_dir(entry, repos_dir)
        if not (root / ".git").exists():
            continue
        for f in sources.iter_files(entry, root, config):
            text = f.full_path.read_text(encoding="utf-8", errors="replace")
            if sources.is_minified(text):
                continue
            parts = chunking.chunk_markdown(text) if f.kind == "doc" else chunking.chunk_code(text)
            for heading, body in parts:
                yield f, heading, body


def write_chunks(config: dict, repos_dir: Path, staging: Path, to_sync, only, limit: int | None) -> int:
    con = store.create(staging / "chunks.db")
    terms = privacy.load_terms(ROOT / "privacy.local.txt")
    count, blocked, seen = 0, 0, set()
    for f, heading, body in collect(config, repos_dir, to_sync, only):
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


class Previous:
    """Vectors of the live index, addressed by chunk text, for reuse. Empty if there is no usable index."""

    def __init__(self, index: Path):
        self.rows: dict[str, int] = {}
        self.vectors, self.model, self.dim = None, None, None
        db = index / "chunks.db"
        if not db.exists() or not (index / "vectors.f32").exists():
            return
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        try:
            meta = {k: json.loads(v) for k, v in con.execute("SELECT key, value FROM meta").fetchall()}
            self.model, self.dim = meta.get("embed_model"), meta.get("dim")
            total = con.execute("SELECT count(*) FROM chunks").fetchone()[0]
            if not self.dim or (index / "vectors.f32").stat().st_size < total * self.dim * 4:
                return
            self.vectors = np.memmap(index / "vectors.f32", dtype=np.float32, mode="r", shape=(total, self.dim))
            for cid, heading, text in con.execute("SELECT id, heading, text FROM chunks"):
                self.rows[chunk_key(heading, text)] = cid - 1
        finally:
            con.close()

    def usable(self, model: str, dim: int) -> bool:
        return self.vectors is not None and self.model == model and self.dim == dim

    def __len__(self) -> int:
        return len(self.rows)


def embed_all(staging: Path, count: int, previous: Previous | None = None) -> dict:
    """Resumable: the vector file grows in row order, so a restart continues at its end."""
    from .models import EMBED_MODEL, Embedder, OllamaEmbedder
    url = os.environ.get("IOB_RAG_OLLAMA")
    embedder = OllamaEmbedder(url) if url else Embedder()
    batch = 64 if url else BATCH
    path = staging / "vectors.f32"
    width = embedder.dim * 4
    done = path.stat().st_size // width if path.exists() else 0
    if path.exists():
        os.truncate(path, done * width)   # an interrupted write leaves a partial row
    if previous is not None and not previous.usable(EMBED_MODEL, embedder.dim):
        previous = None     # other model or dimension: every vector is computed again
    con = sqlite3.connect(staging / "chunks.db")
    started, reused, embedded = time.time(), 0, 0
    with path.open("ab") as out:
        for step, start in enumerate(range(done, count, batch), 1):
            rows = con.execute("SELECT heading, text FROM chunks WHERE id > ? ORDER BY id LIMIT ?", (start, batch)).fetchall()
            matrix = np.empty((len(rows), embedder.dim), dtype=np.float32)
            fresh = []
            for n, (h, t) in enumerate(rows):
                old = previous.rows.get(chunk_key(h, t)) if previous else None
                if old is None:
                    fresh.append(n)
                else:
                    matrix[n] = previous.vectors[old]
            if fresh:
                matrix[fresh] = embedder.encode([f"{rows[n][0]}\n{rows[n][1]}".strip() for n in fresh])
            reused, embedded = reused + len(rows) - len(fresh), embedded + len(fresh)
            out.write(matrix.tobytes())
            out.flush()
            finished = start + len(rows)
            if step % 25 == 0:
                rate = (finished - done) / max(time.time() - started, 1)
                print(f"embedded {finished}/{count} ({embedded} new, {reused} reused), {rate:.1f}/s, "
                      f"rest {(count - finished) / max(rate, .01) / 3600:.1f} h", flush=True)
    np.save(staging / "ids.npy", np.arange(1, count + 1))
    stats = {"embedded": embedded, "reused": reused, "seconds": round(time.time() - started)}
    con.execute("INSERT OR REPLACE INTO meta VALUES ('dim', ?)", (json.dumps(embedder.dim),))
    con.execute("INSERT OR REPLACE INTO meta VALUES ('embed_model', ?)", (json.dumps(EMBED_MODEL),))
    con.execute("INSERT OR REPLACE INTO meta VALUES ('built_at', ?)", (json.dumps(time.strftime("%Y-%m-%dT%H:%M:%S%z")),))
    con.execute("INSERT OR REPLACE INTO meta VALUES ('embedding', ?)", (json.dumps(stats),))
    con.commit()
    con.close()
    print(f"embedding: {stats}", flush=True)
    return stats


def switch(index_dir: Path, staging: Path) -> None:
    live = index_dir / "live"
    old = index_dir / "previous"
    shutil.rmtree(old, ignore_errors=True)
    if live.exists():
        live.rename(old)
    staging.rename(live)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-sync", action="store_true", help="use the checkouts as they are")
    parser.add_argument("--full", action="store_true", help="fetch and embed everything, no reuse of the live index")
    parser.add_argument("--resume", action="store_true", help="continue embedding an unfinished staging build")
    parser.add_argument("--only", nargs="*", help="limit to these repositories")
    parser.add_argument("--quick", action="store_true", help="small index for a first try, minutes instead of hours")
    parser.add_argument("--limit", type=int, help="stop after this many chunks, for tests")
    parser.add_argument("--chunks-only", action="store_true")
    parser.add_argument("--no-switch", action="store_true")
    args = parser.parse_args()
    if args.quick:
        args.only = QUICK
    config = sources.load_config(ROOT / "sources.json")
    index_dir = ROOT / "index"
    staging, live = index_dir / "staging", index_dir / "live"
    if args.resume:
        count = sqlite3.connect(staging / "chunks.db").execute("SELECT count(*) FROM chunks").fetchone()[0]
    else:
        previous_commits = {} if args.full else indexed_commits(live)
        if args.skip_sync:
            to_sync: set[str] | None = set()
        else:
            plan = plan_sync(config, ROOT / "data" / "repos", previous_commits, args.only, args.full)
            to_sync = plan.pop("sync")
            print("repositories: " + ", ".join(f"{k} {len(v)}" for k, v in plan.items()), flush=True)
            for key in ("changed", "new", "removed", "unreachable"):
                if plan[key]:
                    print(f"  {key}: {' '.join(plan[key])}", flush=True)
        shutil.rmtree(staging, ignore_errors=True)
        staging.mkdir(parents=True)
        count = write_chunks(config, ROOT / "data" / "repos", staging, to_sync, args.only, args.limit)
        if not args.skip_sync:
            con = sqlite3.connect(staging / "chunks.db")
            con.execute("INSERT INTO meta VALUES ('repositories', ?)", (json.dumps({k: len(v) for k, v in plan.items()}),))
            con.commit()
            con.close()
    if args.chunks_only:
        return
    previous = None
    if not args.full:
        previous = Previous(live)
        print(f"vectors in the live index: {len(previous)}", flush=True)
    embed_all(staging, count, previous)
    if not args.no_switch:
        switch(index_dir, staging)
        print("index switched", flush=True)


if __name__ == "__main__":
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    main()
