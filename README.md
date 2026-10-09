# Is it an agent, or just a cron job?

[![Offline verification](https://github.com/bitsandletters/agent-or-cron-eval/actions/workflows/verify.yml/badge.svg)](https://github.com/bitsandletters/agent-or-cron-eval/actions/workflows/verify.yml)

A portable, synthetic weekly-analytics benchmark for the accompanying article. Its central comparison crosses narrow versus broad instructions with tool-driven reporting versus invoking a saved script. A deterministic baseline and model interpretation of prepared evidence provide additional comparisons. Every arm produces the same `report.json` and `report.md` contract.

**The included examples and offline model runners are synthetic mocks. They test the harness, not a model, and support no claim about a winner.** Real model suites are launched by the operator later, through existing Codex, Amp, or Cursor subscription access. The harness has no model SDK, provider API client, API-key requirement, spending cap, or quota-conservation policy. Quota exhaustion is a retained outcome. It never switches a failed subscription run to separately billed inference.

The unit of comparison is **host + model configuration + prompt breadth + execution style**. Natural host routing and helper requests are valid behavior to observe. Shared fixtures and scoring make the task consistent; they do not remove differences in host prompts, tools, context, routing, or caches.

## Quick start: entirely offline

Use Python 3.11 or newer on macOS or Linux. The checkout runner needs only the Python standard library and no installation or network access. Run these commands from this directory:

```sh
python3 --version
python3 cronbench verify
python3 -m unittest discover -s tests -v
python3 cronbench plan --config configs/offline.json --out runs/demo
python3 cronbench run --study runs/demo --mode offline
python3 cronbench status --study runs/demo
python3 cronbench aggregate --study runs/demo
python3 cronbench review-export --study runs/demo --out exports/review
```

`plan` fixes the randomized run order, configuration, fixture split, repeated runs, and integrity manifest. An existing study is resumed, not replanned in place. Running `run` again skips completed attempts. To retain a new attempt for failed or nonpassing runs:

```sh
python3 cronbench run --study runs/demo --mode offline --retry-failed
python3 cronbench aggregate --study runs/demo
```

The supplied offline configuration plans **210 runs**: seven cells × six development fixtures × five repeats. The cells are the deterministic baseline, two prepared-evidence variants, and the four narrow/broad × tool-driven/saved-script combinations. Of these, 30 runs execute the deterministic baseline and 180 use synthetic mocks.

See [synthetic example outputs](examples/README.md) and the [release verification record](docs/verification.md).

`--limit N` limits how many attempts a command launches, which is useful for checking an adapter. It is an operational batch size, not a token or spending gate. A process timeout prevents hangs. There is no automatic “retry until success”; every attempt remains in the results.

For a local command installed into a new virtual environment, the supplied installer also works offline:

```sh
python3 scripts/install.py --venv .venv
.venv/bin/cronbench verify
```

This launcher points at this checkout, including its fixtures and schemas. Keep the checkout in place, or install again into a new environment after moving it. It is not a standalone wheel that bundles benchmark data.

## What the five arms do

| Arm | Prompt breadth | Execution style | Work performed |
| --- | --- | --- | --- |
| A | None | `deterministic_pipeline` | Fixed fetch, validate, calculate, and template; zero runtime LLM |
| B | Narrow and broad variants | `prepared_evidence` | Model interprets deterministically prepared evidence |
| C | Narrow | `tool_driven` | Agent follows an explicit procedural checklist and invokes tools |
| D | Broad | `tool_driven` | Agent pursues the reporting goal with the same low-level tools |
| E | Narrow and broad variants | `saved_script` | Agent invokes A through the `saved-report` tool |

A–D share the same source data, validation, arithmetic, and rendering capabilities. Only E receives the complete-report shortcut. Pair C with E-narrow and D with E-broad to examine execution style; pair C with D and E-narrow with E-broad to examine prompt breadth. B supplies a secondary narrow/broad comparison and preserves the prepared numeric fields. It does not require exactly one request. Request counts, helper use, and opaque routing remain observations rather than compliance tests.

C and D must invoke the supplied low-level tools; shell access is the portable tool transport. Fixtures include ordinary growth, decline, quiet changes, zero denominators, incomplete data, and a recoverable source failure. Example runs start fresh contexts. A process launched by hand is not evidence of scheduling; a `scheduled` invocation needs retained schedule evidence.

## Configure the factors

Select treatment factors directly in each `targets` entry. For the main four-cell comparison, a manual host target can use:

```json
{
  "id": "my-host-main-comparison",
  "host": "codex",
  "runner": "manual",
  "requested_model": "REPLACE_WITH_AVAILABLE_SELECTOR",
  "configured_main_model": "REPLACE_WITH_AVAILABLE_SELECTOR",
  "configured_auxiliary_models": null,
  "routing_mode": "host_native_opaque",
  "invocation_mode": "fresh_context",
  "execution_styles": ["tool_driven", "saved_script"],
  "prompt_breadths": ["narrow", "broad"]
}
```

Add `"prepared_evidence"` to `execution_styles` for B's two secondary cells. Put the baseline in a separate `runner: "baseline"` target with `execution_styles: ["deterministic_pipeline"]`, `prompt_breadths: ["none"]`, and no model. The other runner types are `manual`, `command`, and `mock`. Configure known auxiliary models explicitly; leave the list null when the host does not expose them.

The planner derives A–E arm labels from those factors. Older `arms` configurations remain accepted, but `arms` and `execution_styles` must not be supplied together. Use the factor fields for new studies, and inspect the generated plan before executing it. `repeats`, `seed`, `split`, and optional `fixtures` selection belong at the top level of the configuration. A target/fixture/repeat shares a `pair_id` across its treatment cells, making matched comparisons possible without pairing unrelated hosts.

## Run with subscription hosts

Read [host-specific briefs and verified interface limits](docs/hosts.md) before choosing an available model. Examples are configurations, not promises of account entitlement or fixed model availability. Fill in the actual selector supported by the host, record configuration and authentication route, and keep real suites separate from the offline demo.

The most portable integration is export/import:

```sh
python3 cronbench plan --config configs/subscription.example.json --out runs/subscription
python3 cronbench status --study runs/subscription
```

Choose a run ID from that study and export its fresh attempt:

```sh
RUN_ID="replace-with-planned-run-id"
python3 cronbench export --study runs/subscription --run-id "$RUN_ID"
```

The command reports the packet directory. Give that directory and `prompt.md` to a new host conversation. Run the assigned arm, retain its outputs and host exports, and copy `metadata.template.json` to a separate `metadata.json` file before filling verified fields. Keep absent values `null`. Import using the attempt number printed by export:

```sh
ATTEMPT=1
METADATA="/absolute/path/to/metadata.json"
python3 cronbench import --study runs/subscription --run-id "$RUN_ID" \
  --attempt "$ATTEMPT" --metadata "$METADATA"
python3 cronbench aggregate --study runs/subscription
```

Add `--usage-artifact /absolute/path/to/host-events.jsonl` for a supported documented usage export. Unsupported host formats do not become invented measurements: use canonical metadata with provenance when exported counters are available, or leave them unknown. See the [runner protocol](docs/runner-protocol.md) for packet contents, metadata semantics, tool commands, failure import, and command adapters.

The subscription example also contains A. Run `python3 cronbench run --study runs/subscription --mode offline` to execute its deterministic baseline; manual targets remain pending for export/import.

`configs/command.example.json` illustrates the command runner. Use a reviewed command or local adapter and the host's existing subscription authentication. After configuring the command:

```sh
python3 cronbench plan --config configs/command.example.json --out runs/command
python3 cronbench run --study runs/command --mode command
```

The harness does not prove a host's billing route from a configuration label. Record the host's observable route and retain a failure when the intended subscription route is unavailable. Do not add API keys or enable extra billing to make the experiment run.

## Results and review

Every finalized attempt has an immutable `record.json`, raw artifacts, checksums, usage provenance, scoring components, timing, and any failures. `results.jsonl` collects retained attempts for analysis. The aggregate distinguishes planned runs, attempts, passing results, failures, missing measurements, retries, and treatment verification. Missing cost or usage is not a zero-cost run.

The default aggregate is written to `runs/demo/summary/aggregate.json` and `aggregate.md` for the quick-start study. Review export writes reports and `ratings.csv` to `exports/review`; its private mapping is `runs/demo/review-key.private.json`. Give reviewers the export directory only. Choose a new empty export directory after adding attempts so an earlier review set is not mixed with new IDs.

Automated scoring checks structure, arithmetic, structured evidence, predefined material-change coverage, missing-data treatment, bounded unsupported-claim patterns, and agreement between JSON and Markdown. It is not a semantic oracle. Export blinded reports for human judgments of support, usefulness, restraint, and next checks; keep the reviewer-to-run mapping private. See [study design and analysis rules](docs/study-design.md).

The dated [pricing table](pricing/prices.json) estimates **API-dollar equivalents**, not subscription charges. Rates, rate scope, actual-model evidence, cache semantics, and missing usage can make an estimate unavailable or conditional. The deterministic baseline's zero tokens are known by construction; that does not include electricity, local compute, development, or human work. Projections for 4, 13, and 52 weekly reports carry their assumptions and do not convert a monthly subscription fee into a token price.

## Reproducibility and held-out data

The versioned fixtures, schemas, prompts, scorer, shared runtime, and pricing table are covered by `manifest.json`. Run `verify` before planning or resuming. For an intentional benchmark change, inspect the diff, regenerate the manifest, and commit both together:

```sh
python3 cronbench manifest
python3 cronbench verify
```

Do not regenerate a manifest to make an old study silently accept changed inputs. Create a new study or restore the original checkout version.

The evaluated packet omits scoring code, scoring keys, and other fixtures. A directory boundary cannot stop an unrestricted agent from reading the controller checkout. Use a restricted filesystem root or separate environment for held-out evaluation, and record the isolation policy. Publishing held-out fixtures makes them public; they are held out from development runs, not permanently secret. Future confirmatory studies need a newly withheld fixture version.

## Project layout

```text
cronbench                 Checkout CLI launcher
src/cronbench/            Controller, tools, scorer, usage, costs, aggregation
fixtures/development/    Fixtures for implementation and pilot testing
fixtures/heldout/        Separate fixture split for evaluation
schemas/                 Shared report and tool contracts
prompts/                 Common instructions and arm treatments
configs/                 Offline, subscription, and command examples
pricing/                 Dated sourced API-equivalent rate table
examples/                Clearly labeled synthetic example artifacts
tests/                   Offline regression tests
docs/                    Study, protocol, and host briefs
runs/                    Local plans, packets, retained attempts (ignored)
exports/                 Local review exports (ignored)
```

Before sharing results, inspect host exports for account details and private paths, and keep private reviewer mappings out of public artifacts. The fixture data and included example reports are synthetic; real model study results are published separately below.

## Published studies

The example mocks above remain synthetic plumbing checks. Separately, the [OpenAI/Amp development pilot (2026-10-08)](studies/openai-amp-development-20261008/README.md) records 78 real executions over synthetic development fixtures, including official automated results, per-run measurements, scoring caveats, and a blinded review bundle. It is a small host/configuration comparison, not a general model leaderboard; human usefulness review remains outstanding.
