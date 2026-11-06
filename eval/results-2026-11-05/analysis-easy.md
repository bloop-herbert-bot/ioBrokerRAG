## Per model: correct (A / B / C), Δ C−A with 95 % bootstrap interval, invented A → C

| Vendor | Tier | Model | A | B | C | Δ C−A (points) | significant | invented A → C | median chars A |
|---|---|---|---|---|---|---|---|---|---|
| Anthropic | top | claude-opus-5.5 | 82 % | 81 % | 84 % | +2 (-4 … +8) | no | 12 → 6 | 1937 |
| Anthropic | medium | claude-sonnet-5.5 | 76 % | 75 % | 84 % | +7 (+0 … +14) | yes | 13 → 6 | 1626 |
| Anthropic | light | claude-haiku-5.5 | 59 % | 60 % | 69 % | +10 (+1 … +20) | yes | 23 → 12 | 1411 |
| Google | top | gemini-4-argon | 72 % | 74 % | 82 % | +10 (+3 … +16) | yes | 11 → 5 | 1298 |
| Google | medium | gemini-3.8-flash | 68 % | 68 % | 78 % | +9 (+1 … +17) | yes | 13 → 7 | 1025 |
| OpenAI | top | gpt-6.1-sol | 81 % | 76 % | 82 % | +1 (-6 … +7) | no | 5 → 3 | 726 |
| OpenAI | medium | gpt-6.1-terra | 79 % | 73 % | 77 % | -2 (-8 … +5) | no | 4 → 5 | 594 |
| OpenAI | light | gpt-6-luna | 63 % | 62 % | 72 % | +9 (-1 … +18) | no | 12 → 5 | 503 |
| local | local | gemma4-26b | 14 % | 28 % | 56 % | +42 (+33 … +51) | yes | 49 → 10 | 1520 |
| xAI | top | grok-4.6 | 61 % | 63 % | 79 % | +18 (+9 … +26) | yes | 15 → 4 | 588 |

## Per vendor (mean over its models)

| Vendor | A | B | C | invented A / B / C |
|---|---|---|---|---|
| Anthropic | 73 % | 72 % | 79 % | 27 % / 17 % / 13 % |
| OpenAI | 74 % | 70 % | 77 % | 12 % / 6 % / 7 % |
| Google | 70 % | 71 % | 80 % | 20 % / 14 % / 10 % |
| xAI | 61 % | 63 % | 79 % | 25 % / 17 % / 7 % |
| local | 14 % | 28 % | 56 % | 82 % / 57 % / 17 % |

## Judge bias: mean over all modes per judge

| Model | judge-claude-opus-5.5 | judge-gemini-4-argon | judge-gpt-6.1-sol | difference 1−2 |
|---|---|---|---|---|
| claude-haiku-5.5 | 63 % | 73 % | 53 % | -10 |
| claude-opus-5.5 | 85 % | 93 % | 69 % | -8 |
| claude-sonnet-5.5 | 80 % | 88 % | 68 % | -7 |
| gemini-3.8-flash | 71 % | 83 % | 61 % | -12 |
| gemini-4-argon | 75 % | 87 % | 65 % | -12 |
| gemma4-26b | 34 % | 37 % | 27 % | -3 |
| gpt-6-luna | 64 % | 69 % | 63 % | -5 |
| gpt-6.1-sol | 79 % | 85 % | 75 % | -6 |
| gpt-6.1-terra | 76 % | 82 % | 71 % | -7 |
| grok-4.6 | 67 % | 75 % | 61 % | -8 |

## Ranking per mode (correct)

- **A:** claude-opus-5.5 82 %, gpt-6.1-sol 81 %, gpt-6.1-terra 79 %, claude-sonnet-5.5 76 %, gemini-4-argon 72 %, gemini-3.8-flash 68 %, gpt-6-luna 63 %, grok-4.6 61 %, claude-haiku-5.5 59 %, gemma4-26b 14 %
- **B:** claude-opus-5.5 81 %, gpt-6.1-sol 76 %, claude-sonnet-5.5 75 %, gemini-4-argon 74 %, gpt-6.1-terra 73 %, gemini-3.8-flash 68 %, grok-4.6 63 %, gpt-6-luna 62 %, claude-haiku-5.5 60 %, gemma4-26b 28 %
- **C:** claude-opus-5.5 84 %, claude-sonnet-5.5 84 %, gpt-6.1-sol 82 %, gemini-4-argon 82 %, grok-4.6 79 %, gemini-3.8-flash 78 %, gpt-6.1-terra 77 %, gpt-6-luna 72 %, claude-haiku-5.5 69 %, gemma4-26b 56 %

## Retrieval hit vs. effect C−A (cloud models)

| Reranker gold rank in top 5 | questions | Δ C−A |
|---|---|---|
| rank 1 | 30 | +13 points |
| rank 2-5 | 19 | +3 points |
| not in top 5 | 11 | -2 points |
