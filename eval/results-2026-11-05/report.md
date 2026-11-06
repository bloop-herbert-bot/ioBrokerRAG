# ioBroker RAG: answers with and without RAG

105 questions, judges: judge-claude-opus-5.5, judge-gpt-6.1-sol, judge-gemini-4-argon. Score per answer = mean of the judges (0-2). Modes: A = no context, B = top-1 document without reranker, C = top-5 documents with reranker.

## Retrieval

| Ranking | Category | n | Hit@1 | Hit@5 | MRR | Median ms |
|---|---|---|---|---|---|---|
| plain | all | 105 | 55 | 91 | 0.66 | 202 |
| plain | api | 35 | 16 | 30 | 0.61 | 190 |
| plain | adapter | 35 | 19 | 33 | 0.72 | 186 |
| plain | troubleshooting | 35 | 20 | 28 | 0.65 | 220 |
| rerank | all | 105 | 55 | 93 | 0.66 | 3192 |
| rerank | api | 35 | 17 | 26 | 0.59 | 3197 |
| rerank | adapter | 35 | 22 | 34 | 0.74 | 3142 |
| rerank | troubleshooting | 35 | 16 | 33 | 0.63 | 3196 |

## Results per model

Correct = score sum / maximum. Fully correct / wrong = all judges gave 2 / 0. Invented = at least one judge saw an invented API.

| Tier | Model | Mode | n | Correct | Fully correct | Wrong (0) | Invented | Median s |
|---|---|---|---|---|---|---|---|---|
| top | claude-opus-5.5 | A | 105 | 76 % | 42 | 2 | 18 | 22.4 |
| top | claude-opus-5.5 | B | 105 | 81 % | 52 | 1 | 13 | 20.4 |
| top | claude-opus-5.5 | C | 105 | 86 % | 60 | 0 | 8 | 20.5 |
| top | gpt-6.1-sol | A | 105 | 69 % | 40 | 8 | 17 | 20.2 |
| top | gpt-6.1-sol | B | 105 | 78 % | 51 | 2 | 5 | 18.0 |
| top | gpt-6.1-sol | C | 105 | 84 % | 67 | 1 | 6 | 17.3 |
| top | gemini-4-argon | A | 105 | 62 % | 23 | 8 | 30 | 18.3 |
| top | gemini-4-argon | B | 105 | 73 % | 36 | 1 | 18 | 19.0 |
| top | gemini-4-argon | C | 105 | 84 % | 60 | 0 | 10 | 28.0 |
| top | grok-4.6 | A | 105 | 52 % | 18 | 16 | 36 | 35.7 |
| top | grok-4.6 | B | 105 | 66 % | 31 | 5 | 18 | 33.9 |
| top | grok-4.6 | C | 105 | 82 % | 56 | 0 | 10 | 30.9 |
| medium | claude-sonnet-5.5 | A | 105 | 64 % | 25 | 4 | 25 | 25.9 |
| medium | claude-sonnet-5.5 | B | 105 | 74 % | 42 | 1 | 18 | 25.3 |
| medium | claude-sonnet-5.5 | C | 105 | 83 % | 60 | 1 | 13 | 25.9 |
| medium | gpt-6.1-terra | A | 105 | 67 % | 36 | 5 | 8 | 27.3 |
| medium | gpt-6.1-terra | B | 105 | 75 % | 43 | 1 | 7 | 24.4 |
| medium | gpt-6.1-terra | C | 105 | 81 % | 54 | 0 | 7 | 18.4 |
| medium | gemini-3.8-flash | A | 105 | 54 % | 19 | 17 | 32 | 20.0 |
| medium | gemini-3.8-flash | B | 105 | 69 % | 32 | 4 | 17 | 18.9 |
| medium | gemini-3.8-flash | C | 105 | 79 % | 46 | 2 | 10 | 18.1 |
| light | claude-haiku-5.5 | A | 105 | 48 % | 16 | 19 | 38 | 18.1 |
| light | claude-haiku-5.5 | B | 105 | 61 % | 25 | 7 | 20 | 16.4 |
| light | claude-haiku-5.5 | C | 105 | 72 % | 39 | 4 | 18 | 15.6 |
| light | gpt-6-luna | A | 105 | 49 % | 18 | 19 | 28 | 22.5 |
| light | gpt-6-luna | B | 105 | 65 % | 34 | 7 | 10 | 14.1 |
| light | gpt-6-luna | C | 105 | 73 % | 42 | 5 | 13 | 16.8 |
| local | gemma4-26b | A | 105 | 9 % | 1 | 78 | 86 | 17.9 |
| local | gemma4-26b | B | 105 | 37 % | 15 | 37 | 51 | 16.9 |
| local | gemma4-26b | C | 105 | 60 % | 26 | 13 | 19 | 16.6 |

## Per category (correct, A / B / C)

| Model | API & syntax | Adapter | Troubleshooting |
|---|---|---|---|
| claude-opus-5.5 | 80 % / 81 % / 90 % | 73 % / 84 % / 80 % | 74 % / 79 % / 89 % |
| gpt-6.1-sol | 69 % / 80 % / 90 % | 70 % / 76 % / 83 % | 70 % / 77 % / 80 % |
| gemini-4-argon | 67 % / 77 % / 90 % | 59 % / 71 % / 80 % | 59 % / 72 % / 81 % |
| grok-4.6 | 60 % / 66 % / 87 % | 45 % / 66 % / 76 % | 52 % / 67 % / 84 % |
| claude-sonnet-5.5 | 67 % / 74 % / 86 % | 56 % / 72 % / 77 % | 69 % / 75 % / 86 % |
| gpt-6.1-terra | 69 % / 81 % / 84 % | 65 % / 68 % / 76 % | 68 % / 75 % / 83 % |
| gemini-3.8-flash | 54 % / 67 % / 84 % | 54 % / 70 % / 77 % | 53 % / 69 % / 77 % |
| claude-haiku-5.5 | 52 % / 66 % / 72 % | 37 % / 57 % / 70 % | 54 % / 60 % / 72 % |
| gpt-6-luna | 50 % / 72 % / 76 % | 46 % / 59 % / 69 % | 51 % / 63 % / 73 % |
| gemma4-26b | 7 % / 30 % / 60 % | 4 % / 39 % / 62 % | 17 % / 41 % / 60 % |

Judge agreement (identical score): 65 % of 3150 answers.
