# Contributing

- **New source:** add it to `sources.json`. Only public repositories with an MIT, Apache 2.0 or BSD license. `tools/check_sources.py` must pass.
- **Test questions:** add them to `eval/questions.jsonl`. Write them yourself. Do not copy forum posts or private data.
- **Code:** run `pytest`, keep changes small, explain the reason in the pull request.
- **Sign-off:** contributions are MIT licensed. Sign your commits with `git commit -s` ([Developer Certificate of Origin](https://developercertificate.org/)).
- **Measure it:** changes to chunking or ranking need the result of `eval/run.py` before and after.

Text from AI services may not be allowed as model training data. Mark such questions in the pull request.
