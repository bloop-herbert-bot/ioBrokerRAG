"""License policy, generated adapter sources and the incremental build."""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

from iobroker_rag import build, licenses, search, sources

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import sync_adapters  # noqa: E402

POLICY = {"allow": ["MIT", "Apache-2.0"], "review": ["GPL-*"], "deny": ["NOASSERTION", "none", "CC-BY-NC-*"]}


def test_classify_follows_policy_and_denies_unknown():
    assert licenses.classify("MIT", POLICY) == "allow"
    assert licenses.classify("GPL-3.0", POLICY) == "review"
    assert licenses.classify("CC-BY-NC-4.0", POLICY) == "deny"
    assert licenses.classify(None, POLICY) == "deny"
    assert licenses.classify("NOASSERTION", POLICY) == "deny"
    assert licenses.classify("WTFPL", POLICY) == "deny"


def test_decide_prefers_github_and_flags_mismatch():
    assert licenses.decide("MIT", "MIT", POLICY) == ("MIT", "allow", False)
    assert licenses.decide("MIT", "Apache 2.0", POLICY) == ("MIT", "allow", True)       # same category, allow stays
    assert licenses.decide("MIT", "GPL-3.0", POLICY) == ("MIT", "review", True)         # categories differ: a human looks
    assert licenses.decide(None, "MIT", POLICY) == ("MIT", "allow", False)              # no LICENSE file, io-package counts
    assert licenses.decide("NOASSERTION", "MIT", POLICY) == ("MIT", "review", True)    # unidentified LICENSE file
    assert licenses.decide("NOASSERTION", None, POLICY) == ("NOASSERTION", "deny", False)
    mit = "Copyright (c) 2026 A\nThe MIT License (MIT)\nCopyright (c) 2016 B\nPermission is hereby granted, free of charge, to any person obtaining a copy"
    assert licenses.decide("NOASSERTION", "MIT", POLICY, mit) == ("MIT", "allow", False)        # text confirms the claim
    assert licenses.decide("NOASSERTION", None, POLICY, mit) == ("MIT", "allow", False)
    assert licenses.decide("NOASSERTION", "GPL-3.0", POLICY, mit) == ("GPL-3.0", "review", True)  # text contradicts it


def test_normalize_and_detect():
    assert licenses.normalize("CC BY-SA 3.0") == "CC-BY-SA-3.0" and licenses.normalize("CC-BY") == "CC-BY"
    assert licenses.normalize("cc by-nc-nd 4.0") == "CC-BY-NC-ND-4.0" and licenses.normalize("GPL-2.0-or-later") == "GPL-2.0"
    assert licenses.normalize("AGPL-3.0-only") == "AGPL-3.0" and licenses.normalize("Apache 2.0") == "Apache-2.0"
    assert licenses.classify("CC-BY-ND-3.0") == "deny" and licenses.classify("CC-BY-SA-3.0") == "review"
    gpl = "This program is free software: you can redistribute it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License"
    assert licenses.detect(gpl) == "GPL-3.0" and licenses.detect("Apache License\n Version 2.0, January 2004") == "Apache-2.0"
    assert licenses.detect("# Icon Licenses\nall sorts of things") == "none" and licenses.detect(None) == "none"


def test_parse_meta_handles_branches_and_monorepos():
    assert sync_adapters.parse_meta("https://raw.githubusercontent.com/TA2k/ioBroker.x/main/io-package.json") == ("TA2k/ioBroker.x", "main", "")
    mono = "https://raw.githubusercontent.com/ioBroker/ioBroker.vis-2/master/packages/iobroker.vis-2/io-package.json"
    assert sync_adapters.parse_meta(mono) == ("ioBroker/ioBroker.vis-2", "master", "packages/iobroker.vis-2/")
    assert sync_adapters.parse_meta("https://example.com/io-package.json") is None


def fake_github(repos: dict):
    return lambda repo: repos.get(repo)


def fake_raw(license_: str | None):
    return lambda url: {"common": {"licenseInformation": {"license": license_}}} if license_ else {}


def test_generator_skips_unknown_license_archived_and_core():
    item = {"meta": "https://raw.githubusercontent.com/a/ioBroker.x/main/io-package.json"}
    gh = fake_github({"a/ioBroker.x": {"license": None, "archived": False}})
    bucket, entry = sync_adapters.build_entry("x", item, False, set(), POLICY, gh, fake_raw(None))
    assert bucket == "skipped" and "denied" in entry["reason"] and "url" in entry
    gh = fake_github({"a/ioBroker.x": {"license": {"spdx_id": "MIT"}, "archived": True}})
    assert sync_adapters.build_entry("x", item, False, set(), POLICY, gh, fake_raw("MIT"))[1]["reason"] == "archived"
    gh = fake_github({})
    assert sync_adapters.build_entry("x", item, False, set(), POLICY, gh, fake_raw("MIT"))[1]["reason"] == "repository not found"
    gh = fake_github({"a/ioBroker.x": {"license": {"spdx_id": "MIT"}, "archived": False}})
    assert sync_adapters.build_entry("x", item, False, {"a/iobroker.x"}, POLICY, gh, fake_raw("MIT"))[0] == "skipped"


