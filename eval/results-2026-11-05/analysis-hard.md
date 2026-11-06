## Per model: correct (A / B / C), Δ C−A with 95 % bootstrap interval, invented A → C

| Vendor | Tier | Model | A | B | C | Δ C−A (points) | significant | invented A → C | median chars A |
|---|---|---|---|---|---|---|---|---|---|
| Anthropic | top | claude-opus-5.5 | 67 % | 82 % | 89 % | +21 (+12 … +31) | yes | 6 → 2 | 2260 |
| Anthropic | medium | claude-sonnet-5.5 | 47 % | 72 % | 82 % | +35 (+24 … +45) | yes | 12 → 7 | 1880 |
| Anthropic | light | claude-haiku-5.5 | 33 % | 62 % | 74 % | +42 (+31 … +52) | yes | 15 → 6 | 1791 |
| Google | top | gemini-4-argon | 48 % | 73 % | 86 % | +38 (+27 … +49) | yes | 19 → 5 | 1511 |
| Google | medium | gemini-3.8-flash | 34 % | 69 % | 82 % | +48 (+37 … +58) | yes | 19 → 3 | 1378 |
| OpenAI | top | gpt-6.1-sol | 54 % | 80 % | 87 % | +34 (+21 … +46) | yes | 12 → 3 | 900 |
| OpenAI | medium | gpt-6.1-terra | 51 % | 76 % | 86 % | +34 (+25 … +44) | yes | 4 → 2 | 785 |
| OpenAI | light | gpt-6-luna | 31 % | 69 % | 74 % | +43 (+31 … +54) | yes | 16 → 8 | 700 |
| local | local | gemma4-26b | 3 % | 48 % | 67 % | +63 (+53 … +73) | yes | 37 → 9 | 1834 |
| xAI | top | grok-4.6 | 40 % | 70 % | 87 % | +47 (+38 … +57) | yes | 21 → 6 | 920 |

## Per vendor (mean over its models)

| Vendor | A | B | C | invented A / B / C |
|---|---|---|---|---|
| Anthropic | 49 % | 72 % | 82 % | 24 % / 16 % / 11 % |
| OpenAI | 45 % | 75 % | 82 % | 24 % / 9 % / 10 % |
| Google | 41 % | 71 % | 84 % | 42 % / 20 % / 9 % |
| xAI | 40 % | 70 % | 87 % | 47 % / 18 % / 13 % |
| local | 3 % | 48 % | 67 % | 82 % / 38 % / 20 % |

## Judge bias: mean over all modes per judge

| Model | judge-claude-opus-5.5 | judge-gemini-4-argon | judge-gpt-6.1-sol | difference 1−2 |
|---|---|---|---|---|
| claude-haiku-5.5 | 60 % | 61 % | 48 % | -0 |
| claude-opus-5.5 | 79 % | 86 % | 73 % | -7 |
| claude-sonnet-5.5 | 68 % | 77 % | 57 % | -9 |
| gemini-3.8-flash | 64 % | 67 % | 55 % | -3 |
| gemini-4-argon | 71 % | 78 % | 59 % | -7 |
| gemma4-26b | 41 % | 43 % | 34 % | -1 |
| gpt-6-luna | 58 % | 60 % | 54 % | -2 |
| gpt-6.1-sol | 75 % | 76 % | 71 % | -1 |
| gpt-6.1-terra | 72 % | 75 % | 67 % | -3 |
| grok-4.6 | 67 % | 71 % | 59 % | -4 |

## Ranking per mode (correct)

- **A:** claude-opus-5.5 67 %, gpt-6.1-sol 54 %, gpt-6.1-terra 51 %, gemini-4-argon 48 %, claude-sonnet-5.5 47 %, grok-4.6 40 %, gemini-3.8-flash 34 %, claude-haiku-5.5 33 %, gpt-6-luna 31 %, gemma4-26b 3 %
- **B:** claude-opus-5.5 82 %, gpt-6.1-sol 80 %, gpt-6.1-terra 76 %, gemini-4-argon 73 %, claude-sonnet-5.5 72 %, grok-4.6 70 %, gemini-3.8-flash 69 %, gpt-6-luna 69 %, claude-haiku-5.5 62 %, gemma4-26b 48 %
- **C:** claude-opus-5.5 89 %, gpt-6.1-sol 87 %, grok-4.6 87 %, gemini-4-argon 86 %, gpt-6.1-terra 86 %, claude-sonnet-5.5 82 %, gemini-3.8-flash 82 %, claude-haiku-5.5 74 %, gpt-6-luna 74 %, gemma4-26b 67 %

## Retrieval hit vs. effect C−A (cloud models)

| Reranker gold rank in top 5 | questions | Δ C−A |
|---|---|---|
| rank 1 | 25 | +46 points |
| rank 2-5 | 19 | +30 points |
| not in top 5 | 1 | -2 points |
