"""Portable command line; model access always remains with the chosen host."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .aggregate import aggregate, render_markdown
from .review import export_review
from .runner import ROOT, collect_records, create_plan, finalize, load_plan, manifest, prepare_attempt, read_json, run_study, verify, write_json


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("verify", help="Check immutable fixture/protocol/scorer checksums")
    sub.add_parser("manifest", help="Developer only: regenerate checksums after intentional versioned changes")
    plan_parser = sub.add_parser("plan")
    plan_parser.add_argument("--config", required=True)
    plan_parser.add_argument("--out", required=True)
    run_parser = sub.add_parser("run")
    run_parser.add_argument("--study", required=True)
    run_parser.add_argument("--mode", choices=("offline", "command"), default="offline")
    run_parser.add_argument("--retry-failed", action="store_true")
    run_parser.add_argument("--limit", type=int)
    status_parser = sub.add_parser("status")
    status_parser.add_argument("--study", required=True)
    export_parser = sub.add_parser("export")
    export_parser.add_argument("--study", required=True)
    export_parser.add_argument("--run-id", required=True)
    import_parser = sub.add_parser("import")
    import_parser.add_argument("--study", required=True)
    import_parser.add_argument("--run-id", required=True)
    import_parser.add_argument("--attempt", type=int, required=True)
    import_parser.add_argument("--metadata", required=True)
    import_parser.add_argument("--usage-artifact")
    aggregate_parser = sub.add_parser("aggregate")
    aggregate_parser.add_argument("--study", required=True)
    aggregate_parser.add_argument("--out")
    review_parser = sub.add_parser("review-export")
    review_parser.add_argument("--study", required=True)
    review_parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "verify":
            result = verify()
        elif args.command == "manifest":
            write_json(ROOT / "manifest.json", manifest())
            result = verify()
        elif args.command == "plan":
            plan = create_plan(args.config, args.out)
            result = {"study_id": plan["study_id"], "runs": len(plan["runs"]), "path": str(Path(args.out).resolve())}
        elif args.command == "run":
            if args.limit is not None and args.limit < 1:
                raise ValueError("--limit must be positive")
            records = run_study(args.study, args.mode, args.retry_failed, args.limit)
            result = {"executed": len(records), "outcomes": [{"run_id": r["run_id"], "attempt": r["attempt"], "status": r["status"], "passed": (r.get("score") or {}).get("passed")} for r in records]}
        elif args.command == "status":
            plan = load_plan(args.study)
            records = collect_records(args.study)
            latest = {}
            for row in records:
                if row["attempt"] > latest.get(row["run_id"], {}).get("attempt", 0):
                    latest[row["run_id"]] = row
            result = {"study_id": plan["study_id"], "planned": len(plan["runs"]), "recorded_attempts": len(records),
                      "runs": [{"run_id": r["run_id"], "arm": r["arm"], "target": r["target"]["id"],
                                "fixture": r["fixture_id"], "repeat": r["repeat"], "factors": r["factors"], "pair_id": r["pair_id"],
                                "status": latest.get(r["run_id"], {}).get("status", "pending_or_awaiting_import")} for r in plan["runs"]]}
        elif args.command == "export":
            attempt_dir = prepare_attempt(args.study, args.run_id)
            result = {"attempt": read_json(attempt_dir / "attempt.json")["attempt"], "packet": str(attempt_dir / "packet"),
                      "instruction": "Open only this packet in a fresh host context. Follow prompt.md; import verified metadata afterward."}
        elif args.command == "import":
            attempt_dir = Path(args.study) / "runs" / args.run_id / f"attempt-{args.attempt:03d}"
            result = finalize(args.study, attempt_dir, read_json(args.metadata), usage_artifact=args.usage_artifact)
        elif args.command == "aggregate":
            plan = load_plan(args.study)
            records = collect_records(args.study)
            result = aggregate(records, read_json(ROOT / "pricing/prices.json"))
            result["study_completion"] = {"planned_runs": len(plan["runs"]), "finalized_runs": len({r["run_id"] for r in records}),
                                          "pending_runs": len(plan["runs"]) - len({r["run_id"] for r in records})}
            out = Path(args.out) if args.out else Path(args.study) / "summary"
            write_json(out / "aggregate.json", result)
            (out / "aggregate.md").write_text(render_markdown(result))
            result = {"path": str(out.resolve()), "groups": len(result.get("groups", [])), "study_completion": result["study_completion"]}
        elif args.command == "review-export":
            load_plan(args.study)
            result = export_review(args.study, args.out)
        print(json.dumps(result, indent=2, allow_nan=False))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"cronbench: {exc}", file=sys.stderr)
        raise SystemExit(2)


if __name__ == "__main__":
    main()
