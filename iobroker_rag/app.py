"""Web application: REST for scripts, MCP for AI clients. Both use the same search."""
from __future__ import annotations

import hmac
import os
import time
from contextlib import asynccontextmanager

import anyio
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from pydantic import BaseModel, Field

from . import __version__, search

MAX_TOP_K = 20
INSTRUCTIONS = ("Search public ioBroker documentation and source code. Results are background knowledge about "
                "ioBroker, not the state of the user's system. Name the source file in your answer.")


class Query(BaseModel):
    question: str = Field(min_length=2, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=MAX_TOP_K)
    rerank: bool = True
    include_prompt: bool = False


def source_name(hit) -> str:
    return f"{hit.repo.split('/')[-1]}/{hit.path}"


def adapter_of(hit) -> str:
    """'iobroker.shelly' for adapter documentation (ioBroker.docs copy or the adapter's own repository)."""
    name = search.adapter_of(hit.repo, hit.path)
    return f"iobroker.{name}" if name else hit.repo.split("/")[-1]


def render(hits) -> str:
    return "\n\n---\n\n".join(
        f"[Source: {source_name(h)}" + (f" § {h.heading}" if h.heading else "")
        + f" | {h.kind} | {h.license} | relevance: {h.relevance:.2f}]\n{h.text}" for h in hits)


def create_app(index, searcher) -> FastAPI:
    token = os.environ.get("IOB_RAG_TOKEN", "")
    origins = [o.strip() for o in os.environ.get("IOB_RAG_CORS", "").split(",") if o.strip()]
    mcp = MCPServer("ioBroker RAG", version=__version__, instructions=INSTRUCTIONS)

    @mcp.tool()
    async def search_iobroker_docs(question: str, top_k: int = 5) -> str:
        """Search ioBroker documentation and source code. Use it for questions about scripts, adapters,
        objects, states, Blockly, VIS, Admin, installation and error messages."""
        limit = max(1, min(top_k, MAX_TOP_K))
        hits = await anyio.to_thread.run_sync(searcher.search, question[:2000], limit)
        return render(hits) or "No results."

    # This service has no cookies or sessions, so the Host check protects nothing. Access is limited by the token.
    security = TransportSecuritySettings(enable_dns_rebinding_protection=False)
    mcp_app = mcp.streamable_http_app(stateless_http=True, json_response=True, transport_security=security)

    @asynccontextmanager
    async def lifespan(_):
        async with mcp.session_manager.run():
            yield

    app = FastAPI(title="ioBroker RAG", version=__version__, lifespan=lifespan)

    @app.middleware("http")
    async def require_token(request: Request, call_next):
        sent = request.headers.get("authorization", "").removeprefix("Bearer ").strip()
        public = request.url.path == "/health" or request.method == "OPTIONS"
        if token and not public and not hmac.compare_digest(sent, token):
            return JSONResponse({"detail": "unauthorized"}, status_code=401)
        return await call_next(request)

    if origins:
        app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["GET", "POST"],
                           allow_headers=["authorization", "content-type"])

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "documents": len(index), "model": index.meta["embed_model"],
                "built_at": index.meta.get("built_at"), "version": __version__}

    @app.get("/stats")
    def stats() -> dict:
        rows = index.con.execute("SELECT repo, count(*) FROM chunks GROUP BY repo").fetchall()
        return {"total_documents": len(index), "collections": {r[0]: r[1] for r in rows}}

    @app.post("/query")
    def query(q: Query) -> dict:
        started = time.perf_counter()
        hits = searcher.search(q.question, q.top_k, q.rerank)
        context = render(hits)
        answer = {
            "context": context,
            "sources": [{"file": source_name(h), "type": h.kind, "language": h.language, "adapter": adapter_of(h),
                         "section": h.heading, "relevance": round(h.relevance, 3), "license": h.license,
                         "commit": h.commit, "score": h.score} for h in hits],
            "query_time_ms": round((time.perf_counter() - started) * 1000, 1),
            "total_results": len(hits),
        }
        if q.include_prompt:
            answer["prompt"] = f"Answer using only this ioBroker context. Name the source.\n\n{context}\n\nQuestion: {q.question}"
        return answer

    app.mount("/", mcp_app)
    return app
