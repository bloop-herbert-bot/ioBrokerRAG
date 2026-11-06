# ioBroker RAG: answers with and without RAG

45 questions, judges: judge-claude-opus-5.5, judge-gpt-6.1-sol, judge-gemini-4-argon. Score per answer = mean of the judges (0-2). Modes: A = no context, B = top-1 document without reranker, C = top-5 documents with reranker.

## Retrieval

| Ranking | Category | n | Hit@1 | Hit@5 | MRR | Median ms |
|---|---|---|---|---|---|---|
| plain | all | 45 | 33 | 43 | 0.84 | 363 |
| plain | api | 15 | 11 | 15 | 0.87 | 300 |
| plain | adapter | 15 | 11 | 15 | 0.85 | 340 |
| plain | troubleshooting | 15 | 11 | 13 | 0.79 | 858 |
| rerank | all | 45 | 25 | 44 | 0.71 | 3553 |
| rerank | api | 15 | 9 | 14 | 0.73 | 3230 |
| rerank | adapter | 15 | 9 | 15 | 0.72 | 3315 |
| rerank | troubleshooting | 15 | 7 | 15 | 0.68 | 6403 |

## Results per model

Correct = score sum / maximum. Fully correct / wrong = all judges gave 2 / 0. Invented = at least one judge saw an invented API.

| Tier | Model | Mode | n | Correct | Fully correct | Wrong (0) | Invented | Median s |
|---|---|---|---|---|---|---|---|---|
| top | claude-opus-5.5 | A | 45 | 67 % | 16 | 2 | 6 | 21.3 |
| top | claude-opus-5.5 | B | 45 | 82 % | 25 | 1 | 4 | 21.5 |
| top | claude-opus-5.5 | C | 45 | 89 % | 31 | 0 | 2 | 19.6 |
| top | gpt-6.1-sol | A | 45 | 54 % | 11 | 8 | 12 | 24.2 |
| top | gpt-6.1-sol | B | 45 | 80 % | 26 | 1 | 3 | 20.1 |
| top | gpt-6.1-sol | C | 45 | 87 % | 34 | 1 | 3 | 17.3 |
| top | gemini-4-argon | A | 45 | 48 % | 5 | 7 | 19 | 22.7 |
| top | gemini-4-argon | B | 45 | 73 % | 19 | 1 | 10 | 23.5 |
| top | gemini-4-argon | C | 45 | 86 % | 29 | 0 | 5 | 29.0 |
| top | grok-4.6 | A | 45 | 40 % | 2 | 11 | 21 | 42.7 |
| top | grok-4.6 | B | 45 | 70 % | 18 | 2 | 8 | 37.0 |
| top | grok-4.6 | C | 45 | 87 % | 29 | 0 | 6 | 32.1 |
| medium | claude-sonnet-5.5 | A | 45 | 47 % | 1 | 4 | 12 | 28.1 |
| medium | claude-sonnet-5.5 | B | 45 | 72 % | 18 | 1 | 10 | 24.0 |
| medium | claude-sonnet-5.5 | C | 45 | 82 % | 26 | 1 | 7 | 25.9 |
| medium | gpt-6.1-terra | A | 45 | 51 % | 8 | 5 | 4 | 29.7 |
| medium | gpt-6.1-terra | B | 45 | 76 % | 21 | 0 | 5 | 25.1 |
| medium | gpt-6.1-terra | C | 45 | 86 % | 29 | 0 | 2 | 15.8 |
| medium | gemini-3.8-flash | A | 45 | 34 % | 3 | 15 | 19 | 23.6 |
| medium | gemini-3.8-flash | B | 45 | 69 % | 17 | 3 | 8 | 26.9 |
| medium | gemini-3.8-flash | C | 45 | 82 % | 24 | 1 | 3 | 17.7 |
| light | claude-haiku-5.5 | A | 45 | 33 % | 1 | 12 | 15 | 18.8 |
| light | claude-haiku-5.5 | B | 45 | 62 % | 13 | 3 | 7 | 17.8 |
| light | claude-haiku-5.5 | C | 45 | 74 % | 20 | 2 | 6 | 16.5 |
| light | gpt-6-luna | A | 45 | 31 % | 2 | 17 | 16 | 29.9 |
| light | gpt-6-luna | B | 45 | 69 % | 20 | 3 | 4 | 15.5 |
| light | gpt-6-luna | C | 45 | 74 % | 23 | 2 | 8 | 15.3 |
| local | gemma4-26b | A | 45 | 3 % | 0 | 38 | 37 | 22.4 |
| local | gemma4-26b | B | 45 | 48 % | 13 | 13 | 17 | 21.6 |
| local | gemma4-26b | C | 45 | 67 % | 16 | 4 | 9 | 18.0 |

## Per category (correct, A / B / C)

| Model | API & syntax | Adapter | Troubleshooting |
|---|---|---|---|
| claude-opus-5.5 | 78 % / 78 % / 90 % | 70 % / 91 % / 86 % | 54 % / 77 % / 91 % |
| gpt-6.1-sol | 51 % / 76 % / 90 % | 62 % / 87 % / 84 % | 48 % / 79 % / 88 % |
| gemini-4-argon | 47 % / 72 % / 88 % | 51 % / 74 % / 82 % | 47 % / 72 % / 89 % |
| grok-4.6 | 42 % / 58 % / 89 % | 37 % / 80 % / 81 % | 41 % / 72 % / 92 % |
| claude-sonnet-5.5 | 50 % / 69 % / 83 % | 48 % / 80 % / 74 % | 43 % / 68 % / 88 % |
| gpt-6.1-terra | 43 % / 78 % / 82 % | 56 % / 73 % / 83 % | 56 % / 78 % / 92 % |
| gemini-3.8-flash | 24 % / 56 % / 77 % | 42 % / 80 % / 81 % | 36 % / 72 % / 88 % |
| claude-haiku-5.5 | 29 % / 53 % / 72 % | 40 % / 72 % / 68 % | 29 % / 61 % / 83 % |
| gpt-6-luna | 18 % / 73 % / 70 % | 38 % / 70 % / 71 % | 37 % / 62 % / 80 % |
| gemma4-26b | 1 % / 37 % / 61 % | 1 % / 51 % / 61 % | 8 % / 57 % / 78 % |

Judge agreement (identical score): 69 % of 1350 answers.
