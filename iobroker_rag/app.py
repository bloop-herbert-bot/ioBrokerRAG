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
from pydantic import BaseModel, ConfigDict, Field

from . import __version__, licenses, search

MAX_TOP_K = 20
API_VERSION = 1  # contract in docs/api.md; raised only for breaking changes
INSTRUCTIONS = ("Search public ioBroker documentation and source code. Results are background knowledge about "
                "ioBroker, not the state of the user's system. Name the source file in your answer.")


class Query(BaseModel):
    model_config = ConfigDict(extra="forbid")  # a misspelt field is an error, not a silent default

    question: str = Field(min_length=2, max_length=2000, description="Question in natural language, German or English.")
    top_k: int = Field(default=5, ge=1, le=MAX_TOP_K, description="Number of results.")
    rerank: bool = Field(default=True, description="Rerank the candidates with the cross-encoder. Better order, about 3 s slower.")
    include_prompt: bool = Field(default=False, description="Also return a ready prompt with the context and the question.")


class Source(BaseModel):
    file: str = Field(description="Repository name and path of the file, e.g. 'ioBroker.docs/docs/en/admin.md'.")
    repo: str = Field(description="GitHub repository, 'owner/name'.")
    type: str = Field(description="'doc' for documentation, 'code' for source code.")
    language: str = Field(description="Language of the text, 'de' or 'en'.")
    adapter: str = Field(description="'iobroker.<name>' for adapter documentation, otherwise the repository name.")
    section: str = Field(description="Heading path of the chunk inside the file, empty if none.")
    relevance: float = Field(description="Cosine similarity of question and chunk in the embedding space, 0..1. "
                                         "Comparable across queries.")
    score: float = Field(description="Ranking score of this query: reranker score minus the penalty for code and "
                                     "unrelated adapter READMEs, or the fusion score 1/(61+rank) without reranker. "
                                     "Only for ordering within one response.")
    license: str = Field(description="SPDX license id of the source repository, e.g. 'MIT'.")
    license_status: str = Field(description="Verdict of the license policy for that id: 'allow' (permissive), "
                                            "'review' (e.g. copyleft, indexed only by installations that opted in) "
                                            "or 'deny'.")
    commit: str = Field(description="Indexed commit of the source repository.")


class QueryResponse(BaseModel):
    context: str = Field(description="All results rendered as text for a prompt, each with a "
                                     "'[Source: file § section | type | license | relevance: x]' header.")
    sources: list[Source] = Field(description="The results, best first.")
    query_time_ms: float = Field(description="Search time on the server.")
    total_results: int = Field(description="Number of entries in sources.")
    prompt: str | None = Field(default=None, description="Only with include_prompt=true.")


class Health(BaseModel):
    status: str = Field(description="'ok'.")
    version: str = Field(description="Server version.")
    api_version: int = Field(description="Version of the REST contract in docs/api.md.")
    documents: int = Field(description="Chunks in the live index.")
    model: str = Field(description="Embedding model of the index.")
    built_at: str | None = Field(description="Build time of the live index, ISO 8601.")


class Stats(BaseModel):
    total_documents: int = Field(description="Chunks in the live index.")
    collections: dict[str, int] = Field(description="Chunks per source repository.")


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


def create_app(index, searcher, license_policy: dict | None = None) -> FastAPI:
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

    @app.get("/health", response_model=Health)
    def health() -> dict:
        return {"status": "ok", "documents": len(index), "model": index.meta["embed_model"],
                "built_at": index.meta.get("built_at"), "version": __version__, "api_version": API_VERSION}

    @app.get("/stats", response_model=Stats)
    def stats() -> dict:
        rows = index.con.execute("SELECT repo, count(*) FROM chunks GROUP BY repo").fetchall()
        return {"total_documents": len(index), "collections": {r[0]: r[1] for r in rows}}

    @app.post("/query", response_model=QueryResponse, response_model_exclude_none=True)
    def query(q: Query) -> dict:
        started = time.perf_counter()
        hits = searcher.search(q.question, q.top_k, q.rerank)
        context = render(hits)
        answer = {
            "context": context,
            "sources": [{"file": source_name(h), "repo": h.repo, "type": h.kind, "language": h.language,
                         "adapter": adapter_of(h), "section": h.heading or "", "relevance": round(h.relevance, 3),
                         "score": h.score, "license": h.license,
                         "license_status": licenses.classify(h.license, license_policy), "commit": h.commit}
                        for h in hits],
            "query_time_ms": round((time.perf_counter() - started) * 1000, 1),
            "total_results": len(hits),
        }
        if q.include_prompt:
            answer["prompt"] = f"Answer using only this ioBroker context. Name the source.\n\n{context}\n\nQuestion: {q.question}"
        return answer

    app.mount("/", mcp_app)
    return app
