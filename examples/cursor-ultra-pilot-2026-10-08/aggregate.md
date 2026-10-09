# Evaluation aggregate

API-equivalent estimates are conditional comparisons, not subscription charges. Mock groups are synthetic harness checks, not model evaluations. Unknown values remain unknown.

Recorded 51 final runs and 51 attempts, including 0 additional attempts and 0 quota-exhausted attempts.
Final pass rate: 62.7%. Final execution failure rate: 0.0%.

| Group | Host / actual model | Arm / prompt | Split / cache | Mock | First pass | Final pass | Attempt failure | Latency median / p95 / sd (s) | API equivalent / passing report |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| G1 | cursor / claude-haiku-5-5 | C / narrow | development / unknown | False | 0/3 | 0/3 | 0.0% | 31.506 / 41.747 / 6.012 | unknown |
| G2 | cursor / claude-haiku-5-5 | D / broad | development / unknown | False | 0/3 | 0/3 | 0.0% | 31.552 / 37.441 / 5.743 | unknown |
| G3 | cursor / claude-haiku-5-5 | E / broad | development / unknown | False | 3/3 | 3/3 | 0.0% | 18.274 / 19.711 / 2.451 | $0.005277 |
| G4 | cursor / claude-haiku-5-5 | E / narrow | development / unknown | False | 3/3 | 3/3 | 0.0% | 16.767 / 21.244 / 3.166 | $0.005848 |
| G5 | cursor / claude-sonnet-5-5 | C / narrow | development / unknown | False | 1/3 | 1/3 | 0.0% | 37.316 / 70.390 / 20.243 | $0.409634 |
| G6 | cursor / claude-sonnet-5-5 | D / broad | development / unknown | False | 1/3 | 1/3 | 0.0% | 36.124 / 43.967 / 5.081 | $0.422115 |
| G7 | cursor / claude-sonnet-5-5 | E / broad | development / unknown | False | 3/3 | 3/3 | 0.0% | 12.903 / 13.847 / 0.665 | $0.066308 |
| G8 | cursor / claude-sonnet-5-5 | E / narrow | development / unknown | False | 3/3 | 3/3 | 0.0% | 15.113 / 16.512 / 1.762 | $0.068390 |
| G9 | cursor / gemini-3.8-flash | C / narrow | development / unknown | False | 1/3 | 1/3 | 0.0% | 212.560 / 262.367 / 44.511 | $0.634053 |
| G10 | cursor / gemini-3.8-flash | D / broad | development / unknown | False | 1/3 | 1/3 | 0.0% | 245.730 / 255.693 / 5.368 | $0.767237 |
| G11 | cursor / gemini-3.8-flash | E / broad | development / unknown | False | 3/3 | 3/3 | 0.0% | 58.576 / 59.228 / 2.335 | $0.077118 |
| G12 | cursor / gemini-3.8-flash | E / narrow | development / unknown | False | 3/3 | 3/3 | 0.0% | 55.123 / 56.155 / 6.384 | $0.077727 |
| G13 | cursor / grok-4.7 | C / narrow | development / unknown | False | 0/3 | 0/3 | 0.0% | 174.962 / 182.588 / 20.143 | unknown |
| G14 | cursor / grok-4.7 | D / broad | development / unknown | False | 1/3 | 1/3 | 0.0% | 173.110 / 173.457 / 12.533 | $1.078190 |
| G15 | cursor / grok-4.7 | E / broad | development / unknown | False | 3/3 | 3/3 | 0.0% | 39.631 / 43.312 / 3.204 | $0.182343 |
| G16 | cursor / grok-4.7 | E / narrow | development / unknown | False | 3/3 | 3/3 | 0.0% | 32.099 / 47.946 / 8.959 | $0.173672 |
| G17 | python / unknown | A / none | development / unknown | False | 3/3 | 3/3 | 0.0% | 0.087 / 0.107 / 0.011 | $0.000000 |

Group configuration and usage coverage:

