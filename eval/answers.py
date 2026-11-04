"""Answer quality with and without RAG: models answer eval/answers-questions.jsonl in three modes, blind judges grade.

Modes: A = no context, B = top-1 document without reranker, C = top-5 documents with reranker.
Every step is cached in the output directory, a second run only fills gaps. See eval/README.md.
"""
import argparse, json, os, random, statistics, subprocess, threading, time, urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
MODES = {"A": None, "B": {"top_k": 1, "rerank": False}, "C": {"top_k": 5, "rerank": True}}
SYS = ("You are an ioBroker expert. Answer briefly and concretely, with code where useful. "
       "If you are not sure, say so. Answer in the language of the question.")
SYS_RAG = SYS + (" Use the documentation context. If it does not cover the question, say so and answer from your own "
                 "knowledge. Name the source file you used.")
JUDGE = """You grade answers to an ioBroker question. You get the question, reference facts written by a human, and three answers.
Grade every answer on its own:
2 = technically correct and usable, covers the essential reference facts, no wrong function, option or path.
1 = partly correct, incomplete or with a minor error.
0 = wrong, unusable, or relies on invented functions, options, paths or state IDs.
The reference facts are the ground truth. Do not reward length, politeness or cited sources. Facts beyond the reference are fine if they are correct.
Also mark "invented": true if the answer contains a function, option, path or state ID that does not exist in ioBroker.
Reply with JSON only: {"1": {"score": 0, "invented": false}, "2": {...}, "3": {...}, "why": "<one sentence>"}"""

lock = threading.Lock()


def post(url, body, headers=None, timeout=300):
    r = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json", **(headers or {})})
    return json.load(urllib.request.urlopen(r, timeout=timeout))


def load_jsonl(path):
    return [json.loads(l) for l in open(path, encoding="utf-8")] if path.exists() else []


def append(path, row):
    with lock, open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


