# Retrieval check

`questions.jsonl` is the release gate. `questions-chat.jsonl` holds generalized questions derived from real ioBroker use; all names, addresses and private details were removed.

Both sets were written with an AI assistant. Do not use them as model training data.

    .venv/bin/python eval/run.py http://127.0.0.1:8321
    EVAL_FILE=eval/questions-chat.jsonl .venv/bin/python eval/run.py http://127.0.0.1:8321

# Answer check

`answers.py` measures what the retrieval is for: do models answer better with it? Each model answers a question file in three modes. There are two sets, each split into API & syntax, adapter specifics and troubleshooting:

- `answers-questions.jsonl` (default): 60 everyday questions
- `answers-hard.jsonl`: 45 questions on specific documented details
- `answers-all.jsonl`: both together, with a `set` field (`easy`/`hard`)

Every reference fact carries a verbatim quote from the documentation or source code in `evidence`.

The three modes:

- **A** no context
- **B** top-1 document, no reranker
- **C** top-5 documents with reranker

Judges grade the three answers of one model together, in random order, against human-checked reference facts (0 wrong or invented, 1 partly correct, 2 correct and usable). They do not see the retrieved context. Use judges from a different vendor than the tested models, or several judges; the report shows their agreement.

    cp eval/models.example.json my-models.json   # backends, models, judges
    python3 eval/answers.py http://127.0.0.1:8321 --models my-models.json --limit 1   # smoke run, 3 questions
    python3 eval/answers.py http://127.0.0.1:8321 --models my-models.json             # full run

Backends: `ollama` for the native Ollama API (sets `num_ctx`, default 16384; the `/v1` endpoint keeps the small default context and silently cuts the top-5 context), `openai` for any OpenAI-compatible endpoint (iobroker.ai-server, LiteLLM, cloud APIs; the key comes from the environment variable named in `api_key_env`) and `openclaw` for models reachable through the OpenClaw CLI, e.g. a GitHub Copilot subscription (`models.copilot.json`). The CLI starts a process per call; its fixed cost is measured once and subtracted, so latencies of that backend are approximate.

For a detailed analysis per vendor and model, with bootstrap significance of C vs A, judge bias and the effect by retrieval rank, run `python3 eval/analyze.py <out-dir> <questions.jsonl>`. The results of the run of 2026-11-05 (9 Copilot models from 4 vendors, gemma4 local, 3 judges, 105 questions) are in [`results-2026-11-05/`](results-2026-11-05/README.md).

Everything is cached in `--out` (default `eval/answers-out/`, not tracked). A second run only fetches what is missing, `--report-only` rebuilds `report.md`. Cloud runs cost requests: questions x 3 modes per model, plus one judgement per question, model and judge.

The questions and reference facts were written with an AI assistant and checked against the documentation, with a verbatim quote for every fact. Do not use them as training data.
