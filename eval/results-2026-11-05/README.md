# Answer benchmark, run of 2026-11-05

This directory holds the results of one full run of `eval/answers.py`, exactly as it ran.

## Setup

- **Questions:** `eval/answers-all.jsonl`, 105 questions. Field `set` tells the two sets apart:
  - `easy` (60, also in `eval/answers-questions.jsonl`): everyday topics.
  - `hard` (45, also in `eval/answers-hard.jsonl`): specific documented details, such as rare functions, exact option names, less common adapters and specific log messages.
  - Every question has 2–4 reference facts. Each fact is backed by a verbatim quote from the documentation or source code (`evidence`).
- **Models:** `eval/models.copilot.json`.
  - Nine cloud models from four vendors through a GitHub Copilot subscription, called with `openclaw infer model run`. The script checks on every call that the requested provider and model answered.
  - gemma4 26B (Q4) as a local reference model through Ollama, with `num_ctx` 16384.
  - Temperature and reasoning level are the Copilot defaults.
- **Modes:**
  - A = no context
  - B = top-1 document without reranker
  - C = top-5 documents with reranker
- **Judges:** Claude Opus 5.5, GPT-6.1-sol and Gemini 4 Argon. They grade the three answers of one model blind and in random order against the reference facts (0/1/2). The score is the mean of the judges.
- **RAG server:** The retrieval for all questions ran on 2026-11-05 between 15:00 and 15:10 and is cached in `retrieval.json.gz`.
  - At that time the server ran the index before 0.4.0. The index contained ioBroker.docs, js-controller, the javascript adapter and the core libraries, but no adapter repositories from the Latest repository.
  - The 0.4.0 index with all adapters went live later that day, at 19:09. It is not part of this run.

## Files

| File | Content |
|---|---|
| `report.md`, `report-easy.md`, `report-hard.md` | Standard report of `answers.py --report-only` for all questions and per set |
| `analysis-all.md`, `analysis-easy.md`, `analysis-hard.md` | `eval/analyze.py`: per vendor and model, bootstrap significance of C vs A, judge bias, effect by retrieval rank |
| `answers.jsonl.gz` | All answers: model, tier, mode, id, text, seconds. Rows with `error` were retried and are ignored by the report. |
| `judgements.jsonl.gz` | All judgements: judge, model, id, scores and invented per mode, short reason |
| `retrieval.json.gz` | Retrieved contexts (B, C) and gold ranks (plain, rerank) per question |

To rebuild the reports, unpack the three files into one directory and run:

    python3 eval/answers.py http://127.0.0.1:8321 --models eval/models.copilot.json --questions eval/answers-all.jsonl --out <dir> --report-only
    python3 eval/analyze.py <dir> eval/answers-all.jsonl

## Main results (correct, A → C)

| Model | easy | hard |
|---|---|---|
| Claude Opus 5.5 | 82 → 84 % | 67 → 89 % |
| GPT-6.1-sol | 81 → 82 % | 54 → 87 % |
| Grok 4.6 | 61 → 79 % | 40 → 87 % |
| Gemini 4 Argon | 72 → 82 % | 48 → 86 % |
| GPT-6.1-terra | 79 → 77 % | 51 → 86 % |
| Claude Sonnet 5.5 | 76 → 84 % | 47 → 82 % |
| Gemini 3.8 Flash | 68 → 78 % | 34 → 82 % |
| Claude Haiku 5.5 | 59 → 69 % | 33 → 74 % |
| GPT-6-luna | 63 → 72 % | 31 → 74 % |
| gemma4 26B (local) | 14 → 56 % | 3 → 67 % |

## Limitations

- The hard questions were written from the corpus, so the answer is always in the documentation. This is the favourable case for RAG.
- The judges differ in strictness by about 20 points, and all three give the same score on 61–69 % of the answers. The direction of the RAG effect is the same for every judge. The ranking among the top models is not reliable.
- There is one answer per model, question and mode.
- On some questions, gemma4 spent its whole turn thinking and returned no content. In that case `answers.py` retries once without thinking.
