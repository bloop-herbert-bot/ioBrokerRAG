"""Model wrappers. Imported lazily so tests run without torch."""
from __future__ import annotations

import os

import numpy as np

EMBED_MODEL = os.environ.get("IOB_RAG_EMBED", "BAAI/bge-m3")
RERANK_MODEL = os.environ.get("IOB_RAG_RERANK", "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1")


class Embedder:
    def __init__(self, name: str = EMBED_MODEL):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(name, device="cpu")
        self.model.max_seq_length = 512
        self.dim = self.model.get_sentence_embedding_dimension()

    def encode(self, texts: list[str], batch_size: int = 16) -> np.ndarray:
        vectors = self.model.encode(texts, batch_size=batch_size, normalize_embeddings=True, show_progress_bar=False)
        return np.asarray(vectors, dtype=np.float32)


class Reranker:
    def __init__(self, name: str = RERANK_MODEL):
        from sentence_transformers import CrossEncoder
        self.model = CrossEncoder(name, device="cpu", max_length=512)

    def score(self, question: str, texts: list[str]) -> list[float]:
        return [float(s) for s in self.model.predict([(question, t) for t in texts], show_progress_bar=False)]
