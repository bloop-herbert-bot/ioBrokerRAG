#!/usr/bin/env python3
"""Run before every push: no tracked file may contain a term from privacy.local.txt."""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from iobroker_rag.privacy import find_hits, load_terms  # noqa: E402

root = Path(__file__).resolve().parent.parent
terms = load_terms(root / "privacy.local.txt")
if not terms:
    sys.exit("privacy.local.txt is missing or empty, nothing was checked")
hits = 0
for name in subprocess.check_output(["git", "-C", str(root), "ls-files"], text=True).splitlines():
    try:
        found = find_hits((root / name).read_text(encoding="utf-8"), terms)
    except (UnicodeDecodeError, OSError):
        continue
    if found:
        print(f"{name}: {len(found)} private term(s)")
        hits += 1
print(f"{hits} files with private terms")
sys.exit(1 if hits else 0)
