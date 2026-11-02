import numpy as np

from iobroker_rag import chunking, privacy, search, sources, store


def test_hash_in_code_fence_is_no_heading():
    text = "# Title\n\nsome introduction text that is long enough\n\n```bash\n# comment\nls\n```\nmore text after the code block"
    parts = chunking.chunk_markdown(text)
    assert len(parts) == 1 and "# comment" in parts[0][1]


def test_heading_path():
    text = "# A\n\n" + "x" * 50 + "\n\n## B\n\n" + "y" * 50
    assert [p[0] for p in chunking.chunk_markdown(text)] == ["A", "A > B"]


def test_split_long_terminates_and_keeps_size():
    parts = chunking.split_long("a" * 5000)
    assert all(len(p) <= chunking.MAX_CHARS for p in parts) and "".join(parts).count("a") >= 5000


def test_fuse_prefers_items_in_both_lists():
    assert search.fuse([[1, 2, 3], [3, 4, 5]])[0] == 3


def test_diversify_limits_one_file():
    assert search.diversify([1, 2, 3, 4], lambda i: "a" if i < 4 else "b", per_file=2) == [1, 2, 4, 3]


def test_language_and_excludes():
    config = {"exclude_files": ["package-lock.json"], "exclude_dirs": ["node_modules", "admin/assets"]}
    assert sources.language_of("docs/de/dev/x.md") == "de"
    assert sources.language_of("README.md") == "en"
    assert sources.is_excluded("a/node_modules/b.js", config)
    assert sources.is_excluded("admin/assets/x.js", config)
    assert not sources.is_excluded("docs/en/admin.md", config)


def test_privacy_hits(tmp_path):
    f = tmp_path / "p.txt"
    f.write_text("# comment\nSecret.Example\n", encoding="utf-8")
    terms = privacy.load_terms(f)
    assert privacy.find_hits("a secret.example b", terms) == ["secret.example"]
    assert privacy.load_terms(tmp_path / "missing.txt") == []


def test_fts_query_keeps_api_names_and_quotes():
    q = store.fts_query('wie nutze ich setState("x")?')
    assert '"setstate"' in q and q.count('"') % 2 == 0


class FakeIndex:
    def dense(self, v, n):
        return [1, 2]

    def keyword(self, q, n):
        return [2, 3]

    def fetch(self, ids):
        return {i: dict(repo="r", path=f"p{i}", heading="", text=f"t{i}", kind="doc", language="en",
                        license="MIT", commit_sha="c") for i in ids}


class FakeEmbedder:
    def encode(self, texts):
        return np.zeros((1, 2))


class FakeReranker:
    def score(self, q, texts):
        return [1.0 if t.endswith("t3") else 0.0 for t in texts]


def test_search_without_and_with_reranker():
    assert search.Searcher(FakeIndex(), FakeEmbedder()).search("q", 1)[0].path == "p2"
    assert search.Searcher(FakeIndex(), FakeEmbedder(), FakeReranker()).search("q", 1)[0].path == "p3"
