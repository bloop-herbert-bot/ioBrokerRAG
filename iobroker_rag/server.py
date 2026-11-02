"""HTTP API: POST /query, GET /health. Binds to the address given to uvicorn."""
from __future__ import annotations

import os
from dataclasses import asdict
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


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "documents": len(index), "model": index.meta["embed_model"], "built_at": index.meta.get("built_at")}


@app.post("/query")
def query(q: Query) -> dict:
    hits = searcher.search(q.question, q.top_k, q.rerank)
    blocks = [f"[Source: {h.repo.split('/')[-1]}/{h.path}"
              + (f" § {h.heading}" if h.heading else "") + f" | {h.kind} | {h.license}]\n{h.text}" for h in hits]
    return {"context": "\n\n---\n\n".join(blocks), "sources": [
        {**{k: v for k, v in asdict(h).items() if k != "text"}, "file": f"{h.repo.split('/')[-1]}/{h.path}", "section": h.heading}
        for h in hits]}
