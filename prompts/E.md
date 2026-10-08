# Arm E: saved-script orchestration agent

Produce the shared weekly analytics report by invoking the available complete
deterministic pipeline as a saved tool: `python tool.py saved-report`. That script
performs source fetch, recovery, validation, calculations, finding selection, and
canonical rendering. Return its generated `report.json` and `report.md` paths.
Report any tool failure honestly. This arm measures the host/model orchestration
overhead of invoking the same complete pipeline used by arm A.
