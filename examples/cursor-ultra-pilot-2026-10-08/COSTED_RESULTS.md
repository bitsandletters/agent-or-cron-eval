# Cursor pilot — usage backfill & API-equivalent spend

**Source study:** `runs/cursor-pilot` (immutable; scores/latency unchanged)  
**Costed study:** `runs/cursor-pilot-costed`  
**Method:** parse `host.stdout.txt` `type=result.usage` via new Cursor adapter; map stream display names → pricing IDs; re-aggregate with `pricing/prices.json` v2026-10-08.2  

## Measurement recovery

| Field | Before | After backfill |
| --- | --- | --- |
| Model-run usage provenance | unavailable (48) | **measured (48)** |
| Token counters | null | input / output / cache read / write |
| API-equivalent cost | unknown | **complete for 51/51** attempts |
| Latency / pass rates | unchanged | unchanged |

Display → pricing ID (operator-attested for this pilot):

- `Grok 4.7 256K High` → `grok-4.7`
- `Claude Sonnet 5.5 300K High` → `claude-sonnet-5-5`
- `Claude Haiku 5.5 300K High No Thinking` → `claude-haiku-5-5`
- `Gemini 3.8 Flash High` → `gemini-3.8-flash`

## Spend (API-equivalent USD, not Ultra invoices)

All figures are conditional list-price estimates. Cursor Ultra pool drawdown is not modeled. Long-context surcharge regimes are **not** auto-selected from token totals.

Mean per attempt. **Input** is canonical (uncached + cache read + cache write).

| Model | Style | Input | Output | $/attempt |
| --- | --- | ---: | ---: | ---: |
| Claude Haiku 5.5 | saved_script | 157,513 | 1,520 | $0.0056 |
| Claude Haiku 5.5 | tool_driven | 293,502 | 6,064 | $0.0109 |
| Claude Sonnet 5.5 | saved_script | 109,791 | 1,066 | $0.0673 |
| Claude Sonnet 5.5 | tool_driven | 231,759 | 4,500 | $0.1386 |
| Gemini 3.8 Flash | saved_script | 271,804 | 2,960 | $0.0774 |
| Gemini 3.8 Flash | tool_driven | 771,356 | 26,480 | $0.2335 |
| Grok 4.7 | saved_script | 149,248 | 1,780 | $0.1780 |
| Grok 4.7 | tool_driven | 353,387 | 12,246 | $0.3883 |

Across models:

| Style | Pass | Mean $/attempt | Sum $ |
| --- | --- | --- | --- |
| saved_script | 24/24 | $0.082 | $1.97 |
| tool_driven | 5/24 | $0.193 | $4.63 |

- All 48 Cursor attempts: **~$6.60** API-equivalent sum  
- Aggregate cost per passing report (includes failing attempts in numerator): **~$0.21**

## Interpretation for the post

Tool-driven is both **less reliable** and **~2.3× more expensive** per attempt than saved-script on this pilot. Haiku is cheapest; Grok is most expensive at these list rates (and Grok draws from the separate Cursor Models pool on Ultra—still not the same as this API-equivalent column).

## How to reproduce

```sh
python3 cronbench verify
python3 scripts/backfill_cursor_usage.py \
  --source runs/cursor-pilot \
  --out runs/cursor-pilot-costed
python3 cronbench aggregate --study runs/cursor-pilot-costed
```

Future Cursor command runs pick up usage automatically via the updated `parse_usage_artifact` Cursor adapter.
