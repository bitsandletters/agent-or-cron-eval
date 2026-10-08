# Cursor pilot results — primary comparison

**Study:** `runs/cursor-pilot` (`cursor-pilot-primary-comparison`)  
**Host:** Cursor `agent` CLI `2026.10.01-e373342` via Ultra subscription (`CURSOR_API_KEY`)  
**Date (UTC):** 2026-10-08  
**Split:** development · **Fixtures:** `dev-growth`, `dev-decline`, `dev-zero` · **Repeats:** 1  
**Arms:** primary 2×2 only (`tool_driven` / `saved_script` × `narrow` / `broad`) + deterministic baseline A  

## Catalog selectors used

| Target | Requested selector |
| --- | --- |
| Grok 4.7 | `grok-4.7-high` |
| Claude Sonnet 5.5 | `claude-sonnet-5-5-high` |
| Claude Haiku 5.5 | `claude-haiku-5-5-high` |
| Gemini 3.8 Flash | `gemini-3.8-flash-high` |

## Headline

- **51/51** planned runs finalized; **0** timeouts / quota errors / process failures
- Overall automated pass: **32/51 (62.7%)**
- Dominant effect: **saved_script (E) 24/24 pass** vs **tool_driven (C/D) 5/24 pass**
- Prompt breadth within tool-driven: narrow **2/12**, broad **3/12** (small sample; not a clear winner)
- Token/cost usage from Cursor stream-json: **unavailable** (expected per host docs); latency retained

## Pass rates by model × execution style

| Model | tool_driven | saved_script | overall |
| --- | --- | --- | --- |
| Claude Sonnet 5.5 | 2/6 | 6/6 | 8/12 |
| Gemini 3.8 Flash | 2/6 | 6/6 | 8/12 |
| Grok 4.7 | 1/6 | 6/6 | 7/12 |
| Claude Haiku 5.5 | 0/6 | 6/6 | 6/12 |
| Deterministic A | — | — | 3/3 |

## Latency (wall clock, median)

| Model | median | mean | range |
| --- | --- | --- | --- |
| Claude Haiku 5.5 | 22.9s | 25.2s | 14–43s |
| Claude Sonnet 5.5 | 21.8s | 27.9s | 12–74s |
| Grok 4.7 | 93.4s | 101.6s | 30–183s |
| Gemini 3.8 Flash | 109.1s | 142.7s | 42–268s |
| Deterministic A | 0.1s | 0.1s | — |

## Tool-driven failure modes

Failed tool-driven attempts almost always still produced a report; automated fails were scorer components:

- `unsupported_claims` (numeric prose without matching structured claims; occasional causal wording)
- `material_changes` (missed ≥10% WoW click/session findings)
- `evidence_support` (especially Haiku narrow)

Saved-script cells passed because agents invoked `saved-report` and kept A's fixed findings/template.

## Artifacts

- Plan / results: `runs/cursor-pilot/plan.json`, `results.jsonl`
- Aggregate: `runs/cursor-pilot/summary/aggregate.md`, `aggregate.json`
- Per-attempt packets, host stdout/stderr, scores under `runs/cursor-pilot/runs/`
- Config: `configs/cursor-pilot.json`

## Limits for the blog post

- Pilot only: 3 development fixtures, 1 repeat, not held-out
- Host routing is opaque; requested selector ≠ verified provider ID without attestation
- Automated scorer is not a semantic oracle; blinded human review still recommended
- Small N: treat model ranking within tool-driven as suggestive, not definitive

## Usage / spend follow-up

Token counters were present in retained `host.stdout.txt` but originally unparsed. See **`runs/cursor-pilot-costed/`** (and `COSTED_RESULTS.md`) for backfilled measured usage and API-equivalent spend. The original study directory is unchanged; after the harness/pricing manifest bump, use the costed sibling for `cronbench aggregate` / status.