def test_generator_entry_has_license_branch_and_include():
    item = {"meta": "https://raw.githubusercontent.com/a/ioBroker.x/dev/io-package.json"}
    gh = fake_github({"a/ioBroker.x": {"license": {"spdx_id": "MIT"}, "archived": False, "default_branch": "dev"}})
    bucket, entry = sync_adapters.build_entry("x", item, True, set(), POLICY, gh, fake_raw("Apache 2.0"))
    assert bucket == "repos"
    assert entry["repo"] == "a/ioBroker.x" and entry["branch"] == "dev" and entry["license"] == "MIT"
    assert entry["stable"] and entry["policy"] == "allow" and entry["license_claimed"] == "Apache-2.0"
    assert entry["include"] == ["README.md", "docs/", "CHANGELOG.md"] and "meta_branch" not in entry
    gh = fake_github({"a/ioBroker.x": {"license": {"spdx_id": "MIT"}, "archived": False, "default_branch": "main"}})
    entry = sync_adapters.build_entry("x", item, True, set(), POLICY, gh, fake_raw("MIT"))[1]
    assert entry["branch"] == "main" and entry["meta_branch"] == "dev"     # renamed since the Latest entry was made
    gh = fake_github({"a/ioBroker.x": {"license": {"spdx_id": "NOASSERTION"}, "archived": False, "default_branch": "dev"}})
    mit = "Copyright (c) A\nThe MIT License\nPermission is hereby granted, free of charge, to any person obtaining a copy"
    entry = sync_adapters.build_entry("x", item, True, set(), POLICY, gh, fake_raw("MIT"), lambda repo: mit)[1]
    assert entry["license"] == "MIT" and entry["policy"] == "allow" and "license_claimed" not in entry
    gh = fake_github({"a/ioBroker.x": {"license": {"spdx_id": "GPL-3.0"}, "archived": False}})
    assert sync_adapters.build_entry("x", item, False, set(), POLICY, gh, fake_raw("GPL-3.0"))[1]["policy"] == "review"


def write_config(tmp_path: Path, generated: list[dict], index_review=False) -> Path:
    core = {"repos": [{"repo": "ioBroker/ioBroker.docs", "branch": "master", "license": "MIT", "include": ["docs/"]}],
            "languages": ["de", "en"], "exclude_dirs": [], "exclude_files": [], "max_file_bytes": 1000, "index_review": index_review}
    (tmp_path / "sources.json").write_text(json.dumps(core), encoding="utf-8")
    (tmp_path / "sources.adapters.json").write_text(json.dumps({"repos": generated}), encoding="utf-8")
    return tmp_path / "sources.json"


def test_load_config_merges_generated_and_respects_policy(tmp_path):
    generated = [{"adapter": "shelly", "repo": "x/ioBroker.shelly", "branch": "main", "license": "MIT", "policy": "allow", "include": ["README.md"]},
                 {"adapter": "gpl", "repo": "x/ioBroker.gpl", "branch": "main", "license": "GPL-3.0", "policy": "review", "include": ["README.md"]},
                 {"adapter": "docs", "repo": "iobroker/ioBroker.docs", "branch": "main", "license": "MIT", "policy": "allow", "include": ["README.md"]}]
    config = sources.load_config(write_config(tmp_path, generated))
    assert [r["repo"] for r in config["repos"]] == ["ioBroker/ioBroker.docs", "x/ioBroker.shelly"]
    assert config["indexed_adapters"] == {"shelly"}
    config = sources.load_config(write_config(tmp_path, generated, index_review=True))
    assert [r["repo"] for r in config["repos"]][1:] == ["x/ioBroker.shelly", "x/ioBroker.gpl"]


def test_load_config_rejects_colliding_checkout_names(tmp_path):
    generated = [{"adapter": "docs", "repo": "x/ioBroker.docs", "branch": "main", "license": "MIT", "policy": "allow", "include": []},
                 {"adapter": "docs2", "repo": "y/ioBroker.DOCS", "branch": "main", "license": "MIT", "policy": "allow", "include": []}]
    try:
        sources.load_config(write_config(tmp_path, generated))
    except ValueError as e:
        assert "iobroker.docs" in str(e)
    else:
        raise AssertionError("collision not detected")


def test_sparse_dirs_from_include_list():
    entry = {"include": ["README.md", "docs/", "CHANGELOG.md", "src/lib/sandbox.ts", "packages/jsonConfig/"]}
    assert sources.sparse_dirs(entry) == ["docs", "packages/jsonConfig", "src/lib"]
    assert sources.sparse_dirs({"include": ["README.md"]}) == []


