# Runner protocol

Protocol version: **1.0**. All host adapters consume the same evaluation packet and return the same two report files. The controller owns planning, integrity checks, attempt retention, scoring, and aggregation. The host owns its authenticated subscription session. There is no provider API fallback.

## Factor-first configuration

Each target selects `execution_styles` from `deterministic_pipeline`, `prepared_evidence`, `tool_driven`, and `saved_script`, plus `prompt_breadths`. The baseline uses only `deterministic_pipeline`, a `baseline` runner, and breadth `none`. Model targets use `narrow`, `broad`, or both. The primary factorial comparison uses `tool_driven` and `saved_script` at both breadths; `prepared_evidence` adds the secondary interpretation comparison.

The planner derives arm labels and records both factors in each allocation. `tool_driven` with narrow breadth becomes C and with broad breadth becomes D. `saved_script` is E at either breadth; `prepared_evidence` is B; the deterministic baseline is A. Legacy `arms` selection remains supported but is mutually exclusive with `execution_styles`. Prefer factors in new configurations, and keep the supplied examples as the reference for complete target syntax.

Set the configured main model in `target.configured_main_model` and known auxiliary configurations in `target.configured_auxiliary_models` (list or null). Keep observed model evidence in imported metadata. A target's `pair_id` allocation groups the same fixture and repeat across factor cells, while each cell has its own stable `run_id` and fresh attempt context.

## Controller and evaluated context

Run controller commands from the benchmark checkout. Give only the exported packet to the evaluated host. Do not attach this README, scorer, controller source, other fixture files, example answers, or previous reports to the evaluated context. The host receives the packet's `prompt.md`, not instructions improvised per run.

An exported attempt is stored under:

```text
runs/STUDY/runs/RUN_ID/attempt-NNN/
  attempt.json             Controller allocation, timing, packet hashes
  packet/
    prompt.md              Common contract plus assigned-arm prompt
    run.json               Run identity, arm/factors, fixture ID, repeat
    fixture.json           One synthetic two-week data fixture
    report.schema.json     Common JSON output contract
    tools.schema.json      Tool interface contract
    runtime.py             Shared validation and arithmetic
    reporting.py           Shared answer-free Markdown renderer
    tool.py                Local tool command
    metadata.template.json Unknown-safe metadata starting point
```

B also receives prepared `evidence.json` and its deterministic preparation trace. E also receives `baseline.py`, which implements A's complete-report shortcut. Other arms must not obtain that shortcut. Runtime-generated files include `.tool_state.json`, `tool_events.jsonl`, and `evidence.json`. Scoring logic and the full fixture set stay with the controller.

The controller verifies the packet input hashes on import. Edit new output files, not the supplied prompt, schema, fixture, tool code, evidence, or template. Copy the metadata template to a separate metadata file. Input mutation becomes a protocol violation. Hashes establish unchanged bytes; they do not prove that an unrestricted host never looked outside the packet.

Tool traces and operator metadata support reproducible auditing; they are not tamper-proof attestation. A host with shell access can write output files, and the importer cannot independently authenticate every claimed counter or context condition. Keep original host exports and the isolation policy with the results, and distinguish observed evidence from operator assertions.

## Supplied tools

Run from the packet directory using the host's natural shell tool or an adapter exposing these exact operations:

```sh
python3 tool.py fetch search_console
python3 tool.py fetch posthog
python3 tool.py calculate
python3 tool.py render
```

`fetch` exposes one source and records success or failure. A seeded recoverable error is part of the task; retrying the failed source is permitted. `calculate` requires both sources to have been fetched successfully, validates them, and writes unranked `evidence.json`. It does not select findings or write a complete report. `render` renders the completed `report.json` into canonical `report.md` without deciding what the report says. E alone may invoke:

```sh
python3 tool.py saved-report
```

This fetches with bounded source retries, validates, calculates, selects fixed findings, and writes both report files. The trace distinguishes saved-report invocation from its internal fetch/calculation work. A runs this deterministic logic under controller execution with no LLM.

C and D must show successful `calculate` in their trace. E must show successful `saved-report`. B interprets controller-prepared evidence under a narrow or broad prompt and preserves its numeric fields. Natural host requests, internal helpers, and routing are valid behavior. Count them when exported; missing counts are unknown. There is no exactly-one-request requirement or exclusion for opaque routing.

## Output contract

The schema in the packet is authoritative. `report.json` contains exactly:

