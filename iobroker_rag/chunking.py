"""Split markdown along headings and source code along blank lines."""
from __future__ import annotations

import re

MAX_CHARS = 1800
OVERLAP = 200
MIN_CHARS = 40
HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*#*$")
FENCE = re.compile(r"^\s*(```|~~~)")


def split_long(text: str, max_chars: int = MAX_CHARS, overlap: int = OVERLAP) -> list[str]:
    if len(text) <= max_chars:
        return [text]
    parts, start = [], 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        if end < len(text):
            cut = max(text.rfind("\n\n", start, end), text.rfind("\n", start + max_chars // 2, end))
            if cut > start:
                end = cut
        parts.append(text[start:end].strip())
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return [p for p in parts if p]


def chunk_markdown(text: str) -> list[tuple[str, str]]:
    """[(heading path, body)]; a '#' inside a code fence is a comment, not a heading."""
    text = re.sub(r"\A---\n.*?\n---\n", "", text, flags=re.S)
    stack: list[tuple[int, str]] = []
    sections: list[tuple[str, list[str]]] = [("", [])]
    in_fence = False
    for line in text.splitlines():
        if FENCE.match(line):
            in_fence = not in_fence
        m = None if in_fence else HEADING.match(line)
        if m:
            level = len(m.group(1))
            stack = [s for s in stack if s[0] < level] + [(level, m.group(2))]
            sections.append((" > ".join(s[1] for s in stack), [line]))
        else:
            sections[-1][1].append(line)
    out = []
    for heading, lines in sections:
        body = "\n".join(lines).strip()
        if len(body) >= MIN_CHARS:
            out.extend((heading, part) for part in split_long(body))
    return out


def chunk_code(text: str) -> list[tuple[str, str]]:
    return [("", part) for part in split_long(text) if len(part) >= MIN_CHARS]
