# Release verification

Local verification on 2026-10-08 used Python 3.14.7 on macOS. No real model requests, live analytics, messages, or report publication were performed.

| Check | Result |
| --- | --- |
| Offline unit/integration tests | 88 passed |
| Seeded fixture regeneration | All 12 committed fixtures match |
| Integrity manifest | All 34 fixture/protocol/runtime/pricing files verified |
| Full offline development matrix | 210/210 passing reports: 30 deterministic + 180 synthetic mocks |
| Resume same completed study | Zero new attempts; retained records unchanged |
| Failure demonstration | Six retained attempts, including one synthetic quota-exhausted attempt, its retry, intentionally bad outputs, and missing usage |
| Clean-copy installation | Standard-library venv launcher works without pip, network, or packages; works outside checkout working directory; protects an existing destination |
| Python compilation | Source, tests, and scripts compile |
| Public release audit | Tracked-file review and pattern scan; history audited before push; no detected credentials, private logs, personal paths, or customer data |

Regression tests include malformed reports, unsupported claims, missing material changes, zero denominators, incomplete data, recoverable tool failure, numeric corruption, unknown token counts, cache/reasoning subset math, unknown hosting prices, repeated fresh packets, stable paired IDs, factor expansion, opaque/mixed routing, actual scheduled provenance, malformed/truncated host artifacts, subprocess timeout, and contradictory model IDs. Multiple or unknown model request counts never disqualify a report.

GitHub Actions runs the same offline checks and matrix on macOS and Linux with Python 3.11 and 3.13. Consult the [workflow](https://github.com/bitsandletters/agent-or-cron-eval/actions/workflows/verify.yml) for the exact commit's current CI result. Local success is separate from CI status.

Host-interface inspection and its limitations are in [hosts.md](hosts.md). CI and the offline matrix above still use synthetic mocks only. A separate, limited-rigor **Cursor Ultra pilot** (real `agent` CLI runs on development fixtures) is published under [`examples/cursor-ultra-pilot-2026-10-08/`](../examples/cursor-ultra-pilot-2026-10-08/); read its README for caveats. The tests do not validate a particular account's entitlement or guarantee complete usage exports. The local packet boundary is not an OS sandbox. Public held-out fixtures need replacement for a later secret confirmatory evaluation.