| Field | Meaning |
| --- | --- |
| `schema_version` | Shared contract version |
| `fixture_id`, `periods` | Identity and the two weekly windows |
| `summary` | Brief source-grounded summary |
| `sources` | Separate Search Console and PostHog completeness and KPIs |
| `findings` | Zero to three structured evidence-backed findings |
| `limitations` | Data and interpretation limits |
| `next_checks` | Concrete further checks, without invented observations |

Every KPI carries previous/current values, absolute change, `wow_pct`, unit, comparison status, and stable evidence references. A finding identifies its source and metric, states `change` or `insufficient_evidence`, and pairs evidence references with numeric or null structured claims. Do not insert fabricated zeros for missing values. Do not conflate clicks with sessions or infer causes from these weekly totals.

For B, use the prepared identity, periods, and source/KPI blocks without modification; the model supplies the narrative fields. Follow B's packet prompt for assembling the final report. Other arms use the same final contract. Generate Markdown from the JSON through `render`; both files are required and their content must agree.

The run allocation records `prompt_breadth` (`narrow`, `broad`, or A's `none`) and `execution_style` (`deterministic_pipeline`, `prepared_evidence`, `tool_driven`, or `saved_script`). Do not silently change the assigned breadth or substitute a saved script in C/D. C and D form the narrow/broad tool-driven cells; E has both matching saved-script cells. B also has both breadths as a secondary comparison.

## Manual import lifecycle

1. Create a frozen plan with `plan --config ... --out ...`.
2. Use `status --study ...` and the plan to select the next assigned run.
3. Run `export --study ... --run-id ...` to create its fresh numbered packet.
4. Start a new host conversation rooted in that packet. Record model/configuration and execute its prompt. Do not resume a prior conversation or let a development agent evaluate itself in its existing context.
5. Retain report files, raw host exports, latency evidence, session identifiers when available, and errors. Fill a new metadata file with verified fields.
6. Run `import --study ... --run-id ... --attempt N --metadata ...`, optionally adding a documented `--usage-artifact`.

An unfinished attempt must be imported or recorded as a failure before another attempt is created for the same run. Finalized attempt records are not overwritten. A retry gets a new number and new context.

Import quota exhaustion, timeout, or failure even when no report was produced. Set the observed status and include available usage up to failure. Never supply a success-shaped report just to get an error into the system. If a host does not export a dedicated quota status, retain the actual error artifact and explain the operator classification in the failure metadata.

## Metadata and provenance

Start with the generated `metadata.template.json`. This minimal example describes an incomplete measurement, not a measured zero:

```json
{
  "status": "completed",
  "actual_model": null,
  "actual_model_source": null,
  "observed_models": null,
  "observed_models_source": null,
  "routing_mode": "unknown",
  "invocation_mode": "fresh_context",
  "schedule_evidence": null,
  "usage": {
    "input_tokens": null,
    "output_tokens": null,
    "cached_input_tokens": null,
    "cache_write_tokens": null,
    "reasoning_output_tokens": null,
    "request_count": null,
    "provenance": "unavailable",
    "source": null
  },
  "latency_seconds": null,
  "host_version": null,
  "subscription_route": "unverified",
  "fresh_context": null,
  "native_configuration": {},
  "cache_state": "unknown",
  "notes": "Fill only fields supported by this attempt's artifacts."
}
```

`requested_model` comes from the frozen target configuration. Set `actual_model` only when an export identifies it, and name the artifact/field in `actual_model_source`. Do not copy the request selector into actual-model metadata merely because the host accepted it. For mixed-model routing, retain the native breakdown and describe the cost-attribution limitation; the run remains a valid host/configuration observation.

Set `configured_main_model` and `configured_auxiliary_models` in the target configuration before planning. The main field names the configured main role when known. The auxiliary field is a list of known configured helper roles/models, or null when unavailable; an empty list means verified absence, not ignorance. These configuration facts are copied into each result.

In imported metadata, `observed_models` is a list of exported model identifier strings, or null. A nonempty list requires `observed_models_source` identifying its export. Keep exact observed identifiers with evidence; do not turn display labels into invented provider IDs. If several models are observed, aggregate usage cannot be attributed to the main model, so the controller withholds its single-model cost attribution. `routing_mode` is `explicit`, `host_native_opaque`, or `unknown`. Native opaque routing is allowed and is not a purity failure.

`invocation_mode` distinguishes `fresh_context` from `scheduled`. The supplied workflows launch fresh contexts. Use `scheduled` only when an actual scheduling system launched the run, and provide `schedule_evidence` identifying that evidence. The harness does not create a scheduler, and a manual batch or a script on disk is not proof of scheduling.

`native_configuration` should record observable effort, service tier, mode, tools, plugins, sandbox/approval policy, inherited-rule presence, session ID, and routing. Do not copy private account data or credentials into the repository. Record fresh context and subscription route only to the extent the execution evidence supports them.

The canonical usage semantics are:

- `input_tokens` includes the disjoint cache-read and cache-write subsets.
- `output_tokens` includes the reasoning-output subset.
- `total_tokens` is input plus output only when both are known; it is computed by the harness.
- `request_count` means underlying model requests, not host turns, assistant fragments, tool calls, or sessions. It is an observation; no arm requires a particular count.
- `provenance` is `measured`, `estimated`, or `unavailable`; `source` identifies how the counters were obtained.
- Missing fields remain null. A partial measurement stays partial; no tokenizer heuristic is silently substituted.

The normalizer rejects negative counters, booleans, and subset totals larger than their parent totals. When a native format reports uncached input separately, the adapter must establish all necessary parts before populating canonical input. For cost interpretation, optional `pricing_scope` can verify a table row's exact assumptions; otherwise the price estimate states that the scope is assumed.

`--usage-artifact` parses documented Codex/Amp shapes and preserves the raw artifact. It replaces the canonical usage supplied in metadata, so choose the appropriate path. An unsupported shape yields unavailable counters. Cursor or other exports without a documented token mapping should be retained separately, with any verified canonical counters supplied through metadata rather than an unsupported parser. See [host notes](hosts.md) for field-level limits and current sources.

For a failure, use the same metadata structure with an outcome such as:

```json
{
  "status": "quota_exhausted",
  "actual_model": null,
  "actual_model_source": null,
  "usage": {},
  "latency_seconds": null,
  "fresh_context": true,
  "subscription_route": "operator_verified_subscription",
  "failure": {
    "kind": "quota_exhausted",
    "message": "Operator classification; retain the exact exported error artifact."
  },
  "notes": "No report produced. No alternate billing route was used."
}
```

Only use this classification when it is what the host actually reported; generic process failure is not automatically quota exhaustion.

## Command adapter lifecycle

A `command` target supplies an `argv` array, `billing_route: "subscription"`, an optional requested model, and a timeout. This is not shell text. The controller substitutes `{packet}`, `{prompt}`, and `{model}` inside argument strings, executes with the packet as its working directory, retains stdout/stderr, and measures wall time. Use an adapter when the host expects prompt content on stdin or needs host-specific file handling. Do not put credentials in `argv`, study JSON, or reports.

The controller removes common provider/API-key environment variables from the child process. That prevents accidental inheritance through those variables; it does not inspect host credential storage or prove billing mode. The operator must use the host's documented subscription authentication and record it. The adapter must not fall back to a provider key, credits purchase, gateway, or another model when that route fails.

The adapter should invoke one fresh host process for one packet, stream the host's documented event format to stdout, keep diagnostics on stderr, write the required report files, and write `metadata.json` with verified extra fields where possible. It should preserve nonzero exit codes and quota errors. Timeout kills the launched process group and retains the timeout outcome. Avoid daemonizing children, resuming host sessions, or masking errors.

Command execution is opt-in through `run --mode command`; the default offline mode executes only the deterministic baseline and mock targets. A manual target is never silently launched. Available model catalogs, login, and routing must be verified on the executing machine; host example selectors are not a guarantee of availability.

## Integrity, scoring, and handoff

`verify` checks the shared manifest before planning/resuming. `manifest` deliberately updates the expected hashes and is for reviewed benchmark changes. Each plan pins a manifest hash; restoring the original revision is necessary to resume after a protocol change. Keep development/held-out split, source revision, configuration, pricing sources, and artifacts together when handing the study to another host.

The controller scores finalized completed reports, flags input mutation and observable treatment violations, and retains errors. Multiple requests, unknown request counts, and opaque native routing do not make B or any model arm noncompliant. The JSONL records are the auditable unit of measurement. Aggregation and blinded review export operate on those retained records; keep account metadata and the private review mapping out of public artifacts.

For future held-out secrecy, use a new confirmatory fixture version withheld from evaluated hosts until the study is frozen. Public fixture releases support reproducibility but do not preserve secrecy for later studies.
