# Study design

## Question and scope

This study asks how prompt breadth and execution style affect the same weekly synthetic analytics report. Its central design crosses narrow versus broad instructions with tool-driven reporting versus invoking a saved script. A deterministic pipeline anchors the comparison; narrow and broad interpretation of prepared evidence supply a secondary comparison. It does not assume that any arm wins, or that a tool-using host makes a particular model intrinsically more agentic.

The experimental unit is a host, configured model roles, observed models when available, native configuration, prompt breadth, and execution style. Configuration includes effort, service tier, enabled tools, routing, inherited instructions, host version, context policy, and observed cache condition. Hosts may add undisclosed prompts or helper calls. Opaque native routing is a valid host configuration; record its opacity instead of inventing a pure-model attribution. Identical fixtures cannot erase those confounds.

All inputs are synthetic Search Console and PostHog aggregates for two adjacent seven-day windows. Nothing fetches customer analytics, sends messages, or publishes a report. Search Console clicks, impressions, position, and CTR remain separate from PostHog sessions, users, conversions, and conversion rate. CTR and conversion rate are stored as ratios; `wow_pct` is a relative percentage change. A ratio's absolute change is in ratio units, not automatically percentage points.

## Treatments

| Arm | `prompt_breadth` | `execution_style` | Evaluated behavior |
| --- | --- | --- | --- |
| A | `none` | `deterministic_pipeline` | Fixed fetch, validation, arithmetic, findings, and template |
| B | `narrow` or `broad` | `prepared_evidence` | Model interprets prepared evidence under the assigned instruction |
| C | `narrow` | `tool_driven` | Explicit checklist; natural low-level tool invocation |
| D | `broad` | `tool_driven` | Goal and output contract; natural low-level tool invocation |
| E | `narrow` or `broad` | `saved_script` | Agent invokes A as a saved script |

The central 2×2 consists of C, D, E-narrow, and E-broad. Compare C against E-narrow and D against E-broad for execution style under matched breadth. Compare C against D and E-narrow against E-broad for instruction breadth under matched execution style. Use the same fixtures, repeated allocation, host configuration, output contract, and scoring across these cells. B's two variants are a secondary comparison because preparation changes what work remains for the host. A has no prompt-breadth treatment.

Configure targets through `execution_styles` and `prompt_breadths`; A–E are derived labels, not the primary configuration interface. A model target selecting `tool_driven` and `saved_script` at both breadths produces four primary cells. Adding `prepared_evidence` produces six model cells. A separate `deterministic_pipeline` target with breadth `none` adds the baseline. The default offline study therefore has seven cells, six development fixtures, and five repeats: 210 planned runs. Each target/fixture/repeat has a shared `pair_id` across its treatment cells. Compare matched cells within that identity; the separately configured baseline is an additional reference, not an identical host treatment.

All arms use unchanged arithmetic and the same report schema and Markdown renderer. A–D have equivalent low-level data and calculation capability. A's decisions are fixed in code. B can select and write findings, limitations, summary, and next checks; its source data, period identity, and numeric evidence come from deterministic preparation. C and D choose how to execute within the assigned instructions and must invoke the supplied low-level tools. E alone receives the complete pipeline module and `saved-report` shortcut.

A native host turn may contain several inference calls, retries, helper models, and routing decisions. Those are legitimate observed behaviors in every model arm, including B. Request count is a measurement, never a single-call purity requirement or an exclusion rule. A host invocation, message count, or token total does not identify underlying request count. Tool tracing verifies observable supplied-tool calls; it does not prove the absence of helper inference or access outside the packet.

## Fixtures and isolation

The versioned development and held-out splits contain growth, decline, small changes, zero baselines or denominators, incomplete data, and recoverable tool failures. Deterministic source-failure counts reset for each attempt. Low-level source retries stay inside that attempt's tool trace. A new run attempt gets a new packet and is retained separately.

Use the development split to implement and debug runners. Freeze the benchmark revision, run configuration, scorer, and pricing table before inspecting held-out results. Do not tune a prompt on a failed held-out case and describe a rerun as a first held-out test. Log the change and treat the follow-up as a new study.

