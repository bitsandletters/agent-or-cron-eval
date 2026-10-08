# Host execution and measurement notes

Verified against public documentation on **2026-10-08**. This is a subscription-host study: the experimental unit is **host + requested model + observed model(s), when available + configuration + arm**. Identical fixtures and scoring do not remove system-prompt, tool, context, routing, or cache differences.

## What was checked locally

In the local validation environment on 2026-10-08, `codex` and `amp` were not on PATH. Cursor editor CLI reported `3.22.12`; its separate `agent` CLI reported `2026.09.18-9a7762b`. `agent --help` confirmed print mode, `--model`, `--workspace`, JSON/stream-JSON output, sandbox controls, and `models`/`status`. The read-only `agent models` command returned **Authentication required**, exit 1. No model requests were made. Account-specific model availability, actual subscription charging, and real output exports remain unverified. No credential files or private session stores were inspected.

The commands below are launch recipes for the operator, not evidence that these suites have run. Keep local version/help output with each experiment, because host interfaces change.

## Common operator protocol

1. Prepare one packet with the harness. Use only its prompt, schemas, fixtures, and allowed tools in the evaluated workspace. Keep scorer, reference answers, other runs, and held-out fixture collection outside the host's accessible root.
2. Start a new conversation/process for each fresh-context attempt. Do not resume, fork a prior conversation, or reuse an agent that helped develop the harness. Save the host session ID when exported. Use `invocation_mode="scheduled"` only for an actual scheduled invocation with supporting provenance; a command launched manually remains `fresh_context`.
3. Record the exact requested selector, effort, speed/service tier, enabled tools/plugins, host version, authentication mode, cache condition, and known inherited rules or memory. An operator label such as “Grok” is not a provider model ID. Leave the actual ID null unless an artifact identifies it.
4. Run the assigned arm and retain `report.json`, `report.md`, the raw event stream, stderr, exit status, elapsed time, and tool trace. Import manually exported artifacts when a host cannot be automated. Preserve malformed outputs, timeouts, retries, and quota errors as outcomes.
5. Import only evidence-backed usage values. Missing fields remain null. A dashboard total shared with unrelated activity cannot be attributed to this attempt; retain it as context rather than converting it into run usage.

Do not enable provider API billing, add paid API keys, or change billing settings to make a subscription run work. If subscription access fails, retain the failure. This harness does not impose spending caps, conserve quota, purchase credits, switch models, or retry through another billing route. A timeout prevents hangs; it is not a spending gate.

Fresh conversation does not prove cold cache. Record cold/warm/unknown separately and retain the observed cache counts. A local packet is a convenience boundary, not an OS security boundary: a host with unrestricted shell/filesystem access can still read the checkout or other packets. For held-out results, use a separately restricted account/container/VM and record its policy. Repository instructions, global skills, memories, and host-provided helpers are possible confounds; document them without exposing private content.

## Comparison factors and routing metadata

The comparisons vary prompt breadth and execution style. Record both factors independently of the arm label:

| Arm | `prompt_breadth` | `execution_style` |
| --- | --- | --- |
| A | `none` | `deterministic_pipeline` |
| B | `narrow` or `broad` | `prepared_evidence` |
| C | `narrow` | `tool_driven` |
| D | `broad` | `tool_driven` |
| E | `narrow` or `broad` | `saved_script` |

Use these fields to describe the native host configuration without guessing its internals:

| Field | Meaning |
| --- | --- |
| `configured_main_model` | Explicitly configured main-model selector, or null when unknown. It records configuration, not proof of the model served. |
| `configured_auxiliary_models` | Known configured helper-model list; null when unknown. An empty list asserts that no auxiliary models were configured and needs evidence. |
| `observed_models` | Model IDs supported by the run's exported artifacts; null when unavailable. Do not substitute the requested selector or a display name. |
| `routing_mode` | `explicit` for documented explicit model routing; `host_native_opaque` when the host handles routing without exposing the full route; `unknown` when routing information is unavailable. |
| `invocation_mode` | `fresh_context` for a newly started evaluation context; `scheduled` only when the run was actually scheduled and that origin is attested. |

