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
    return json.loads(path.read_text(encoding="utf-8"))


def sync_repo(entry: dict, repos_dir: Path) -> Path:
    """Blobless clone: full tree, file contents fetched on checkout only."""
    target = repos_dir / entry["repo"].split("/")[-1]
    url = f"https://github.com/{entry['repo']}.git"
    if (target / ".git").exists():
        subprocess.run(["git", "-C", str(target), "fetch", "--depth=1", "origin", entry["branch"]], check=True)
        subprocess.run(["git", "-C", str(target), "reset", "--hard", "FETCH_HEAD"], check=True)
    else:
        repos_dir.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", "--depth=1", "--branch", entry["branch"], url, str(target)], check=True)
    return target


def repo_commit(root: Path) -> str:
    return subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()


def is_excluded(rel: str, config: dict) -> bool:
    if Path(rel).name in config["exclude_files"]:
        return True
    padded = f"/{rel}"
    return any(f"/{d}/" in padded for d in config["exclude_dirs"])


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
        files = [base] if base.is_file() else sorted(p for p in base.rglob("*") if p.is_file())
        for full in files:
            rel = full.relative_to(root).as_posix()
            if full.suffix.lower() not in TEXT_SUFFIXES or is_excluded(rel, config):
                continue
            if full.stat().st_size > config["max_file_bytes"]:
                continue
            language = language_of(rel)
            if language not in config["languages"]:
                continue
            yield SourceFile(entry["repo"], rel, full, commit, entry["license"], language,
                             "doc" if full.suffix.lower() == ".md" else "code")
