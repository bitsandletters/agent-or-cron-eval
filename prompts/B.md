# Arm B: prepared evidence with model interpretation

The harness has already fetched, validated, and calculated source data and placed
the complete unranked result in `evidence.json`. Interpret that evidence to produce
`report.json` according to the shared contract and the assigned breadth
instruction. Preserve its periods, completeness, and KPI objects. Select and
describe up to three findings, limitations, and next checks.

Prefer the supplied evidence. The same low-level source-fetch and calculation
tools remain available when you want to validate or refetch it. Use the host's
natural request and model-routing behavior. Request counts, routing, validation,
and refetches are observations recorded by the harness and do not determine
compliance. Invoke `python tool.py render` after writing the final report JSON.