The evaluator receives one fixture, shared answer-free validation/calculation/rendering code, schemas, and its arm prompt. It does not receive the scorer or other fixture files. B additionally receives deterministic evidence. E necessarily receives A's report logic; that disclosure is its treatment, and code access can reveal its fixed decision rules. Do not reuse E's context for another arm.

The controller repository contains both splits and scoring logic. A host with unrestricted filesystem access can read them despite the packet instruction. A separate machine, container, account, or enforceable root-restricted sandbox is required to establish a stronger boundary. Document what was actually enforced. Repository history, global host instructions, memories, and prior development conversations can also leak study information. A new conversation reduces carryover but does not prove the absence of inherited context.

Publishing the repository exposes its held-out split. It remains useful for reproducing these tests; it cannot serve as an indefinitely secret future benchmark. Use new withheld fixtures and publish their hashes before a later confirmatory study, then release the data after evaluation if desired.

## Run allocation and outcomes

Use five repeats per fixture, target, and treatment cell as a practical starting point, configurable in the study JSON. The configured seed randomizes allocation order. IDs derive from the frozen configuration, manifest, and allocation identity, so the same plan produces stable identities. Save `plan.json`; its timestamps and measurements are not expected to be byte-identical across executions.

The supplied runs use `invocation_mode: fresh_context`. A manually launched fresh process is not a scheduled execution. Label a run `scheduled` only when an actual scheduler launched it and `schedule_evidence` identifies the retained evidence. This distinction prevents “cron job” from becoming an unmeasured label. The harness does not itself install a recurring scheduler.

Each attempt uses a fresh host context. Keep `cache_state` separately as `cold`, `warm`, or `unknown`: fresh context is not proof of a cold provider cache. If deliberately comparing cache conditions, preregister separate target configurations and a reproducible warm-up policy; retain warm-up work as setup rather than hiding it.

Outcomes include `completed`, `failed`, `quota_exhausted`, `timeout`, and `protocol_error`. A completed output can fail deterministic scoring. A report can pass scoring while evidence for an assigned tool or context condition is unavailable. Record those distinctions. Unknown request counts and opaque host routing do not make an attempt noncompliant. Quota exhaustion is an observed host/configuration outcome, not a reason to discard an attempt or change billing route. The harness has no spending or quota-conservation gate. Ordinary timeouts bound hangs.

Resume pending work under the same frozen plan. Retries create another numbered attempt; they never overwrite the first attempt. Report both first-attempt reliability and success after the observed retry policy. Keep source-tool retries, whole-run retries, request counts, and host-reported internal retry evidence distinct. Do not infer hidden retries from tokens alone. Avoid mixing ad hoc reruns with a fixed retry policy without labeling that change.

## Deterministic scoring

The scorer evaluates the same report contract for every arm. Its seven components are:

1. Schema and required fields, including no more than three findings.
2. Numeric agreement with source-specific calculations and reporting periods.
3. Evidence references and structured claims matching the cited source, metric, and value.
4. Coverage of predefined material changes.
5. Correct completeness, nulls, and limitations for missing or undefined comparisons.
6. Bounded checks for unsupported numeric prose, direction contradictions, causal attribution, and source conflation.
7. Canonical agreement between `report.json` and `report.md`.

An automated pass requires every component to pass. The component mean is a diagnostic score, not a validated interval scale of writing quality. Invalid schemas fail before downstream components can be evaluated. Numeric comparison uses a relative tolerance of `1e-7` and absolute tolerance of `1e-6`; the shared runtime rounds changes and ratios consistently.

The frozen material-coverage rule requires findings for comparable Search Console clicks or PostHog sessions whose absolute week-over-week percentage change is at least 10%. This is an operational threshold for this benchmark, not a universal business definition of materiality. It fits within the three-finding limit. Other supported findings may also be reported. Reviewers should distinguish this mechanical coverage rule from a judgment of which findings matter most.

Incomplete observation windows withhold absolute and relative changes even when partial totals exist. Missing source values remain null. A zero previous value makes percentage change undefined; a zero denominator makes the derived rate undefined. A supported `insufficient_evidence` finding is valid. The benchmark requires synthetic-data and source-distinction limitations, plus the relevant data-quality limitations. It does not reward inventing a cause, treating clicks as sessions, or forcing a percentage from a zero baseline.

