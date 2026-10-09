# Summary tables

Means over n=6 development-fixture attempts per cell unless noted.

## Pass rate, latency, tokens, API-equivalent cost

| Model | Style | Pass | Latency median (s) | Input mean | Output mean | $/attempt mean |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Claude Haiku 5.5 | saved_script | 6/6 | 17.5 | 157,513 | 1,520 | $0.0056 |
| Claude Haiku 5.5 | tool_driven | 0/6 | 31.5 | 293,502 | 6,064 | $0.0109 |
| Claude Sonnet 5.5 | saved_script | 6/6 | 13.4 | 109,791 | 1,066 | $0.0673 |
| Claude Sonnet 5.5 | tool_driven | 2/6 | 36.7 | 231,759 | 4,500 | $0.1386 |
| Gemini 3.8 Flash | saved_script | 6/6 | 55.7 | 271,804 | 2,960 | $0.0774 |
| Gemini 3.8 Flash | tool_driven | 2/6 | 245.4 | 771,356 | 26,480 | $0.2335 |
| Grok 4.7 | saved_script | 6/6 | 37.8 | 149,248 | 1,780 | $0.1780 |
| Grok 4.7 | tool_driven | 1/6 | 173.3 | 353,387 | 12,246 | $0.3883 |
