## Per model: correct (A / B / C), Δ C−A with 95 % bootstrap interval, invented A → C

| Vendor | Tier | Model | A | B | C | Δ C−A (points) | significant | invented A → C | median chars A |
|---|---|---|---|---|---|---|---|---|---|
| Anthropic | top | claude-opus-5.5 | 76 % | 81 % | 86 % | +10 (+5 … +16) | yes | 18 → 8 | 2040 |
| Anthropic | medium | claude-sonnet-5.5 | 64 % | 74 % | 83 % | +19 (+13 … +26) | yes | 25 → 13 | 1709 |
| Anthropic | light | claude-haiku-5.5 | 48 % | 61 % | 72 % | +24 (+16 … +31) | yes | 38 → 18 | 1629 |
| Google | top | gemini-4-argon | 62 % | 73 % | 84 % | +22 (+15 … +29) | yes | 30 → 10 | 1406 |
| Google | medium | gemini-3.8-flash | 54 % | 69 % | 79 % | +26 (+18 … +33) | yes | 32 → 10 | 1169 |
| OpenAI | top | gpt-6.1-sol | 69 % | 78 % | 84 % | +15 (+8 … +22) | yes | 17 → 6 | 813 |
| OpenAI | medium | gpt-6.1-terra | 67 % | 75 % | 81 % | +14 (+8 … +20) | yes | 8 → 7 | 642 |
| OpenAI | light | gpt-6-luna | 49 % | 65 % | 73 % | +23 (+15 … +31) | yes | 28 → 13 | 567 |
| local | local | gemma4-26b | 9 % | 37 % | 60 % | +51 (+44 … +58) | yes | 86 → 19 | 1618 |
| xAI | top | grok-4.6 | 52 % | 66 % | 82 % | +30 (+23 … +37) | yes | 36 → 10 | 742 |

## Per vendor (mean over its models)

| Vendor | A | B | C | invented A / B / C |
|---|---|---|---|---|
| Anthropic | 63 % | 72 % | 80 % | 26 % / 16 % / 12 % |
| OpenAI | 62 % | 72 % | 79 % | 17 % / 7 % / 8 % |
| Google | 58 % | 71 % | 82 % | 30 % / 17 % / 10 % |
| xAI | 52 % | 66 % | 82 % | 34 % / 17 % / 10 % |
| local | 9 % | 37 % | 60 % | 82 % / 49 % / 18 % |

## Judge bias: mean over all modes per judge

| Model | judge-claude-opus-5.5 | judge-gemini-4-argon | judge-gpt-6.1-sol | difference 1−2 |
|---|---|---|---|---|
| claude-haiku-5.5 | 62 % | 68 % | 51 % | -6 |
| claude-opus-5.5 | 83 % | 90 % | 71 % | -8 |
| claude-sonnet-5.5 | 75 % | 83 % | 63 % | -8 |
| gemini-3.8-flash | 68 % | 76 % | 58 % | -8 |
| gemini-4-argon | 73 % | 83 % | 62 % | -10 |
| gemma4-26b | 37 % | 40 % | 30 % | -3 |
| gpt-6-luna | 62 % | 65 % | 60 % | -4 |
| gpt-6.1-sol | 77 % | 81 % | 73 % | -4 |
| gpt-6.1-terra | 74 % | 79 % | 69 % | -5 |
| grok-4.6 | 67 % | 73 % | 60 % | -7 |

## Ranking per mode (correct)

- **A:** claude-opus-5.5 76 %, gpt-6.1-sol 69 %, gpt-6.1-terra 67 %, claude-sonnet-5.5 64 %, gemini-4-argon 62 %, gemini-3.8-flash 54 %, grok-4.6 52 %, gpt-6-luna 49 %, claude-haiku-5.5 48 %, gemma4-26b 9 %
- **B:** claude-opus-5.5 81 %, gpt-6.1-sol 78 %, gpt-6.1-terra 75 %, claude-sonnet-5.5 74 %, gemini-4-argon 73 %, gemini-3.8-flash 69 %, grok-4.6 66 %, gpt-6-luna 65 %, claude-haiku-5.5 61 %, gemma4-26b 37 %
- **C:** claude-opus-5.5 86 %, gpt-6.1-sol 84 %, gemini-4-argon 84 %, claude-sonnet-5.5 83 %, grok-4.6 82 %, gpt-6.1-terra 81 %, gemini-3.8-flash 79 %, gpt-6-luna 73 %, claude-haiku-5.5 72 %, gemma4-26b 60 %

## Retrieval hit vs. effect C−A (cloud models)

| Reranker gold rank in top 5 | questions | Δ C−A |
|---|---|---|
| rank 1 | 55 | +28 points |
| rank 2-5 | 38 | +16 points |
| not in top 5 | 12 | -2 points |
