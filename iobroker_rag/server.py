"""Entry point for uvicorn: loads the index and the models once."""
from __future__ import annotations

import os
from pathlib import Path

from .app import create_app
from .models import Embedder, Reranker
from .search import Searcher
from .store import Index

ROOT = Path(__file__).resolve().parent.parent
index = Index(Path(os.environ.get("IOB_RAG_INDEX", ROOT / "index" / "live")))
app = create_app(index, Searcher(index, Embedder(index.meta["embed_model"]), Reranker()))
