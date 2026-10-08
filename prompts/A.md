# Arm A: deterministic pipeline

No model is invoked. The harness fetches the two source blocks, retries recoverable
fixture failures, validates inputs, computes KPIs, selects deterministic findings,
and writes `report.json` and canonical `report.md`. This file documents the arm;
it is not a runtime model prompt. Runtime model token usage is measured zero
because no runtime model request occurs.
