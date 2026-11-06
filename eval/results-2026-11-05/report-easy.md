# ioBroker RAG: answers with and without RAG

60 questions, judges: judge-claude-opus-5.5, judge-gpt-6.1-sol, judge-gemini-4-argon. Score per answer = mean of the judges (0-2). Modes: A = no context, B = top-1 document without reranker, C = top-5 documents with reranker.

## Retrieval

| Ranking | Category | n | Hit@1 | Hit@5 | MRR | Median ms |
|---|---|---|---|---|---|---|
| plain | all | 60 | 22 | 48 | 0.53 | 161 |
| plain | api | 20 | 5 | 15 | 0.42 | 156 |
| plain | adapter | 20 | 8 | 18 | 0.62 | 159 |
| plain | troubleshooting | 20 | 9 | 15 | 0.55 | 176 |
| rerank | all | 60 | 30 | 49 | 0.61 | 3095 |
| rerank | api | 20 | 8 | 12 | 0.49 | 3146 |
| rerank | adapter | 20 | 13 | 19 | 0.76 | 3050 |
| rerank | troubleshooting | 20 | 9 | 18 | 0.60 | 3092 |

## Results per model

Correct = score sum / maximum. Fully correct / wrong = all judges gave 2 / 0. Invented = at least one judge saw an invented API.

| Tier | Model | Mode | n | Correct | Fully correct | Wrong (0) | Invented | Median s |
|---|---|---|---|---|---|---|---|---|
| top | claude-opus-5.5 | A | 60 | 83 % | 26 | 0 | 12 | 23.9 |
| top | claude-opus-5.5 | B | 60 | 81 % | 27 | 0 | 9 | 19.9 |
| top | claude-opus-5.5 | C | 60 | 84 % | 29 | 0 | 6 | 20.8 |
| top | gpt-6.1-sol | A | 60 | 81 % | 29 | 0 | 5 | 17.6 |
| top | gpt-6.1-sol | B | 60 | 76 % | 25 | 1 | 2 | 16.9 |
| top | gpt-6.1-sol | C | 60 | 82 % | 33 | 0 | 3 | 17.1 |
| top | gemini-4-argon | A | 60 | 72 % | 18 | 1 | 11 | 15.8 |
| top | gemini-4-argon | B | 60 | 74 % | 17 | 0 | 8 | 15.3 |
| top | gemini-4-argon | C | 60 | 82 % | 31 | 0 | 5 | 26.3 |
| top | grok-4.6 | A | 60 | 61 % | 16 | 5 | 15 | 32.5 |
| top | grok-4.6 | B | 60 | 63 % | 13 | 3 | 10 | 33.0 |
| top | grok-4.6 | C | 60 | 79 % | 27 | 0 | 4 | 29.2 |
| medium | claude-sonnet-5.5 | A | 60 | 76 % | 24 | 0 | 13 | 25.0 |
| medium | claude-sonnet-5.5 | B | 60 | 75 % | 24 | 0 | 8 | 26.4 |
| medium | claude-sonnet-5.5 | C | 60 | 84 % | 34 | 0 | 6 | 26.1 |
| medium | gpt-6.1-terra | A | 60 | 79 % | 28 | 0 | 4 | 25.8 |
| medium | gpt-6.1-terra | B | 60 | 73 % | 22 | 1 | 2 | 23.6 |
| medium | gpt-6.1-terra | C | 60 | 77 % | 25 | 0 | 5 | 21.2 |
| medium | gemini-3.8-flash | A | 60 | 68 % | 16 | 2 | 13 | 19.5 |
| medium | gemini-3.8-flash | B | 60 | 68 % | 15 | 1 | 9 | 17.0 |
| medium | gemini-3.8-flash | C | 60 | 78 % | 22 | 1 | 7 | 18.4 |
| light | claude-haiku-5.5 | A | 60 | 59 % | 15 | 7 | 23 | 17.4 |
| light | claude-haiku-5.5 | B | 60 | 60 % | 12 | 4 | 13 | 15.5 |
| light | claude-haiku-5.5 | C | 60 | 69 % | 19 | 2 | 12 | 14.8 |
| light | gpt-6-luna | A | 60 | 63 % | 16 | 2 | 12 | 17.8 |
| light | gpt-6-luna | B | 60 | 62 % | 14 | 4 | 6 | 12.8 |
| light | gpt-6-luna | C | 60 | 72 % | 19 | 3 | 5 | 17.0 |
| local | gemma4-26b | A | 60 | 14 % | 1 | 40 | 49 | 15.8 |
| local | gemma4-26b | B | 60 | 28 % | 2 | 24 | 34 | 14.3 |
| local | gemma4-26b | C | 60 | 56 % | 10 | 9 | 10 | 15.9 |

## Per category (correct, A / B / C)

| Model | API & syntax | Adapter | Troubleshooting |
|---|---|---|---|
| claude-opus-5.5 | 83 % / 84 % / 89 % | 76 % / 78 % / 76 % | 89 % / 80 % / 88 % |
| gpt-6.1-sol | 82 % / 84 % / 89 % | 76 % / 68 % / 82 % | 86 % / 75 % / 75 % |
| gemini-4-argon | 82 % / 80 % / 91 % | 65 % / 68 % / 79 % | 68 % / 72 % / 75 % |
| grok-4.6 | 72 % / 72 % / 86 % | 51 % / 56 % / 72 % | 60 % / 62 % / 78 % |
| claude-sonnet-5.5 | 79 % / 78 % / 88 % | 62 % / 67 % / 79 % | 88 % / 81 % / 84 % |
| gpt-6.1-terra | 88 % / 83 % / 85 % | 72 % / 63 % / 70 % | 78 % / 73 % / 77 % |
| gemini-3.8-flash | 76 % / 75 % / 89 % | 62 % / 62 % / 74 % | 67 % / 67 % / 69 % |
| claude-haiku-5.5 | 70 % / 76 % / 73 % | 34 % / 46 % / 72 % | 73 % / 59 % / 64 % |
| gpt-6-luna | 75 % / 71 % / 80 % | 52 % / 51 % / 68 % | 62 % / 63 % / 68 % |
| gemma4-26b | 11 % / 25 % / 59 % | 7 % / 30 % / 62 % | 23 % / 29 % / 46 % |

Judge agreement (identical score): 61 % of 1800 answers.
