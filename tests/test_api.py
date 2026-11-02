import json

import pytest
from fastapi.testclient import TestClient

from iobroker_rag.app import create_app
from iobroker_rag.search import Hit

MCP_HEADERS = {"Accept": "application/json, text/event-stream", "Content-Type": "application/json"}


class FakeIndex:
    meta = {"embed_model": "fake"}

    def __len__(self):
        return 1


class FakeSearcher:
    def search(self, question, top_k=5, rerank=True):
        return [Hit("ioBroker/ioBroker.docs", "docs/en/adapterref/iobroker.shelly/README.md", "Setup", "text", "doc",
                    "en", "MIT", "abc", 1.0, 0.71)][:top_k]


@pytest.fixture
def client():
    with TestClient(create_app(FakeIndex(), FakeSearcher())) as c:
        yield c


def rpc(client, method, params=None, headers=None):
    body = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}}
    return client.post("/mcp", json=body, headers={**MCP_HEADERS, **(headers or {})})


def test_rest_contract_used_by_existing_clients(client):
    d = client.post("/query", json={"question": "setState", "top_k": 1, "include_prompt": True}).json()
    assert "relevance: 0.71]" in d["context"] and d["sources"][0]["adapter"] == "iobroker.shelly"
    assert d["sources"][0]["relevance"] == 0.71 and "prompt" in d


def test_rejects_bad_query(client):
    assert client.post("/query", json={"question": "x"}).status_code == 422


def test_mcp_lists_and_calls_the_tool(client):
    init = {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "t", "version": "1"}}
    assert rpc(client, "initialize", init).status_code == 200
    tools = rpc(client, "tools/list").json()["result"]["tools"]
    assert [t["name"] for t in tools] == ["search_iobroker_docs"]
    r = rpc(client, "tools/call", {"name": "search_iobroker_docs", "arguments": {"question": "shelly", "top_k": 99}})
    assert "iobroker.shelly" in json.dumps(r.json()["result"])


def test_token(monkeypatch):
    monkeypatch.setenv("IOB_RAG_TOKEN", "secret")
    with TestClient(create_app(FakeIndex(), FakeSearcher())) as c:
        assert c.get("/health").status_code == 200
        assert c.post("/query", json={"question": "abc"}).status_code == 401
        assert rpc(c, "tools/list").status_code == 401
        ok = c.post("/query", json={"question": "abc"}, headers={"Authorization": "Bearer secret"})
        assert ok.status_code == 200
