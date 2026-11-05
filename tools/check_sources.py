#!/usr/bin/env python3
"""Check every source against GitHub and the license policy. Exit 1 on any difference.

sources.json: the recorded license must equal what GitHub reports and must be allowed.
sources.adapters.json: the same, plus the verdict must match the policy, archived repositories must not be listed,
and entries with a claimed license that differs from GitHub are reported.
"""
import base64
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from iobroker_rag import licenses  # noqa: E402

root = Path(__file__).resolve().parent.parent
config = json.loads((root / "sources.json").read_text(encoding="utf-8"))
policy = config.get("license_policy") or licenses.DEFAULT_POLICY
headers = {"Accept": "application/vnd.github+json"}
if os.environ.get("GITHUB_TOKEN"):
    headers["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"


def github(url: str) -> dict | None:
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


def check(entry: dict, generated: bool) -> list[str]:
    """Same decision as the generator: GitHub's SPDX id, the LICENSE text for NOASSERTION, the recorded claim."""
    info = github(f"https://api.github.com/repos/{entry['repo']}")
    if info is None:
        return ["repository not found"]
    spdx = (info.get("license") or {}).get("spdx_id")
    text = None
    if spdx == "NOASSERTION":
        data = github(f"https://api.github.com/repos/{entry['repo']}/license") or {}
        text = base64.b64decode(data["content"]).decode("utf-8", "replace") if data.get("encoding") == "base64" else None
    claimed = entry.get("license_claimed", entry["license"])
    found, verdict, mismatch = licenses.decide(spdx, claimed, policy, text)
    problems = []
    if found != entry["license"]:
        problems.append(f"license recorded {entry['license']}, GitHub {found}")
    if generated:
        if info.get("archived"):
            problems.append("archived on GitHub")
        if verdict == "deny":
            problems.append(f"license {found} is denied by the policy")
        elif entry.get("policy") != verdict:
            problems.append(f"policy recorded {entry.get('policy')}, is {verdict}")
        if mismatch:
            problems.append(f"io-package.json claims {claimed} (information)")
    elif verdict != "allow":
        problems.append(f"license {found} is not allowed for a hand-made source")
    return problems


bad = total = 0
for name, generated in (("sources.json", False), (config.get("generated", "sources.adapters.json"), True)):
    path = root / name
    if not path.exists():
        continue
    entries = json.loads(path.read_text(encoding="utf-8"))["repos"]
    only = sys.argv[1:]
    for entry in entries:
        if only and entry["repo"] not in only:
            continue
        total += 1
        problems = check(entry, generated)
        for p in problems:
            print(f"{entry['repo']}: {p}")
        bad += any("(information)" not in p for p in problems)
print(f"{total} repositories, {bad} with differences")
sys.exit(1 if bad else 0)
