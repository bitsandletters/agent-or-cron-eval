# Evaluation aggregate

API-equivalent estimates are conditional comparisons, not subscription charges. Mock groups are synthetic harness checks, not model evaluations. Unknown values remain unknown.

Recorded 4 final runs and 6 attempts, including 2 additional attempts and 1 quota-exhausted attempts.
Final pass rate: 75.0%. Final execution failure rate: 0.0%.

| Group | Host / actual model | Arm / prompt | Split / cache | Mock | First pass | Final pass | Attempt failure | Latency median / p95 / sd (s) | API equivalent / passing report |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| G1 | offline-mock / unknown | B / broad | development / unknown | True | 1/1 | 1/1 | 0.0% | 0.116 / 0.116 / 0.000 | unknown |
| G2 | offline-mock / unknown | B / narrow | development / unknown | True | 1/1 | 1/1 | 0.0% | 0.107 / 0.107 / 0.000 | unknown |
| G3 | offline-mock / unknown | C / narrow | development / unknown | True | 0/1 | 1/1 | 50.0% | 0.050 / 0.095 / 0.050 | unknown |
| G4 | offline-mock / unknown | D / broad | development / unknown | True | 0/1 | 0/1 | 0.0% | 0.102 / 0.102 / 0.000 | unknown |

Group configuration and usage coverage:

- G1: requested model `None`, routing `explicit`, invocation `fresh_context`; complete cost for 0/1 attempts; factors `{"execution_style": "prepared_evidence", "prompt_breadth": "broad"}`; configuration `{"host_version": null, "native": {}, "subscription_route": "not_applicable", "treatment_verified": true}`.
- G2: requested model `None`, routing `explicit`, invocation `fresh_context`; complete cost for 0/1 attempts; factors `{"execution_style": "prepared_evidence", "prompt_breadth": "narrow"}`; configuration `{"host_version": null, "native": {}, "subscription_route": "not_applicable", "treatment_verified": true}`.
- G3: requested model `None`, routing `explicit`, invocation `fresh_context`; complete cost for 0/2 attempts; factors `{"execution_style": "tool_driven", "prompt_breadth": "narrow"}`; configuration `{"host_version": null, "native": {}, "subscription_route": "not_applicable", "treatment_verified": true}`.
- G4: requested model `None`, routing `explicit`, invocation `fresh_context`; complete cost for 0/2 attempts; factors `{"execution_style": "tool_driven", "prompt_breadth": "broad"}`; configuration `{"host_version": null, "native": {}, "subscription_route": "not_applicable", "treatment_verified": true}`.

Weekly projection of runtime API-equivalent cost:

| Group | 4 reports | 13 reports | 52 reports |
| --- | --- | --- | --- |
| G1 | unknown | unknown | unknown |
| G2 | unknown | unknown | unknown |
| G3 | unknown | unknown | unknown |
| G4 | unknown | unknown | unknown |

Projection assumptions: one report per week, the observed attempt/retry and fixture mix repeats, the configured prices and cache mix remain unchanged, and setup is excluded. These are arithmetic projections, not forecasts of subscription charges.

Accounting and comparison limits:

- Pass rate includes failed, timeout, protocol-error, quota-exhausted, and unscored final outcomes in its denominator.
- First-attempt outcomes include recorded attempt 1 only; final-run outcomes use the greatest recorded attempt number. All attempts remain visible.
- Retries never replace earlier attempts in the usage, cost, or attempt-failure totals.
- Total attempt latency per final run sums recorded attempts, excludes gaps between retries, and is unknown if any attempt latency or history is missing.
- Unknown actual model IDs form a separate group; display names are not inferred model IDs.
- Mock, cache state, split, host, requested/actual model, configuration, prompt/execution factors, configured/observed models, routing mode, and invocation mode are separate groups.
- Opaque host routing and multiple requests are observed configuration/outcomes, not disqualifications. A single-model price requires verified run-wide token attribution; otherwise actual model and total cost remain unknown.
- Overall mixes are descriptive totals, not evidence that different hosts or model configurations are causally comparable.
- A known partial subtotal is not a complete cost. Cost per passing report and projections require complete attempt costs.
- Canonical input includes cache subsets and canonical output includes reasoning subsets; do not sum these columns together.
- Setup cost is unknown unless setup_usage was explicitly recorded; runtime projections exclude setup.

See aggregate.json and retained per-attempt artifacts for rates, price dates and sources, partial subtotals, setup costs, detailed score components, configured/observed models, first-attempt outcomes, and unavailable reasons.
