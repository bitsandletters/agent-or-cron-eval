# Cursor Ultra pilot (2026-10-08) — real host runs, limited rigor

This directory publishes **retained results from a real Cursor `agent` CLI pilot**, not the synthetic offline mocks.

It is useful for readers of the accompanying blog post who want the underlying numbers. It is **not** a confirmatory held-out study.

## What was run

- **Host:** Cursor `agent` CLI `2026.10.01-e373342` on a Cloud Agent VM, authenticated with a Cursor user API key (Ultra plan).
- **Models (catalog selectors):** `grok-4.7-high`, `claude-sonnet-5-5-high`, `claude-haiku-5-5-high`, `gemini-3.8-flash-high`.
- **Design:** primary 2×2 only — `tool_driven` / `saved_script` × `narrow` / `broad` — plus deterministic baseline A.
- **Fixtures:** development `dev-growth`, `dev-decline`, `dev-zero` (not held-out).
- **Repeats:** 1 per cell → 48 model attempts + 3 baseline = 51 planned/finalized.
- **Config:** `config.json` (same factors as `configs/cursor-pilot.json`).

## Caveats (please keep these in any write-up)

1. **Pilot / development split only** — not held-out; not five repeats; not multiple hosts.
2. **Small N** — n=6 per model×style cell; model rankings inside tool-driven are suggestive.
3. **Host confounds** — Cursor system prompts, tools, routing, and caches differ from Codex/Amp; the unit is host+model+config+arm.
4. **Costs are API-equivalent list prices**, not Ultra subscription charges or pool drawdown. Long-context surcharge regimes were not auto-selected from token totals.
5. **Usage was backfilled** from retained `type=result.usage` in host transcripts after a Cursor adapter landed; display names were operator-mapped to pricing IDs.
6. **Raw host transcripts are not published** (account/path risk). Published rows keep scores, usage, latency, and report files.
7. **Automated scoring is not a semantic oracle**; no blinded human review is included here.
8. Packet isolation was the usual directory boundary, not a hard OS sandbox.

## Files

| Path | Contents |
| --- | --- |
| `results.jsonl` | 51 scrubbed attempt records (usage, scores, latency) |
| `aggregate.json` / `aggregate.md` | Harness aggregate over those rows |
| `tables/summary.md` | Compact pass / latency / token / $ table |
| `reports/<run_id>/` | `report.json`, `report.md`, and `meta.json` per attempt |
| `config.json` / `plan.json` | Pilot configuration and frozen plan metadata |

## Reproduce analysis (offline)

```sh
python3 -c "import json; rows=[json.loads(l) for l in open('examples/cursor-ultra-pilot-2026-10-08/results.jsonl')]; print(len(rows), 'rows')"
```

Re-running the live host suite requires your own Cursor subscription auth, the `configs/cursor-pilot.json` factors, and accepting quota/cost on your account. Do not add provider BYOK to force completion.

## Related harness changes in this commit

- Cursor usage parser for `result.usage` camelCase counters
- Pricing rows for `claude-haiku-5-5` and `gemini-3.8-flash`
- `scripts/backfill_cursor_usage.py` for rebuilding costed studies from retained stdout