Native helper calls, retries, routing, and internal request counts are measured host behavior. They do not invalidate B or any other arm solely because multiple models or requests were involved. Group comparisons by host and configuration, and retain unknown routing fields as unknown. A schedule label describes invocation provenance; it does not establish agentic behavior.

## OpenAI Codex runner brief

Use an existing **ChatGPT subscription** login. `codex login status` reports the active authentication method. OpenAI documents both subscription and separately billed API-key paths; `forced_login_method="chatgpt"` is a documented way to require the intended route. Do not obtain credentials by reading local files. [Authentication](https://learn.chatgpt.com/docs/auth)

After installing a supported CLI and authenticating interactively, check `codex exec --help` and run a fresh `exec` from the packet directory. A recipe, with `MODEL` set to an available selector, is:

```sh
codex --version
codex login status
codex exec --json --model "$MODEL" -c 'forced_login_method="chatgpt"' \
  --sandbox workspace-write --output-last-message final.txt - < prompt.md \
  > host-events.jsonl 2> host-stderr.txt
```

Use the harness command adapter or import the resulting files. If the CLI refuses a non-Git packet, review its documented `--skip-git-repo-check` option or initialize only that disposable packet; do not expose the full benchmark checkout to solve it. In the desktop app, use a new local task attached to the packet, choose the model explicitly, paste the prompt, and import the outputs. An app task with prior study discussion is not a fresh context.

The documented JSONL stream includes session/turn events, tool items, failures, and `turn.completed.usage` with `input_tokens`, `cached_input_tokens`, `output_tokens`, and, in the current example, `reasoning_output_tokens`. Record only fields present in the actual version's export. Final response capture and `--output-schema` are documented. A turn event describes an agent turn; underlying request count and actual model IDs may be unavailable. Request counts are descriptive measurements, not an arm-compliance criterion. [Non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode)

Treat cached input as a subset only when the export semantics establish that relationship. Reasoning tokens may already be inside output totals: retain their breakdown but never add them twice. A run-level total does not reveal the context length or service tier of every underlying request.

## Amp runner brief

Amp documents local execution and streaming output:

```sh
amp --version
amp --help
amp --execute --stream-json < prompt.md > host-events.jsonl 2> host-stderr.txt
```

Run from the packet directory, use a new thread, and avoid `threads continue`. Execute mode is an agent turn, not a single inference. Its documented noninteractive authentication is an **Amp access token**, not an OpenAI provider key; do not extract the short-lived login token from disk. Local authenticated operation and a manual fresh-thread import are alternatives when CLI automation is unavailable. [Execute mode](https://ampcode.com/docs/cli/execute-mode)

There is no verified generic Amp `--model` recipe here. Choose and record the mode before its first message. **Tune Modes** supports main-agent, Oracle, and subagent model/effort pins; record the roles that are known, or retain the host's native routing. The documented ChatGPT subscription connection and ChatGPT Only preset can route OpenAI usage to the subscription. Presets can change, unavailable pins can fall back, and supporting system models are not covered by role pins. These are configuration characteristics to record, not requirements to eliminate auxiliary models. [The Dial](https://ampcode.com/docs/the-dial)

Inspect the routing preview and the read-only `amp config model-providers list` output, redacting account details before sharing. Connection precedence and unmatched models can route to Amp credits or other configured providers. Do not use `check-access` as an offline check: its documentation says it performs inference. Use the intended subscription connection and document billing provenance and any unknowns. Do not enable a separately billed provider route to complete the run. Opaque native model routing is valid host behavior and should be recorded as `host_native_opaque`. [Model routing](https://ampcode.com/docs/customize/model-routing)

Amp's stream schema has optional `assistant.message.usage` and optional terminal `result.usage`: input, output, cache-read, cache-creation, and sometimes 5-minute/1-hour write breakdowns. Use the terminal aggregate **or** complete per-message records, never both. Retain session ID, duration, reported turns, errors, and tool-use IDs. Model IDs and reasoning-token totals are not promised. The adapter preserves exported output/cache counts but leaves canonical input total null because the public schema does not establish cache inclusivity across routed models. A canonical import can supply a total when artifact semantics support it. Missing cache fields remain unknown. [Streaming JSON](https://ampcode.com/docs/cli/streaming-json)

## Cursor runner brief: Grok, Claude, open weights

Use the existing Cursor account login, then inspect the supported catalog:

```sh
agent --version
agent status
agent models
```

`agent login` is the documented browser flow. `agent status` reports authentication/account/endpoint information. The Cursor user API key is a Cursor credential, but these recipes use browser login and do not configure provider keys. [Authentication](https://cursor.com/docs/cli/reference/authentication)

Choose the exact selector returned for the account, record all bracket overrides, and start a fresh invocation without `--resume` or `--continue`:

```sh
agent --print --output-format stream-json --model "$MODEL" \
  --sandbox enabled --auto-review --workspace "$PACKET" \
  "Read prompt.md and execute this one evaluation attempt." \
  > host-events.jsonl 2> host-stderr.txt
```

`--auto-review` was verified in local help; verify it on other versions. Approval behavior can affect latency and failures, so record it. The native agent has shell/write tools. For interactive execution, open only the packet workspace and start a new chat with the selected model. [CLI parameters](https://cursor.com/docs/cli/reference/parameters), [CLI overview](https://cursor.com/docs/cli/overview)

The documented stream has an initialization model **display name**, `apiKeySource`, session ID, tool start/completion IDs, terminal result, timing, and optional request ID. No token/cache/reasoning usage fields are promised by that schema; print mode suppresses thinking events. Preserve raw output, import usage separately when available, and leave unavailable numbers null. Do not infer request counts from assistant text fragments or duplicate streamed flushes. [Output format](https://cursor.com/docs/cli/reference/output-format)

Cursor documents included usage pools for Grok and other models including Claude, with optional additional usage. Record the account's actual route; do not enable additional billing for this experiment. Public listings do not establish a particular account's entitlement or an open-weight model's availability. Run open-weight entries only if the account's catalog and route support them under the intended subscription; otherwise record **model unavailable**. Do not silently replace them with an API gateway, local server, or a different model. [Models and pricing](https://cursor.com/docs/models-and-pricing)

## Arm B: prepared evidence and native interpretation

B means deterministic evidence preparation followed by model interpretation inside the selected host. Run it with both narrow and broad prompts. The prepared evidence, low-level tool interface, and output contract define the treatment; the host may use its natural planning, file access, helper models, internal retries, or context management while interpreting that evidence.

There is no one-request requirement. Multiple or unknown internal request counts do not make a B run noncompliant and are not grounds to exclude it. Capture available request counts, token totals, observed models, latency, failures, and tool activity as outcomes. If the host hides an internal detail, record it as unknown and preserve the raw export. Keep native subscription execution for this comparison; do not replace it with an independently billed API call.

## Pricing and publication

`pricing/prices.json` is a dated, editable **API-equivalent** reference, not a subscription invoice or claim about what the host pays. Match verified actual provider IDs exactly. The supplied rates assume their stated region, service tier, context regime, and cache-write duration. An exact `usage.pricing_scope` match can select a listed alternative regime; the estimator does not infer a regime from a run-wide token sum. Default-scope estimates are conditional, and an explicit unmatched scope leaves the total unavailable. Unknown model, hosting, usage, cache semantics, or cache-write duration can also make the total unavailable; a known subtotal is not a full cost.

For each published comparison, include the price-table version/checksum, source date, measured versus estimated fields, excluded costs, and host configuration. Weekly projections at 4, 13, and 52 reports assume a stated representative runtime distribution, retry/failure policy, cache mix, and separately amortized setup. A host's monthly included pool is not a dollar conversion rate. Open weights do not imply free hosting; the example `gpt-oss-120b` row deliberately has unknown prices and makes no Cursor availability claim. [OpenAI open-weight model reference](https://developers.openai.com/api/docs/models/gpt-oss-120b)
