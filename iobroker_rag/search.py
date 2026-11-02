"""Hybrid retrieval: vectors + BM25, Reciprocal Rank Fusion, optional reranking."""
from __future__ import annotations

from dataclasses import dataclass

RRF_K = 60
CANDIDATES = 50
RERANK_POOL = 24


def fuse(rankings: list[list[int]], k: int = RRF_K) -> list[int]:
    scores: dict[int, float] = {}
    for ranking in rankings:
        for rank, item in enumerate(ranking):
            scores[item] = scores.get(item, 0.0) + 1.0 / (k + rank + 1)
    return sorted(scores, key=lambda i: (-scores[i], i))


def diversify(ids: list[int], key, per_file: int = 2) -> list[int]:
    """At most per_file chunks per file first; the same text often exists several times."""
    seen: dict[str, int] = {}
    head, tail = [], []
    for i in ids:
        k = key(i)
        seen[k] = seen.get(k, 0) + 1
        (head if seen[k] <= per_file else tail).append(i)
    return head + tail


@dataclass
class Hit:
    repo: str
    path: str
    heading: str
    text: str
    kind: str
    language: str
    license: str
    commit: str
    score: float
    relevance: float = 0.0


class Searcher:
    def __init__(self, index, embedder, reranker=None):
        self.index, self.embedder, self.reranker = index, embedder, reranker

    def search(self, question: str, top_k: int = 5, rerank: bool = True) -> list[Hit]:
        vector = self.embedder.encode([question])[0]
        ranked = fuse([self.index.dense(vector, CANDIDATES), self.index.keyword(question, CANDIDATES)])
        rows = self.index.fetch(ranked[:CANDIDATES * 2])
        ranked = diversify([i for i in ranked if i in rows], lambda i: f"{rows[i]['repo']}/{rows[i]['path']}")
        scores = {i: 1.0 / (RRF_K + n + 1) for n, i in enumerate(ranked)}
        if rerank and self.reranker is not None:
            pool = ranked[:RERANK_POOL]
            texts = [f"{rows[i]['heading']}\n{rows[i]['text']}" for i in pool]
            scores = dict(zip(pool, self.reranker.score(question, texts)))
            ranked = sorted(pool, key=lambda i: -scores[i])
        top = ranked[:top_k]
        similarity = self.index.similarity(vector, top) if hasattr(self.index, "similarity") else {}
        return [Hit(rows[i]["repo"], rows[i]["path"], rows[i]["heading"], rows[i]["text"], rows[i]["kind"],
                    rows[i]["language"], rows[i]["license"], rows[i]["commit_sha"], float(scores[i]),
                    float(similarity.get(i, 0.0))) for i in top]
