# Shared task and output contract, version 1.0

Produce a weekly analytics report from the provided synthetic Search Console and
PostHog fixture. This task uses no live customer data. Do not send messages, access
live services, or publish anything. Work only in the supplied run packet. Do not
inspect other fixture packets, the harness checkout, reference answers, scoring
code, host history, or previous runs. These instructions provide procedural
isolation, not an operating-system sandbox.

Write `report.json` matching `report.schema.json`. Then invoke
`python tool.py render` to create the identical canonical `report.md` format used
by every arm. Rendering performs no analysis or narrative generation. The output
must include:

- The provided schema version, fixture ID, and reporting periods.
- Separate source-specific KPI blocks, completeness metadata, previous and
  current values, absolute changes, percentage changes, units, statuses, and
  evidence references. Include every KPI exposed by the calculation tool.
- A short summary and up to three prioritized, evidence-backed findings.
- Limitations and practical next checks. Insufficient evidence is a valid finding.

Search Console clicks and PostHog sessions measure different populations. Do not
substitute, add, or equate them. CTR is clicks divided by impressions;
conversion_rate is conversions divided by sessions. Ratio values are fractions
(for example, `0.05`), while `wow_pct` is a percentage (for example, `20`). Changes
are current minus previous; percentage changes divide that difference by the
previous value. Zero baselines produce null percentage changes. Missing values
remain null. If either week has fewer than seven observed days, absolute and
percentage changes are withheld as null. Never replace unavailable values with
zero, infinity, an extrapolation, or a claim of complete coverage.

Findings contain `id`, `kind` (`change` or `insufficient_evidence`), `source`,
`metric`, `statement`, `evidence_refs`, and `claims` (`[{"ref": "...", "value":
123}]`). Use references exactly as supplied by `evidence.json`: for example,
`search_console.clicks.wow_pct`. Every reference in a finding must be supported
by a corresponding structured claim and belong to that finding's source and
metric. A `change` finding requires a comparable percentage change and a claim
for its `wow_pct`. An `insufficient_evidence` finding must concern a KPI whose
comparison status is incomplete, missing, or zero_baseline. Each numeric value
written in a finding's prose must also be covered by its structured claims;
preserve the calculation tool's precision. Do not infer causes from aggregate
weekly counts. Suggest additional investigation as a next check instead.

Include limitations with codes `synthetic_data` and `source_distinction`, each
with `source: null`. Include all warnings from `evidence.json` as limitations,
preserving their `code` and `source`, and explaining their effect. Limitation
objects have `code`, `source` (source name or null), and `detail`. `next_checks`
is a nonempty array of text.

Tool interfaces are described in `tools.schema.json`. A source tool can have a
recoverable error; another invocation of the same fetch is permitted. Record an
unrecoverable failure honestly through the runner instead of inventing data.
Do not infer or invent token usage, cache usage, reasoning tokens, model IDs,
charges, or tool provenance. The outer harness records that metadata separately.

Follow the run's assigned breadth instruction when interpreting evidence. Use the
host's natural request and model-routing behavior. Available request counts and
routing metadata are recorded as observations; extra requests do not constitute
noncompliance or a scoring failure.

Output quality is assessed using deterministic structured checks plus a separate
blinded human review of prose support, prioritization, and usefulness. The same
fixture and contract do not remove host context, tool, routing, or subscription
confounds.
