# OpenAI models in Amp: development pilot, 2026-10-08

> AI-generated study report, prepared by Amp from retained evaluation records and exported host transcripts. Human usefulness/clarity review has not been completed.

## Main finding

Moving the reporting work into the supplied deterministic script eliminated automated report failures in this pilot and reduced model-generated tokens and conditional API-equivalent cost. Tool-driven agents produced correct KPI data but sometimes omitted the scorer's expected narrative finding. Some official failures were keyword-scoring false positives. These results compare host/model configurations, not model intelligence in isolation.

All **78 planned runs completed**, with no whole-run retries or execution failures. Official automated passes were **61/78**: deterministic baseline 6/6, saved-script runs 36/36, and tool-driven runs 19/36. All 78 passed schema, KPI arithmetic, missing-data handling, and canonical Markdown checks. All saved-script JSON reports matched the corresponding deterministic baseline report exactly.

## Design and provenance

- Six synthetic development fixtures: growth, decline, quiet, zero baseline, incomplete coverage, and recoverable source failure. One run per fixture in each cell; no held-out evaluation or repeated trials.
- Three configurations crossed narrow/broad prompts with tool-driven/saved-script execution: 72 model runs plus six deterministic baselines. Prepared-evidence Arm B was not included.
- Sol: `gpt-6.1-sol`, Amp `gpt61s`, high effort, Amp High behavior. Astra: `gpt-6-astra`, Amp `astra`, medium effort, Amp Medium behavior. Luna: `gpt-6-luna`, Amp `gpt6l`, medium effort, Amp Low behavior. Features were empty for all three. Exported assistant usage model IDs matched requested models.
- Each model attempt used a fresh, separate no-project Amp orb containing only its exported packet. Global user instructions and workspace plugins/skills could be inherited. The first eight bootstrap prompts differed slightly; assigned benchmark prompts were unchanged.
- Existing ChatGPT subscription access was verified. No API keys, provider calls, or billing fallbacks were added. Per-request billing receipts and supporting-system routing/usage were unavailable.
- Study ID: `b076a373e8144ef6c0bc`; seed: `20261008`.
- Benchmark revision: [`b5baeb5`](https://github.com/bitsandletters/agent-or-cron-eval/commit/b5baeb51dcebcc3c1cc2edb901863a0fb17e3297).
- Manifest SHA256: `4f1a6ef761dde69b7af4eee63b498b6b4559005aa320cc8dd6afee4098910c82`.
- Pricing file SHA256: `ab167cafd796eb8243625ee132ddc1710fbae54f6dabdf7f7eb36c321878c3b6`.
- Fixtures, prompts, runtime, pricing, and frozen scoring were not modified. Offline verification passed 88 tests and verified all 34 manifest files.

## Official automated results

Each model cell contains six fixture runs. A pass means all required deterministic scoring checks passed for that run; it is not LLM-judge approval. There was no LLM judge.

| Configuration | Narrow tools (C) | Broad tools (D) | Narrow script (E) | Broad script (E) |
| --- | ---: | ---: | ---: | ---: |
| Sol / Amp High | 3/6 | 4/6 | 6/6 | 6/6 |
| Astra / Amp Medium | 4/6 | 4/6 | 6/6 | 6/6 |
| Luna / Amp Low | 4/6 | 0/6 | 6/6 | 6/6 |

The deterministic baseline passed 6/6 with median local wall time 0.115 seconds and zero runtime LLM tokens.

### What the 17 failures mean

The failures fall into three disjoint categories:

1. **Seven causal-keyword false positives.** Manual transcript/report inspection found negated attribution (such as “not … caused”) or arithmetic explanation (“because baseline was zero”), rather than unsupported causal claims. Official scores remain unchanged.
2. **Nine missing required PostHog sessions narrative findings.** All six tool-driven growth runs and all three broad-tool decline runs omitted the scorer-required sessions finding. The correct sessions data remained in the KPI tables; the agents selected other analyses. This is an expected-analysis coverage failure, not missing numeric data, and does not by itself establish poor human usefulness.
3. **One Luna broad/retry finding claim failure.** A position finding lacked its required `wow_pct` claim and used a positive 0.7 magnitude while the structured claim was −0.7 absolute change.

Discounting **only** the seven manually audited causal false positives gives this sensitivity analysis, not an official rescore:

| Configuration | Narrow tools | Broad tools |
| --- | ---: | ---: |
| Sol | 5/6 | 4/6 |
| Astra | 5/6 | 4/6 |
| Luna | 5/6 | 3/6 |

Thus “5/6” means five fixture runs would satisfy the remaining deterministic requirements under that adjustment. The sixth narrow Luna run contained correct data and analysis, but not the expected sessions analysis.

Six Luna runs also sent administrative completion messages to the controller despite the packet's no-messaging instruction: three tool runs and three script runs. This was an unscored side effect, not a customer message.

## Time, tokens, and cost

The fixture fetches read local JSON. **There was no simulated API/network wall time, sleep, or retry backoff** in the source tools; the recoverable source failure was immediate. Model-run wall time includes orb provisioning, packet transfer/wait, task execution, and packaging. It is not isolated inference latency and is not directly comparable to baseline compute time alone.

The following values pool narrow and broad within each execution style (12 runs per model/style). Reductions compare pooled medians, not medians of per-fixture reductions.

| Configuration | Script median wall seconds | Script median output tokens | Script vs tools median API-equivalent cost reduction |
| --- | ---: | ---: | ---: |
| Sol | 118.26 | 2,033 | 45.53% |
| Astra | 87.35 | 890 | 36.91% |
| Luna | 81.34 | 1,308.5 | 44.34% |

Mean-cost reductions were 44.31%, 33.98%, and 43.69%, respectively. Per-treatment timings, input/output tokens, and conditional costs appear in `summary.json`; all individual measurements appear in `results.csv`.

### Why Astra's script output token count was lower

Output tokens sum model-generated output across the execution: tool-call arguments, verification/packaging code, commentary, and final responses. They are **not the generated report's token count**. Python generated the same reports for all configurations.

The host transcripts show Astra generally used compact commands and shorter verification/packaging code. Sol often added extensive checks: in one median-adjacent script run, a verification/packaging call accounted for 1,463 of 2,121 output tokens. Luna sometimes added extra steps, including the administrative messages noted above. Astra's lower total therefore reflects less observed orchestration overhead, not shorter reports or established intrinsic reasoning efficiency. Separate reasoning-token totals were unavailable.

### Cost limitations

Costs are conditional **API-dollar equivalents**, not subscription charges or invoices. They use the repository-supplied dated pricing table, not independently verified current prices, with default standard global scope and the observed cache mix. Assistant usage counters were summed from host exports; every message satisfied `totalInputTokens = inputTokens + cacheReadInputTokens + cacheCreationInputTokens`. Terminal aggregates were not double-counted.

Reasoning-token totals, underlying request counts, supporting-system usage, and per-request billing receipts are unknown. Projections assume one invocation each week, a uniform six-fixture mix, the observed cache mix, and no whole-run retries; they exclude human work, orchestration, hosting, and development costs. Unknown measurements are not zero.

## Interpretation and next step

For this fixed reporting task, using the script was reliable across all three tested configurations and left little reporting work for the model. The tool-driven results illustrate analysis-selection and scorer-sensitivity differences. They do **not** establish that Luna is generally equivalent to larger models on narrow jobs, that broad agents are generally reliable, or that any model is a universal winner.

This is a small development pilot with one observation per fixture/cell, different host behaviors/effort settings, no held-out confirmation, and no completed human review. A useful next step is blinded review of support, usefulness, restraint, and next checks before making stronger quality claims. Any scorer revision should be versioned and tested in a new study, not retrofitted to these official scores.

## Published data

- [results.csv](results.csv): 78 individual rows with official scores, scoring errors, timing, token usage, and conditional cost; private host-thread links removed.
- [summary.json](summary.json): 13 groups pooled by frozen target and treatment, plus conditional projections and measurement caveats. The controller's native full-configuration aggregation produced 73 groups because session IDs differed; this grouping excludes those per-session IDs.
- [config.json](config.json): frozen target configuration and study factors.
- [blinded-review.zip](blinded-review.zip): 78 report/fixture sets and blank ratings, without private mappings or host logs. Reviewers should receive only this ZIP, not the identifiable results table.

Raw host exports, local run directories, private paths, and the reviewer-to-run mapping are intentionally not committed. The publication supports auditing the reported aggregates and reviewing outputs; it does not include every raw execution artifact. All fixture/source data are synthetic; the model executions and measurements are real.
