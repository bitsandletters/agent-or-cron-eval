# Examples

## Real host pilot (limited rigor)

- [`cursor-ultra-pilot-2026-10-08/`](cursor-ultra-pilot-2026-10-08/) publishes scrubbed results from a **real Cursor Ultra / `agent` CLI pilot** (51 attempts: primary 2×2 × four models × three development fixtures + baseline). Read that directory’s README for design, caveats, and file map. It is intended for blog readers who want underlying numbers; it is **not** a held-out confirmatory study and does **not** claim a winner.

## Synthetic examples only

The remaining files demonstrate formats and accounting. They are **not real model evaluations** and establish no model ranking, real quota capacity, or subscription cost.

- `synthetic-offline/results.jsonl` contains seven development-fixture attempts: one deterministic baseline and six mock factor cells, all for `dev-growth`, repeat 1. Corresponding JSON/Markdown reports are under `reports/`. Model usage is explicitly synthetic/estimated; actual model IDs remain null.
- `synthetic-offline/aggregate.json` and `.md` aggregate only those seven rows, not the full local verification matrix. Durations are measured harness execution time on one machine, not model latency.
- `synthetic-failures/results.jsonl` retains six attempts across four planned runs: synthetic quota exhaustion followed by success, intentionally incorrect output repeated on retry, and missing-usage outputs at both prompt breadths. Failure and retry rows remain visible. Its aggregates retain unknown usage/cost rather than treating it as zero.

Generate your own full offline matrix using `configs/offline.json`. The failure demonstration is reproducible with:

```sh
python3 cronbench plan --config configs/failure-demo.json --out runs/failures
python3 cronbench run --study runs/failures
python3 cronbench run --study runs/failures --retry-failed
python3 cronbench aggregate --study runs/failures
```

Raw host transcripts, private review mappings, user data, and local personal paths are deliberately absent from these shared examples. Artifact checksums in example rows refer to the original local synthetic attempts; the subset is an illustration, not a complete retained study directory.
