"""Clone the allowlisted repositories and yield the files that may be indexed."""
from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

TEXT_SUFFIXES = {".md", ".ts", ".js", ".tsx", ".json"}
LANG_DIR = re.compile(r"(?:^|/)docs/([a-z]{2}(?:-[a-z]{2})?)/", re.I)
ADAPTERREF_EN = re.compile(r"^docs/en/adapterref/iobroker\.([^/]+)/", re.I)
ADAPTER_REPO = re.compile(r"/iobroker\.([^/]+)$", re.I)


@dataclass(frozen=True)
class SourceFile:
    repo: str
    path: str
    full_path: Path
    commit: str
    license: str
    language: str
    kind: str


def load_config(path: Path) -> dict:
    """sources.json plus the generated adapter list next to it. Generated entries never override hand-made ones."""
    config = json.loads(path.read_text(encoding="utf-8"))
    config["indexed_adapters"] = set()
    generated = path.parent / config.get("generated", "sources.adapters.json")
    if not generated.exists():
        return config
    core = {r["repo"].lower() for r in config["repos"]}
    wanted = {"allow"} | ({"review"} if config.get("index_review") else set())
    for entry in json.loads(generated.read_text(encoding="utf-8"))["repos"]:
        if entry.get("policy", "allow") in wanted and entry["repo"].lower() not in core:
            config["repos"].append({**entry, "generated": True})
            config["indexed_adapters"].add(entry["adapter"].lower())
    names = [r["repo"].split("/")[-1].lower() for r in config["repos"]]
    doubled = sorted({n for n in names if names.count(n) > 1})
    if doubled:
        raise ValueError(f"two sources share a repository name, checkouts would collide: {doubled}")
    return config


def adapter_name(repo: str) -> str | None:
    """'owner/ioBroker.shelly' -> 'shelly'; None for anything that is not an adapter repository."""
    m = ADAPTER_REPO.search(repo)
    return m.group(1).lower() if m else None


def checkout_dir(entry: dict, repos_dir: Path) -> Path:
    """data/repos/<repository name>; load_config rejects two entries with the same name."""
    return repos_dir / entry["repo"].split("/")[-1]


def remote_head(entry: dict) -> str | None:
    """Commit at the remote branch tip without fetching anything; None if the remote is unreachable."""
    url = f"https://github.com/{entry['repo']}.git"
    try:
        out = subprocess.check_output(["git", "ls-remote", url, f"refs/heads/{entry['branch']}"], text=True,
                                      stderr=subprocess.DEVNULL, timeout=60)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return None
    return out.split()[0] if out.strip() else None


def sparse_dirs(entry: dict) -> list[str]:
    """Directories of the include list ('docs/' -> docs, 'src/lib/x.ts' -> src/lib); root files always come along."""
    dirs = set()
    for p in entry["include"]:
        if p.endswith("/"):
            dirs.add(p.rstrip("/"))
        elif "/" in p:
            dirs.add(p.rsplit("/", 1)[0])
    return sorted(dirs)


def sync_repo(entry: dict, repos_dir: Path) -> Path:
    """Shallow clone of one branch; only the included directories and the root files are checked out, blobs outside
    them are never downloaded. With 800 adapter repositories this is the difference between 1 and 7 GB."""
    target = checkout_dir(entry, repos_dir)
    url = f"https://github.com/{entry['repo']}.git"
    if (target / ".git").exists():
        subprocess.run(["git", "-C", str(target), "fetch", "--depth=1", "origin", entry["branch"]], check=True)
        subprocess.run(["git", "-C", str(target), "reset", "--hard", "FETCH_HEAD"], check=True)
    else:
        repos_dir.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", "-q", "--depth=1", "--filter=blob:none", "--sparse", "--branch", entry["branch"],
                        url, str(target)], check=True)
        subprocess.run(["git", "-C", str(target), "sparse-checkout", "set", *sparse_dirs(entry)], check=True)
    return target


def repo_commit(root: Path) -> str:
    return subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()


def is_excluded(rel: str, config: dict) -> bool:
    if Path(rel).name in config["exclude_files"]:
        return True
    padded = f"/{rel}"
    return any(f"/{d}/" in padded for d in config["exclude_dirs"])


def is_duplicate_adapterref(rel: str, config: dict) -> bool:
    """ioBroker.docs keeps English copies of adapter READMEs. Skip them once the original repository is indexed;
    translations stay, the original has none."""
    m = ADAPTERREF_EN.match(rel)
    return bool(m) and m.group(1).lower() in config.get("indexed_adapters", ())


def language_of(rel: str) -> str:
    m = LANG_DIR.search(rel)
    return m.group(1).lower() if m else "en"


def is_minified(text: str) -> bool:
    lines = text.splitlines() or [""]
    return max(len(line) for line in lines) > 5000


def iter_files(entry: dict, root: Path, config: dict) -> Iterator[SourceFile]:
    commit = repo_commit(root)
    for include in entry["include"]:
        base = root / include
        if not base.exists():
            continue        # generated entries list README.md, docs/ and CHANGELOG.md; not every adapter has all three
        files = [base] if base.is_file() else sorted(p for p in base.rglob("*") if p.is_file())
        for full in files:
            rel = full.relative_to(root).as_posix()
            if full.suffix.lower() not in TEXT_SUFFIXES or is_excluded(rel, config) or is_duplicate_adapterref(rel, config):
                continue
            if full.stat().st_size > config["max_file_bytes"]:
                continue
            language = language_of(rel)
            if language not in config["languages"]:
                continue
            yield SourceFile(entry["repo"], rel, full, commit, entry["license"], language,
                             "doc" if full.suffix.lower() == ".md" else "code")
