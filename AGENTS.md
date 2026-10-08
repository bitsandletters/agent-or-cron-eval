# Working on this harness

This checkout is the evaluation controller. Read README.md and docs/runner-protocol.md before changing the design or running host suites.

- Run offline tests with `python3 -m unittest discover -s tests -v`; verify the manifest and seeded fixtures.
- Use the explicit prompt-breadth and execution-style factors in configs. Request counts and native model routing are observations, never model-call purity gates.
- Evaluate hosts only in exported fresh packets. Do not expose scorer, other fixtures, or previous attempts to the evaluated context. A directory alone is not a security boundary.
- Use the selected host's existing subscription route. Do not add provider API calls, credentials, billing fallbacks, spending caps, or quota-conservation rules.
- Preserve unknown usage and model IDs as null. Retain every failure and retry. Record an actually scheduled invocation only with evidence of scheduling.
- Change frozen fixtures/prompts/scoring intentionally, regenerate manifest.json, and start a new study. Do not retrofit an existing study to new code.
- Keep runs, host logs, credentials, private review keys, and personal paths out of commits. Shared examples must remain explicitly synthetic.

The offline mocks validate plumbing and support no model-quality claim.
