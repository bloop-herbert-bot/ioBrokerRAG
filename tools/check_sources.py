#!/usr/bin/env python3
"""Compare the licenses in sources.json with what GitHub reports. Exit 1 on any difference."""
import json
import os
import sys
import urllib.request
from pathlib import Path

config = json.loads((Path(__file__).resolve().parent.parent / "sources.json").read_text(encoding="utf-8"))
headers = {"Accept": "application/vnd.github+json"}
if os.environ.get("GITHUB_TOKEN"):
    headers["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
bad = 0
for entry in config["repos"]:
    request = urllib.request.Request(f"https://api.github.com/repos/{entry['repo']}", headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        found = (json.load(response).get("license") or {}).get("spdx_id")
    if found != entry["license"]:
        print(f"{entry['repo']}: sources.json {entry['license']}, GitHub {found}")
        bad += 1
print(f"{len(config['repos'])} repositories, {bad} differences")
sys.exit(1 if bad else 0)
