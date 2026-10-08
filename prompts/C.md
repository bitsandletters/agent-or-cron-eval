# Arm C: procedural checklist agent

Follow this checklist in order using the available tools:

1. Invoke `python tool.py fetch search_console`. Retry that fetch if its error is
   recoverable.
2. Invoke `python tool.py fetch posthog`. Retry that fetch if its error is
   recoverable.
3. Invoke `python tool.py calculate` to validate and calculate evidence.
4. Read `evidence.json`, inspect completeness and every KPI, and preserve its
   periods, source coverage, values, units, statuses, and references.
5. Select up to three findings, giving priority to consequential observed changes
   and explaining when a comparison has insufficient evidence. Support each
   finding with numeric references and structured claims.
6. Include required source distinction, synthetic-data, and evidence warnings as
   limitations. Add next checks that could resolve uncertainties without asserting
   unobserved causes.
7. Write `report.json` matching the report schema, then invoke
   `python tool.py render`. Return the generated artifact paths.

Use natural tool invocation in this fresh context. The complete-report saved
script is unavailable in this arm.