- G1: requested model `claude-haiku-5-5-high`, routing `host_native_opaque`, invocation `fresh_context`; complete cost for 3/3 attempts; factors `{"execution_style": "tool_driven", "prompt_breadth": "narrow"}`; configuration `{"auth": "Cursor Ultra subscription via agent CLI", "catalog_verified": true, "effort": "high", "host_version": null, "native": {}, "subscription_route": "operator_configured_unverified", "treatment_verified": null}`.
- G2: requested model `claude-haiku-5-5-high`, routing `host_native_opaque`, invocation `fresh_context`; complete cost for 3/3 attempts; factors `{"execution_style": "tool_driven", "prompt_breadth": "broad"}`; configuration `{"auth": "Cursor Ultra subscription via agent CLI", "catalog_verified": true, "effort": "high", "host_version": null, "native": {}, "subscription_route": "operator_configured_unverified", "treatment_verified": null}`.
- G3: requested model `claude-haiku-5-5-high`, routing `host_native_opaque`, invocation `fresh_context`; complete cost for 3/3 attempts; factors `{"execution_style": "saved_script", "prompt_breadth": "broad"}`; configuration `{"auth": "Cursor Ultra subscription via agent CLI", "catalog_verified": true, "effort": "high", "host_version": null, "native": {}, "subscription_route": "operator_configured_unverified", "treatment_verified": null}`.
- G4: requested model `claude-haiku-5-5-high`, routing `host_native_opaque`, invocation `fresh_context`; complete cost for 3/3 attempts; factors `{"execution_style": "saved_script", "prompt_breadth": "narrow"}`; configuration `{"auth": "Cursor Ultra subscription via agent CLI", "catalog_verified": true, "effort": "high", "host_version": null, "native": {}, "subscription_route": "operator_configured_unverified", "treatment_verified": null}`.
- G5: requested model `claude-sonnet-5-5-high`, routing `host_native_opaque`, invocation `fresh_context`; complete cost for 3/3 attempts; factors `{"execution_style": "tool_driven", "prompt_breadth": "narrow"}`; configuration `{"auth": "Cursor Ultra subscription via agent CLI", "catalog_verified": true, "effort": "high", "host_version": null, "native": {}, "subscription_route": "operator_configured_unverified", "treatment_verified": null}`.
- G6: requested model `claude-sonnet-5-5-high`, routing `host_native_opaque`, invocation `fresh_context`; complete cost for 3/3 attempts; factors `{"execution_style": "tool_driven", "prompt_breadth": "broad"}`; configuration `{"auth": "Cursor Ultra subscription via agent CLI", "catalog_verified": true, "effort": "high", "host_version": null, "native": {}, "subscription_route": "operator_configured_unverified", "treatment_verified": null}`.
- G7: requested model `claude-sonnet-5-5-high`, routing `host_native_opaque`, invocation `fresh_context`; complete cost for 3/3 attempts; factors `{"execution_style": "saved_script", "prompt_breadth": "broad"}`; configuration `{"auth": "Cursor Ultra subscription via agent CLI", "catalog_verified": true, "effort": "high", "host_version": null, "native": {}, "subscription_route": "operator_configured_unverified", "treatment_verified": null}`.
- G8: requested model `claude-sonnet-5-5-high`, routing `host_native_opaque`, invocation `fresh_context`; complete cost for 3/3 attempts; factors `{"execution_style": "saved_script", "prompt_breadth": "narrow"}`; configuration `{"auth": "Cursor Ultra subscription via agent CLI", "catalog_verified": true, "effort": "high", "host_version": null, "native": {}, "subscription_route": "operator_configured_unverified", "treatment_verified": null}`.
- G9: requested model `gemini-3.8-flash-high`, routing `host_native_opaque`, invocation `fresh_context`; complete cost for 3/3 attempts; factors `{"execution_style": "tool_driven", "prompt_breadth": "narrow"}`; configuration `{"auth": "Cursor Ultra subscription via agent CLI", "catalog_verified": true, "effort": "high", "host_version": null, "native": {}, "subscription_route": "operator_configured_unverified", "treatment_verified": null}`.
- G10: requested model `gemini-3.8-flash-high`, routing `host_native_opaque`, invocation `fresh_context`; complete cost for 3/3 attempts; factors `{"execution_style": "tool_driven", "prompt_breadth": "broad"}`; configuration `{"auth": "Cursor Ultra subscription via agent CLI", "catalog_verified": true, "effort": "high", "host_version": null, "native": {}, "subscription_route": "operator_configured_unverified", "treatment_verified": null}`.
- G11: requested model `gemini-3.8-flash-high`, routing `host_native_opaque`, invocation `fresh_context`; complete cost for 3/3 attempts; factors `{"execution_style": "saved_script", "prompt_breadth": "broad"}`; configuration `{"auth": "Cursor Ultra subscription via agent CLI", "catalog_verified": true, "effort": "high", "host_version": null, "native": {}, "subscription_route": "operator_configured_unverified", "treatment_verified": null}`.
- G12: requested model `gemini-3.8-flash-high`, routing `host_native_opaque`, invocation `fresh_context`; complete cost for 3/3 attempts; factors `{"execution_style": "saved_script", "prompt_breadth": "narrow"}`; configuration `{"auth": "Cursor Ultra subscription via agent CLI", "catalog_verified": true, "effort": "high", "host_version": null, "native": {}, "subscription_route": "operator_configured_unverified", "treatment_verified": null}`.
- G13: requested model `grok-4.7-high`, routing `host_native_opaque`, invocation `fresh_context`; complete cost for 3/3 attempts; factors `{"execution_style": "tool_driven", "prompt_breadth": "narrow"}`; configuration `{"auth": "Cursor Ultra subscription via agent CLI", "catalog_verified": true, "effort": "high", "host_version": null, "native": {}, "subscription_route": "operator_configured_unverified", "treatment_verified": null}`.
- G14: requested model `grok-4.7-high`, routing `host_native_opaque`, invocation `fresh_context`; complete cost for 3/3 attempts; factors `{"execution_style": "tool_driven", "prompt_breadth": "broad"}`; configuration `{"auth": "Cursor Ultra subscription via agent CLI", "catalog_verified": true, "effort": "high", "host_version": null, "native": {}, "subscription_route": "operator_configured_unverified", "treatment_verified": null}`.
- G15: requested model `grok-4.7-high`, routing `host_native_opaque`, invocation `fresh_context`; complete cost for 3/3 attempts; factors `{"execution_style": "saved_script", "prompt_breadth": "broad"}`; configuration `{"auth": "Cursor Ultra subscription via agent CLI", "catalog_verified": true, "effort": "high", "host_version": null, "native": {}, "subscription_route": "operator_configured_unverified", "treatment_verified": null}`.
- G16: requested model `grok-4.7-high`, routing `host_native_opaque`, invocation `fresh_context`; complete cost for 3/3 attempts; factors `{"execution_style": "saved_script", "prompt_breadth": "narrow"}`; configuration `{"auth": "Cursor Ultra subscription via agent CLI", "catalog_verified": true, "effort": "high", "host_version": null, "native": {}, "subscription_route": "operator_configured_unverified", "treatment_verified": null}`.
- G17: requested model `None`, routing `explicit`, invocation `fresh_context`; complete cost for 3/3 attempts; factors `{"execution_style": "deterministic_pipeline", "prompt_breadth": "none"}`; configuration `{"host_version": null, "native": {}, "pipeline": "v1", "subscription_route": "not_applicable", "treatment_verified": true}`.