def test_adapterref_duplicate_only_for_indexed_adapters_and_english():
    config = {"indexed_adapters": {"shelly"}}
    assert sources.is_duplicate_adapterref("docs/en/adapterref/iobroker.shelly/README.md", config)
    assert not sources.is_duplicate_adapterref("docs/de/adapterref/iobroker.shelly/README.md", config)
    assert not sources.is_duplicate_adapterref("docs/en/adapterref/iobroker.hue/README.md", config)
    assert not sources.is_duplicate_adapterref("docs/en/basics/x.md", config)


def test_adapter_name_and_penalty_for_adapter_repositories(monkeypatch):
    monkeypatch.setattr(search, "CORE_BOOST", 2.0)
    assert sources.adapter_name("TA2k/ioBroker.Shelly") == "shelly" and sources.adapter_name("ioBroker/adapter-core") is None
    assert search.adapter_of("TA2k/ioBroker.shelly", "README.md") == "shelly"
    assert search.core_penalty("Wie richte ich Backups ein?", "doc", "README.md", "TA2k/ioBroker.shelly") == 2.0
    assert search.core_penalty("Shelly per MQTT binden", "doc", "README.md", "TA2k/ioBroker.shelly") == 0.0
    assert search.core_penalty("Wie richte ich Backups ein?", "doc", "README.md", "ioBroker/ioBroker.javascript") == 2.0


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def make_repo(tmp_path: Path, name: str) -> Path:
    repo = tmp_path / name
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "--allow-empty", "-m", "init")
    return repo


def test_plan_sync_distinguishes_unchanged_changed_new_removed(tmp_path, monkeypatch):
    repos_dir = tmp_path / "repos"
    repos_dir.mkdir()
    make_repo(repos_dir, "ioBroker.a")
    make_repo(repos_dir, "ioBroker.b")
    config = {"repos": [{"repo": "o/ioBroker.a", "branch": "main"}, {"repo": "o/ioBroker.b", "branch": "main"},
                        {"repo": "o/ioBroker.c", "branch": "main"}]}
    heads = {"o/ioBroker.a": "same", "o/ioBroker.b": "newer"}
    monkeypatch.setattr(sources, "remote_head", lambda entry: heads.get(entry["repo"]))
    previous = {"o/ioBroker.a": "same", "o/ioBroker.b": "older", "o/ioBroker.gone": "x"}
    plan = build.plan_sync(config, repos_dir, previous, None, full=False)
    assert plan["unchanged"] == ["o/ioBroker.a"] and plan["changed"] == ["o/ioBroker.b"]
    assert plan["new"] == ["o/ioBroker.c"] and plan["removed"] == ["o/ioBroker.gone"]
    assert plan["sync"] == {"o/ioBroker.b", "o/ioBroker.c"}
    assert len(build.plan_sync(config, repos_dir, previous, None, full=True)["sync"]) == 3
    heads["o/ioBroker.a"] = None
    assert build.plan_sync(config, repos_dir, previous, None, full=False)["unreachable"] == ["o/ioBroker.a"]


class CountingEmbedder:
    dim = 4
    calls = 0

    def encode(self, texts):
        CountingEmbedder.calls += len(texts)
        return np.asarray([[float(len(t)), 1.0, 0.0, 0.0] for t in texts], dtype=np.float32)


def fill(staging: Path, rows: list[tuple[str, str]]) -> int:
    from iobroker_rag import store
    con = store.create(staging / "chunks.db")
    for n, (heading, text) in enumerate(rows, 1):
        con.execute("INSERT INTO chunks VALUES (?,?,?,?,?,?,?,?,?)", (n, "r", "p", "c", "MIT", "en", "doc", heading, text))
    con.commit()
    con.close()
    return len(rows)


def test_incremental_embedding_reuses_unchanged_chunks(tmp_path, monkeypatch):
    import iobroker_rag.models as models
    monkeypatch.setattr(models, "Embedder", CountingEmbedder)
    monkeypatch.setattr(models, "EMBED_MODEL", "fake")
    monkeypatch.delenv("IOB_RAG_OLLAMA", raising=False)
    live = tmp_path / "live"
    live.mkdir()
    build.embed_all(live, fill(live, [("A", "alpha"), ("B", "beta"), ("C", "gamma")]))
    assert CountingEmbedder.calls == 3
    staging = tmp_path / "staging"
    staging.mkdir()
    count = fill(staging, [("B", "beta"), ("D", "delta"), ("A", "alpha")])   # one new, two moved
    stats = build.embed_all(staging, count, build.Previous(live))
    assert (stats["embedded"], stats["reused"]) == (1, 2) and CountingEmbedder.calls == 4
    vectors = np.fromfile(staging / "vectors.f32", dtype=np.float32).reshape(3, 4)
    assert vectors[0][0] == len("B\nbeta") and vectors[2][0] == len("A\nalpha") and vectors[1][0] == len("D\ndelta")
    assert build.indexed_commits(staging) == {"r": "c"}
    # another model in the live index: nothing is reused
    monkeypatch.setattr(models, "EMBED_MODEL", "other")
    other = tmp_path / "other"
    other.mkdir()
    assert build.embed_all(other, fill(other, [("A", "alpha")]), build.Previous(live))["reused"] == 0