Structured support checks are stronger than free-text checks. The scorer cannot detect every unsupported claim, paraphrase, implication, misleading emphasis, or poor recommendation. The baseline and scorer share arithmetic, so tests include independent expected values and deliberately corrupted reports; shared code alone is not proof of correctness. Preserve scorer errors with the raw report for audit.

## Blinded human review

Export canonical reports under opaque review IDs and keep the ID-to-run mapping outside the reviewer packet. Review all outcomes or a preregistered random sample, not only attractive reports. Hide host/model/arm and numeric scores until the judgment is recorded. Report text may still reveal stylistic cues; blinding is not guaranteed anonymization.

Ask reviewers to assess evidence support, source distinction, restraint under missing data, materiality of selected findings, clarity, and usefulness of next checks. Record an overall judgment and concrete errors, including unsupported claims the deterministic checks missed. Where feasible, use more than one reviewer and retain disagreements. A passing automated report is not a substitute for human review, and an LLM judge is not the sole arbiter.

## Usage, cost, and latency

Keep exported counters and raw artifacts with provenance. `input_tokens` includes cache-read and cache-write subsets; `output_tokens` includes reasoning-output subsets. Do not add those subsets again when computing total tokens or cost. Native counters with different semantics must be mapped explicitly. Do not add both a terminal aggregate and its underlying message totals. A missing counter is null, even if the host likely did no work of that kind. Known zero is reserved for measured/exported zero or deterministic no-LLM work.

Record `configured_main_model`, `configured_auxiliary_models`, `observed_models`, and `routing_mode` separately. Configured roles are intentions; observed models require exported evidence. Unknown auxiliary models are null, not an invented empty list. `routing_mode` is `explicit`, `host_native_opaque`, or `unknown`. Retain requested and actual model IDs where known, with provenance for the actual ID. The selected UI label is not proof of an actual provider ID.

Natural mixed-model routing remains a valid host-level result. It cannot be priced as one verified model without attributable per-model usage; retain that measurement limit. Tool counts measure the supplied tool interface, not every host-internal tool or inference.

Separate packet setup time, deterministic evidence preparation, and runtime. B's preparation is included in report runtime as well as exposed separately. Measured runtime includes observable work and retries in that attempt; a manual run's supplied timing is only as reliable as its evidence. Development, installation, account login, human review, and host startup outside the observed interval require separate setup accounting if included in an economic comparison.

The dated pricing table is configurable and sourced. Matching requires a known actual model and appropriate rate assumptions. Cache reads, cache writes, service tiers, long-context regimes, regions, and hosting can change the applicable rate. Open weights have no universal API price. Unknown hosting or missing applicable counters can make full cost unavailable; a partial known subtotal is not a full cost. API equivalents are hypothetical estimates, not actual subscription charges or claims about a host's wholesale cost.

Publish cold/warm/unknown groups separately. For 4, 13, and 52 weekly reports, state the representative runtime distribution, source/fixture mix, repeats, retry policy, cache mix, price date, and setup amortization. These are linear planning projections under stated assumptions, not forecasts of quota capacity, price stability, or operational success.

## Analysis and reporting

Retain raw per-attempt JSONL and disclose planned runs, finalized attempts, unresolved work, failures, retries, verified treatments, and missing measurements. Use planned runs for completion coverage; use all observed attempts for attempt reliability; use first attempts for first-attempt success; and label any eventual-success measure with its retry policy. Never remove failures from a latency or cost narrative just because they have no report.

Report pass rate and component results alongside human judgments. Include latency sample size, mean, median, percentile spread, and variability where available. Unknown latency reduces measurement coverage and is not a zero-duration run. Show cost measurement coverage; cost per passing report includes costs of observed failed attempts and retries, and remains unavailable when required costs are missing. Zero passes has no finite cost-per-pass result.

Do not pool mocks with real runs, development with held-out results, or incompatible host configurations. Small repeated samples and shared fixtures do not establish population-wide rankings. Publish the frozen configuration, manifest hash, version, actual model evidence, treatment-verification coverage, review method, and all material limitations with any article claim. The harness supplies measurements; it does not choose the article's conclusion.
