"""Release gate: private terms from privacy.local.txt must never appear in chunks."""
from __future__ import annotations

from pathlib import Path


def load_terms(path: Path) -> list[str]:
    if not path.exists():
        return []
    lines = (line.strip() for line in path.read_text(encoding="utf-8").splitlines())
    return [line.lower() for line in lines if line and not line.startswith("#")]


def find_hits(text: str, terms: list[str]) -> list[str]:
    low = text.lower()
    return [term for term in terms if term in low]