Weekly projection of runtime API-equivalent cost:

| Group | 4 reports | 13 reports | 52 reports |
| --- | --- | --- | --- |
| G1 | $0.044385 | $0.144253 | $0.577011 |
| G2 | $0.042791 | $0.139071 | $0.556283 |
| G3 | $0.021107 | $0.068598 | $0.274391 |
| G4 | $0.023392 | $0.076026 | $0.304102 |
| G5 | $0.546179 | $1.775082 | $7.100326 |
| G6 | $0.562820 | $1.829166 | $7.316665 |
| G7 | $0.265233 | $0.862006 | $3.448025 |
| G8 | $0.273561 | $0.889075 | $3.556299 |
| G9 | $0.845404 | $2.747562 | $10.990249 |
| G10 | $1.022983 | $3.324695 | $13.298778 |
| G11 | $0.308471 | $1.002530 | $4.010119 |
| G12 | $0.310909 | $1.010454 | $4.041816 |
| G13 | $1.668915 | $5.423973 | $21.695891 |
| G14 | $1.437587 | $4.672157 | $18.688627 |
| G15 | $0.729373 | $2.370463 | $9.481853 |
| G16 | $0.694688 | $2.257736 | $9.030944 |
| G17 | $0.000000 | $0.000000 | $0.000000 |

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