class Caller:
    """One call = one system prompt + one user prompt. Returns (text, seconds)."""

    def __init__(self, backends):
        self.backends = backends
        self.overhead = {}

    def __call__(self, spec, system, user):
        b = self.backends[spec["backend"]]
        t = time.time()
        if b["type"] == "openai":
            key = os.environ.get(b.get("api_key_env", ""), "")
            body = {"model": spec["model"], "temperature": 0,
                    "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
            d = post(b["base_url"].rstrip("/") + "/chat/completions", body, {"Authorization": f"Bearer {key}"} if key else None, 600)
            text = d["choices"][0]["message"]["content"] or ""
        elif b["type"] == "ollama":
            body = {"model": spec["model"], "stream": False, "options": {"temperature": 0, "num_ctx": b.get("num_ctx", 16384)},
                    "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
            text = post(b["base_url"].rstrip("/") + "/api/chat", body, timeout=900)["message"]["content"] or ""
        elif b["type"] == "openclaw":
            cmd = ["openclaw", "infer", "model", "run", "--model", spec["model"], "--json", "--prompt", f"{system}\n\n{user}"]
            if b.get("agent"):
                cmd += ["--agent", b["agent"]]
            if spec.get("thinking"):
                cmd += ["--thinking", spec["thinking"]]
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            out = p.stdout[p.stdout.find("{"):]
            d = json.loads(out) if out else {"ok": False, "error": {"message": p.stderr[-300:]}}
            if not d.get("ok"):
                raise RuntimeError(d.get("error", {}).get("message", "openclaw failed")[:300])
            text = d["outputs"][0]["text"] or ""
        else:
            raise ValueError(f"unknown backend type {b['type']}")
        if "</think>" in text:
            text = text.split("</think>")[-1].strip()
        if not text.strip():
            raise RuntimeError("empty answer")
        return text, time.time() - t - self.overhead.get(spec["backend"], 0)

    def calibrate(self, spec):
        """Local models get one untimed call to load them. CLI backends start a process per call;
        its fixed cost is measured once and subtracted from latencies."""
        if self.backends[spec["backend"]]["type"] in ("openai", "ollama"):
            self(spec, "Reply with OK only.", "OK")
            return
        if spec["backend"] in self.overhead:
            return
        times = [self(spec, "Reply with OK only.", "OK")[1] for _ in range(3)]
        self.overhead[spec["backend"]] = statistics.median(times)


def retrieve(rag, questions, out):
    path = out / "retrieval.json"
    cache = json.loads(path.read_text()) if path.exists() else {}
    for x in questions:
        if x["id"] in cache:
            continue
        row = {}
        for mode, params in MODES.items():
            if params:
                d = post(rag.rstrip("/") + "/query", {"question": x["q"], **params})
                row[mode] = {"context": d["context"], "ms": d["query_time_ms"]}
        for name, rr in (("plain", False), ("rerank", True)):
            d = post(rag.rstrip("/") + "/query", {"question": x["q"], "top_k": 5, "rerank": rr})
            files = [s["file"] for s in d["sources"]]
            rank = next((i for i, f in enumerate(files) if any(g.lower() in f.lower() for g in x["gold"])), None)
            row[name] = {"files": files, "rank": rank, "ms": d["query_time_ms"]}
        cache[x["id"]] = row
        path.write_text(json.dumps(cache, ensure_ascii=False))
        print(f"retrieval {x['id']}: plain rank {row['plain']['rank']}, rerank rank {row['rerank']['rank']}", flush=True)
    return cache


def answer_all(call, models, questions, ctx, out, workers):
    path = out / "answers.jsonl"
    done = {(r["model"], r["mode"], r["id"]) for r in load_jsonl(path) if not r.get("error")}
    todo = [(m, mode, x) for m in models for mode in MODES for x in questions if (m["name"], mode, x["id"]) not in done]

    def one(job):
        m, mode, x = job
        row = {"model": m["name"], "tier": m["tier"], "mode": mode, "id": x["id"]}
        try:
            if mode == "A":
                row["text"], row["seconds"] = call(m, SYS, x["q"])
            else:
                row["text"], row["seconds"] = call(m, SYS_RAG, f"Documentation context:\n\n{ctx[x['id']][mode]['context']}\n\nQuestion: {x['q']}")
            row["seconds"] = round(row["seconds"], 2)
        except Exception as e:
            row["error"] = str(e)[:300]
        append(path, row)
        print(f"answer {m['name']} {mode} {x['id']} {'ERROR ' + row['error'][:80] if 'error' in row else ''}", flush=True)

    print(f"{len(todo)} answers to fetch", flush=True)
    with ThreadPoolExecutor(workers) as ex:
        list(ex.map(one, todo))


def judge_all(call, judges, questions, out, workers):
    answers = {}
    for r in load_jsonl(out / "answers.jsonl"):
        if not r.get("error"):
            answers[(r["model"], r["id"], r["mode"])] = r["text"]
    path = out / "judgements.jsonl"
    done = {(r["judge"], r["model"], r["id"]) for r in load_jsonl(path) if not r.get("error")}
    models = sorted({k[0] for k in answers})
    todo = [(j, m, x) for j in judges for m in models for x in questions
            if (j["name"], m, x["id"]) not in done and all((m, x["id"], mode) in answers for mode in MODES)]

    def one(job):
        j, m, x = job
        order = list(MODES)
        random.Random(f"{m}|{x['id']}").shuffle(order)
        facts = "\n".join(f"- {f}" for f in x["facts"])
        prompt = f"Question: {x['q']}\n\nReference facts:\n{facts}\n\n" + "\n\n".join(
            f"Answer {i + 1}:\n{answers[(m, x['id'], mode)]}" for i, mode in enumerate(order))
        row = {"judge": j["name"], "model": m, "id": x["id"]}
        try:
            text, _ = call(j, JUDGE, prompt)
            d = json.JSONDecoder().raw_decode(text[text.find("{"):])[0]
            row["scores"] = {mode: int(d[str(i + 1)]["score"]) for i, mode in enumerate(order)}
            row["invented"] = {mode: bool(d[str(i + 1)].get("invented")) for i, mode in enumerate(order)}
            row["why"] = d.get("why", "")
        except Exception as e:
            row["error"] = str(e)[:300]
        append(path, row)
        print(f"judge {j['name']} {m} {x['id']} {row.get('scores', row.get('error', ''))}", flush=True)

    print(f"{len(todo)} judgements to fetch", flush=True)
    with ThreadPoolExecutor(workers) as ex:
        list(ex.map(one, todo))


def pct(a, b):
    return f"{100 * a / b:.0f} %" if b else "-"


def report(cfg, questions, ctx, out):
    qcat = {x["id"]: x["cat"] for x in questions}
    ids = set(qcat)
    answers = {(r["model"], r["mode"], r["id"]): r for r in load_jsonl(out / "answers.jsonl") if not r.get("error") and r["id"] in ids}
    per = defaultdict(list)  # (model, id) -> judgement rows
    for r in load_jsonl(out / "judgements.jsonl"):
        if not r.get("error") and r["id"] in ids:
            per[(r["model"], r["id"])].append(r)
    L = [f"# ioBroker RAG: answers with and without RAG\n", f"{len(questions)} questions, judges: {', '.join(j['name'] for j in cfg['judges'])}. "
         "Score per answer = mean of the judges (0-2). Modes: A = no context, B = top-1 document without reranker, C = top-5 documents with reranker.\n"]

    L += ["## Retrieval\n", "| Ranking | Category | n | Hit@1 | Hit@5 | MRR | Median ms |", "|---|---|---|---|---|---|---|"]
    for name in ("plain", "rerank"):
        for cat in ("all", "api", "adapter", "troubleshooting"):
            rows = [ctx[x["id"]][name] for x in questions if cat in ("all", x["cat"])]
            ranks = [r["rank"] for r in rows]
            L.append(f"| {name} | {cat} | {len(rows)} | {sum(r == 0 for r in ranks)} | {sum(r is not None for r in ranks)} | "
                     f"{sum(1 / (r + 1) for r in ranks if r is not None) / len(rows):.2f} | {statistics.median(r['ms'] for r in rows):.0f} |")

    def stats(model, mode, cats=None):
        sc, inv, zero, full, secs = [], 0, 0, 0, []
        for x in questions:
            if cats and x["cat"] not in cats:
                continue
            js = per.get((model, x["id"]), [])
            if not js:
                continue
            s = statistics.mean(j["scores"][mode] for j in js)
            sc.append(s)
            zero += all(j["scores"][mode] == 0 for j in js)
            full += all(j["scores"][mode] == 2 for j in js)
            inv += any(j["invented"][mode] for j in js)
            if (model, mode, x["id"]) in answers:
                secs.append(answers[(model, mode, x["id"])]["seconds"])
        n = len(sc)
        return n, sum(sc), full, zero, inv, (statistics.median(secs) if secs else None)

    L += ["\n## Results per model\n", "Correct = score sum / maximum. Fully correct / wrong = all judges gave 2 / 0. Invented = at least one judge saw an invented API.\n",
          "| Tier | Model | Mode | n | Correct | Fully correct | Wrong (0) | Invented | Median s |", "|---|---|---|---|---|---|---|---|---|"]
    for m in cfg["models"]:
        for mode in MODES:
            n, s, full, zero, inv, sec = stats(m["name"], mode)
            if n:
                L.append(f"| {m['tier']} | {m['name']} | {mode} | {n} | {pct(s, 2 * n)} | {full} | {zero} | {inv} | {sec:.1f} |" if sec is not None
                         else f"| {m['tier']} | {m['name']} | {mode} | {n} | {pct(s, 2 * n)} | {full} | {zero} | {inv} | - |")

    L += ["\n## Per category (correct, A / B / C)\n", "| Model | API & syntax | Adapter | Troubleshooting |", "|---|---|---|---|"]
    for m in cfg["models"]:
        cells = []
        for cat in ("api", "adapter", "troubleshooting"):
            vals = [stats(m["name"], mode, {cat}) for mode in MODES]
            cells.append(" / ".join(pct(v[1], 2 * v[0]) for v in vals))
        L.append(f"| {m['name']} | " + " | ".join(cells) + " |")

    if len(cfg["judges"]) > 1:
        same = tot = 0
        for js in per.values():
            if len(js) > 1:
                for mode in MODES:
                    tot += 1
                    same += len({j["scores"][mode] for j in js}) == 1
        L.append(f"\nJudge agreement (identical score): {pct(same, tot)} of {tot} answers.")
    (out / "report.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("rag", help="RAG server, e.g. http://127.0.0.1:8321")
    ap.add_argument("--models", default=str(HERE / "models.example.json"))
    ap.add_argument("--questions", default=str(HERE / "answers-questions.jsonl"))
    ap.add_argument("--out", default=str(HERE / "answers-out"))
    ap.add_argument("--only", help="comma separated question ids")
    ap.add_argument("--limit", type=int, help="first N questions per category")
    ap.add_argument("--tiers", help="comma separated tiers to run")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--report-only", action="store_true")
    a = ap.parse_args()
    cfg = json.loads(Path(a.models).read_text())
    questions = load_jsonl(Path(a.questions))
    if a.only:
        questions = [x for x in questions if x["id"] in a.only.split(",")]
    if a.limit:
        seen = defaultdict(int)
        questions = [x for x in questions if (seen.__setitem__(x["cat"], seen[x["cat"]] + 1) or seen[x["cat"]] <= a.limit)]
    if a.tiers:
        cfg["models"] = [m for m in cfg["models"] if m["tier"] in a.tiers.split(",")]
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    ctx = retrieve(a.rag, questions, out)
    if not a.report_only:
        call = Caller(cfg["backends"])
        for spec in cfg["models"] + cfg["judges"]:
            call.calibrate(spec)
        if call.overhead:
            print("CLI overhead subtracted:", {k: round(v, 1) for k, v in call.overhead.items()}, flush=True)
        answer_all(call, cfg["models"], questions, ctx, out, a.workers)
        judge_all(call, cfg["judges"], questions, out, a.workers)
    report(cfg, questions, ctx, out)


if __name__ == "__main__":
    main()
