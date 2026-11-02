"""Index on disk: SQLite with FTS5 for text, one float32 matrix for vectors."""
from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

import numpy as np

SCHEMA = """
CREATE TABLE chunks(id INTEGER PRIMARY KEY, repo TEXT, path TEXT, commit_sha TEXT, license TEXT,
                    language TEXT, kind TEXT, heading TEXT, text TEXT);
CREATE VIRTUAL TABLE chunks_fts USING fts5(heading, text, content='chunks', content_rowid='id',
                                           tokenize="unicode61 tokenchars '._$'");
CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT);
"""
WORD = re.compile(r"[\w.$]{2,}", re.UNICODE)


def create(db_path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(db_path)
    con.executescript(SCHEMA)
    return con


def fts_query(question: str) -> str:
    words = list(dict.fromkeys(w.lower().strip(".") for w in WORD.findall(question)))
    return " OR ".join('"' + w.replace('"', "") + '"' for w in words if w)


class Index:
    def __init__(self, directory: Path):
        self.directory = directory
        self.con = sqlite3.connect(f"file:{directory / 'chunks.db'}?mode=ro", uri=True, check_same_thread=False)
        self.con.row_factory = sqlite3.Row
        meta = dict(self.con.execute("SELECT key, value FROM meta").fetchall())
        self.meta = {k: json.loads(v) for k, v in meta.items()}
        self.ids = np.load(directory / "ids.npy")
        self.vectors = np.memmap(directory / "vectors.f32", dtype=np.float32, mode="r",
                                 shape=(len(self.ids), self.meta["dim"]))

    def __len__(self) -> int:
        return len(self.ids)

    def dense(self, vector: np.ndarray, limit: int) -> list[int]:
        scores = np.asarray(self.vectors @ vector)
        limit = min(limit, len(scores))
        top = np.argpartition(-scores, limit - 1)[:limit]
        return [int(self.ids[i]) for i in top[np.argsort(-scores[top])]]

    def similarity(self, vector: np.ndarray, ids: list[int]) -> dict[int, float]:
        """Cosine per chunk id; row = id - 1, ids are consecutive from 1."""
        return {i: float(self.vectors[i - 1] @ vector) for i in ids}

    def keyword(self, question: str, limit: int) -> list[int]:
        query = fts_query(question)
        if not query:
            return []
        rows = self.con.execute("SELECT rowid FROM chunks_fts WHERE chunks_fts MATCH ? ORDER BY bm25(chunks_fts, 4.0, 1.0) LIMIT ?",
                                (query, limit))
        return [r[0] for r in rows]

    def fetch(self, ids: list[int]) -> dict[int, sqlite3.Row]:
        if not ids:
            return {}
        marks = ",".join("?" * len(ids))
        rows = self.con.execute(f"SELECT * FROM chunks WHERE id IN ({marks})", ids).fetchall()
        return {r["id"]: r for r in rows}
