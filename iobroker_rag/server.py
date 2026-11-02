"""HTTP API: POST /query, GET /health. Binds to the address given to uvicorn."""
from __future__ import annotations

import os
import re
import time
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel, Field

from .models import Embedder, Reranker
from .search import Searcher
from .store import Index

ROOT = Path(__file__).resolve().parent.parent
index = Index(Path(os.environ.get("IOB_RAG_INDEX", ROOT / "index" / "live")))
searcher = Searcher(index, Embedder(index.meta["embed_model"]), Reranker())
app = FastAPI(title="ioBroker RAG")


class Query(BaseModel):
    question: str = Field(min_length=2, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=20)
    rerank: bool = True
    include_prompt: bool = False


def source_name(hit) -> str:
    return f"{hit.repo.split('/')[-1]}/{hit.path}"


def adapter_of(hit) -> str:
    match = re.search(r"adapterref/(iobroker\.[^/]+)/", hit.path)
    return match.group(1) if match else hit.repo.split("/")[-1]


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "documents": len(index), "model": index.meta["embed_model"], "built_at": index.meta.get("built_at")}


@app.get("/stats")
def stats() -> dict:
    rows = index.con.execute("SELECT repo, count(*) FROM chunks GROUP BY repo").fetchall()
    return {"total_documents": len(index), "collections": {r[0]: r[1] for r in rows}}


@app.post("/query")
def query(q: Query) -> dict:
    started = time.perf_counter()
    hits = searcher.search(q.question, q.top_k, q.rerank)
    blocks = [f"[Source: {source_name(h)}" + (f" § {h.heading}" if h.heading else "")
              + f" | {h.kind} | {h.license} | relevance: {h.relevance:.2f}]\n{h.text}" for h in hits]
    context = "\n\n---\n\n".join(blocks)
    answer = {
        "context": context,
        "sources": [{"file": source_name(h), "type": h.kind, "language": h.language, "adapter": adapter_of(h),
                     "section": h.heading, "relevance": round(h.relevance, 3), "license": h.license, "commit": h.commit,
                     "score": h.score} for h in hits],
        "query_time_ms": round((time.perf_counter() - started) * 1000, 1),
        "total_results": len(hits),
    }
    if q.include_prompt:
        answer["prompt"] = f"Answer using only this ioBroker context. Name the source.\n\n{context}\n\nQuestion: {q.question}"
    return answer
