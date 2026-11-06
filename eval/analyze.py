"""Detailed analysis of an answers.py output dir: per vendor and model, judge bias, paired bootstrap of C vs A, effect by retrieval rank.

Usage: python3 eval/analyze.py <out-dir> <questions.jsonl>
"""
import json, random, statistics, sys
from collections import defaultdict
from pathlib import Path

out = Path(sys.argv[1])
qfile = Path(sys.argv[2])
Q = {json.loads(l)["id"]: json.loads(l) for l in open(qfile)}
A = {}
for l in open(out / "answers.jsonl"):
    r = json.loads(l)
    if not r.get("error") and r["id"] in Q:
        A[(r["model"], r["mode"], r["id"])] = r
J = defaultdict(list)
for l in open(out / "judgements.jsonl"):
    r = json.loads(l)
    if not r.get("error") and r["id"] in Q:
        J[(r["model"], r["id"])].append(r)
models = sorted({k[0] for k in J})
tier = {r["model"]: r["tier"] for r in A.values()}
def prov(m):
    return "Anthropic" if m.startswith("claude") else "OpenAI" if m.startswith("gpt") else "Google" if m.startswith("gemini") else "xAI" if m.startswith("grok") else "local"

def score(m, q, mode, judge=None):
    js = [j for j in J.get((m, q), []) if judge is None or j["judge"] == judge]
    return statistics.mean(j["scores"][mode] for j in js) if js else None

def inv(m, q, mode):
    js = J.get((m, q), [])
    return any(j["invented"][mode] for j in js) if js else None

def pct(v): return f"{100 * v / 2:.0f} %"

def boot(diffs, n=5000, seed=1):
    rnd = random.Random(seed)
    means = sorted(statistics.mean(rnd.choices(diffs, k=len(diffs))) for _ in range(n))
    return means[int(0.025 * n)], means[int(0.975 * n)]

L = []
L += ["## Per model: correct (A / B / C), Δ C−A with 95 % bootstrap interval, invented A → C\n",
      "| Vendor | Tier | Model | A | B | C | Δ C−A (points) | significant | invented A → C | median chars A |", "|---|---|---|---|---|---|---|---|---|---|"]
for m in sorted(models, key=lambda m: (prov(m), ["top", "medium", "light", "local"].index(tier[m]))):
    qs = [q for q in Q if (m, q) in J]
    s = {mode: statistics.mean(score(m, q, mode) for q in qs) for mode in "ABC"}
    d = [50 * (score(m, q, "C") - score(m, q, "A")) for q in qs]
    lo, hi = boot(d)
    sig = "yes" if lo > 0 or hi < 0 else "no"
    ia = sum(inv(m, q, "A") for q in qs); ic = sum(inv(m, q, "C") for q in qs)
    chars = statistics.median(len(A[(m, "A", q)]["text"]) for q in qs if (m, "A", q) in A)
    L.append(f"| {prov(m)} | {tier[m]} | {m} | {pct(s['A'])} | {pct(s['B'])} | {pct(s['C'])} | {statistics.mean(d):+.0f} ({lo:+.0f} … {hi:+.0f}) | {sig} | {ia} → {ic} | {chars:.0f} |")

L += ["\n## Per vendor (mean over its models)\n", "| Vendor | A | B | C | invented A / B / C |", "|---|---|---|---|---|"]
for p in ("Anthropic", "OpenAI", "Google", "xAI", "local"):
    ms = [m for m in models if prov(m) == p]
    cells = []
    for mode in "ABC":
        v = [score(m, q, mode) for m in ms for q in Q if (m, q) in J]
        cells.append(pct(statistics.mean(v)))
    iv = [f"{100 * statistics.mean(inv(m, q, mode) for m in ms for q in Q if (m, q) in J):.0f} %" for mode in "ABC"]
    L.append(f"| {p} | " + " | ".join(cells) + " | " + " / ".join(iv) + " |")

judges = sorted({j["judge"] for v in J.values() for j in v})
L += ["\n## Judge bias: mean over all modes per judge\n", "| Model | " + " | ".join(judges) + " | difference 1−2 |", "|---" * (len(judges) + 2) + "|"]
for m in models:
    vals = []
    for jn in judges:
        v = [score(m, q, mode, jn) for q in Q for mode in "ABC" if (m, q) in J and score(m, q, mode, jn) is not None]
        vals.append(statistics.mean(v) if v else float("nan"))
    L.append(f"| {m} | " + " | ".join(pct(v) for v in vals) + f" | {50 * (vals[0] - vals[1]):+.0f} |")

L += ["\n## Ranking per mode (correct)\n"]
for mode in "ABC":
    rk = sorted(models, key=lambda m: -statistics.mean(score(m, q, mode) for q in Q if (m, q) in J))
    L.append(f"- **{mode}:** " + ", ".join(f"{m} {pct(statistics.mean(score(m, q, mode) for q in Q if (m, q) in J))}" for m in rk))

L += ["\n## Retrieval hit vs. effect C−A (cloud models)\n", "| Reranker gold rank in top 5 | questions | Δ C−A |", "|---|---|---|"]
R = json.loads((out / "retrieval.json").read_text())
for label, cond in (("rank 1", lambda r: r == 0), ("rank 2-5", lambda r: r is not None and r > 0), ("not in top 5", lambda r: r is None)):
    qs = [q for q in Q if q in R and cond(R[q]["rerank"]["rank"])]
    d = [50 * (score(m, q, "C") - score(m, q, "A")) for q in qs for m in models if prov(m) != "local" and (m, q) in J]
    L.append(f"| {label} | {len(qs)} | {statistics.mean(d):+.0f} points |" if d else f"| {label} | 0 | - |")
print("\n".join(L))
