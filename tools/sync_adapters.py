#!/usr/bin/env python3
"""Generate sources.adapters.json from the ioBroker Latest repository (sources-dist.json).

For every adapter: repository and branch from the `meta` URL, license from the GitHub API and from io-package.json,
verdict from the policy in sources.json. Archived repositories and denied licenses are listed under `skipped`
with a link only, nothing of them is indexed. sources.json stays the hand-made core list and wins on overlap.

    GITHUB_TOKEN=$(gh auth token) tools/sync_adapters.py            # all adapters
    tools/sync_adapters.py --limit 20 --out /tmp/test.json          # a sample
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from iobroker_rag import licenses  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
LATEST = "https://raw.githubusercontent.com/ioBroker/ioBroker.repositories/master/sources-dist.json"
STABLE = "https://raw.githubusercontent.com/ioBroker/ioBroker.repositories/master/sources-dist-stable.json"
META = re.compile(r"^https://raw\.githubusercontent\.com/([^/]+)/([^/]+)/([^/]+)/(.*?)io-package\.json$")
INCLUDE = ["README.md", "docs/", "CHANGELOG.md"]


def token() -> str:
    if os.environ.get("GITHUB_TOKEN"):
        return os.environ["GITHUB_TOKEN"]
    try:
        return subprocess.check_output(["gh", "auth", "token"], text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


def fetch_json(url: str, headers: dict | None = None) -> dict | None:
    """None for 404 (repository or file gone); other errors are raised, a half-generated list is worse than none."""
    request = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise
    except json.JSONDecodeError:
        return None


def parse_meta(url: str) -> tuple[str, str, str] | None:
    """('owner/repo', branch, subdir) or None for anything that is not a GitHub raw URL."""
    m = META.match(url)
    return (f"{m.group(1)}/{m.group(2)}", m.group(3), m.group(4)) if m else None


def package_license(package: dict | None) -> str | None:
    common = (package or {}).get("common") or {}
    info = common.get("licenseInformation") or {}
    return info.get("license") or common.get("license")


def license_text(repo: str, headers: dict) -> str | None:
    """Text of the LICENSE file, needed only when GitHub reports NOASSERTION."""
    data = fetch_json(f"https://api.github.com/repos/{repo}/license", headers)
    if not data or data.get("encoding") != "base64":
        return None
    return base64.b64decode(data["content"]).decode("utf-8", errors="replace")


def build_entry(name: str, item: dict, stable: bool, core: set[str], policy: dict, github, raw, text=None) -> tuple[str, dict]:
    """('repos' | 'skipped', entry). github(repo), raw(url) and text(repo) are fetchers, replaceable in tests."""
    parsed = parse_meta(item.get("meta", ""))
    link = item.get("meta", "")
    if not parsed:
        return "skipped", {"adapter": name, "reason": "meta is not a GitHub raw URL", "url": link}
    repo, branch, subdir = parsed
    if repo.lower() in core:
        return "skipped", {"adapter": name, "repo": repo, "reason": "already in sources.json"}
    info = github(repo)
    if info is None:
        return "skipped", {"adapter": name, "repo": repo, "reason": "repository not found"}
    if info.get("archived"):
        return "skipped", {"adapter": name, "repo": repo, "reason": "archived"}
    claimed = package_license(raw(item["meta"]))
    spdx = (info.get("license") or {}).get("spdx_id")
    body = text(repo) if spdx == "NOASSERTION" and text else None
    recorded, verdict, mismatch = licenses.decide(spdx, claimed, policy, body)
    # the default branch is where the README lives; the branch in the meta URL may have been renamed since
    entry = {"adapter": name, "repo": repo, "branch": info.get("default_branch") or branch, "license": recorded,
             "policy": verdict, "stable": stable, "include": [subdir + p for p in INCLUDE]}
    if entry["branch"] != branch:
        entry["meta_branch"] = branch
    if mismatch:
        entry["license_claimed"] = licenses.normalize(claimed)
    if verdict == "deny":
        return "skipped", {"adapter": name, "repo": repo, "reason": f"license {recorded} denied by policy",
                           "url": f"https://github.com/{repo}"}
    return "repos", entry


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source", default=LATEST, help="sources-dist.json, URL or file")
    parser.add_argument("--stable", default=STABLE, help="sources-dist-stable.json, URL or file")
    parser.add_argument("--out", default=str(ROOT / "sources.adapters.json"))
    parser.add_argument("--limit", type=int, help="first N adapters only, for a test run")
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()

    def load(location: str) -> dict:
        data = json.loads(Path(location).read_text(encoding="utf-8")) if Path(location).exists() else fetch_json(location)
        data.pop("_repoInfo", None)
        return data

    latest, stable = load(args.source), set(load(args.stable))
    config = json.loads((ROOT / "sources.json").read_text(encoding="utf-8"))
    policy = config.get("license_policy") or licenses.DEFAULT_POLICY
    core = {r["repo"].lower() for r in config["repos"]}
    headers = {"Accept": "application/vnd.github+json"}
    if token():
        headers["Authorization"] = f"Bearer {token()}"
    names = sorted(latest)[: args.limit] if args.limit else sorted(latest)

    def work(name: str) -> tuple[str, dict]:
        return build_entry(name, latest[name], name in stable, core, policy,
                           lambda repo: fetch_json(f"https://api.github.com/repos/{repo}", headers), fetch_json,
                           lambda repo: license_text(repo, headers))

    result: dict[str, list] = {"repos": [], "skipped": []}
    with ThreadPoolExecutor(args.workers) as pool:
        for n, (bucket, entry) in enumerate(pool.map(work, names), 1):
            result[bucket].append(entry)
            if n % 100 == 0:
                print(f"{n}/{len(names)}", file=sys.stderr, flush=True)
    counts = {"adapters": len(names), "indexed": len(result["repos"]), "skipped": len(result["skipped"]),
              "review": sum(e["policy"] == "review" for e in result["repos"]),
              "mismatch": sum("license_claimed" in e for e in result["repos"])}
    out = {"_comment": "Generated by tools/sync_adapters.py from the ioBroker Latest repository. Do not edit by hand.",
           "source": args.source, "counts": counts, **result}
    Path(args.out).write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(counts))
    reasons: dict[str, int] = {}
    for s in result["skipped"]:
        key = re.sub(r"license \S+ denied", "license denied", s["reason"])
        reasons[key] = reasons.get(key, 0) + 1
    print("skipped:", json.dumps(reasons))


if __name__ == "__main__":
    main()
