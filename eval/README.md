# Retrieval check

`questions.jsonl` is the release gate. `questions-chat.jsonl` holds generalized questions derived from real ioBroker use; all names, addresses and private details were removed.

Both sets were written with an AI assistant. Do not use them as model training data.

    .venv/bin/python eval/run.py http://127.0.0.1:8321
    EVAL_FILE=eval/questions-chat.jsonl .venv/bin/python eval/run.py http://127.0.0.1:8321
