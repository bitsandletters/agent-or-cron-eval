#!/usr/bin/env python3
"""Rebuild a study with Cursor usage/cost fields parsed from retained host.stdout.txt.

Leaves the source study immutable. Creates a sibling study whose records carry
measured usage and operator-attested actual_model IDs for pricing. Display names
from the stream are retained as observed_models and are never treated as IDs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cronbench.aggregate import aggregate, render_markdown  # noqa: E402
from cronbench.runner import digest, read_json, timestamp, write_json  # noqa: E402
from cronbench.usage import extract_cursor_display_model, parse_usage_artifact  # noqa: E402

# Operator-attested mapping from Cursor stream display names (this pilot) to
# pricing-table model IDs. Extend deliberately; do not fuzzy-match.
DISPLAY_TO_PRICING_ID = {
    "Grok 4.7 256K High": "grok-4.7",
    "Claude Sonnet 5.5 300K High": "claude-sonnet-5-5",
    "Claude Haiku 5.5 300K High No Thinking": "claude-haiku-5-5",
    "Gemini 3.8 Flash High": "gemini-3.8-flash",
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True, help="Existing study directory")
    parser.add_argument("--out", type=Path, required=True, help="New study directory (must not exist)")
    args = parser.parse_args()
    source = args.source.resolve()
    out = args.out.resolve()
    if not (source / "plan.json").exists():
        raise SystemExit(f"missing plan: {source / 'plan.json'}")
    if out.exists():
        raise SystemExit(f"refusing to overwrite existing study: {out}")

    plan = read_json(source / "plan.json")
    out.mkdir(parents=True)
    shutil.copyfile(ROOT / "manifest.json", out / "manifest.json")
    plan = dict(plan)
    plan["manifest_sha256"] = digest(ROOT / "manifest.json")
    plan["study_id"] = hashlib.sha256(
        json.dumps(
            {"source_study_id": plan.get("study_id"), "backfill": "cursor-usage", "created_at": timestamp()},
            sort_keys=True,
        ).encode()
    ).hexdigest()[:20]
    plan["notes"] = list(plan.get("notes") or []) + [
        "Derivative study: usage and actual_model backfilled from retained Cursor host.stdout.txt.",
        "Original attempt artifacts were copied; scores and reports were not re-executed.",
    ]
    plan["created_at"] = timestamp()
    write_json(out / "plan.json", plan)

    records = []
    for record_path in sorted((source / "runs").glob("*/attempt-*/record.json")):
        attempt_dir = record_path.parent
        rel = attempt_dir.relative_to(source / "runs")
        dest = out / "runs" / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(attempt_dir, dest, dirs_exist_ok=False)
        record = read_json(dest / "record.json")
        stdout = dest / "host.stdout.txt"
        if record.get("host") == "cursor" and stdout.exists():
            text = stdout.read_text(errors="replace")
            usage = parse_usage_artifact(text, "cursor", source="cursor:host.stdout.txt")
            display = extract_cursor_display_model(text)
            actual = DISPLAY_TO_PRICING_ID.get(display) if display else None
            record["usage"] = usage
            if display:
                record["observed_models"] = [display]
                record["observed_models_source"] = "cursor:stream.system.model"
            if actual:
                record["actual_model"] = actual
                record["actual_model_source"] = (
                    f"operator_map:{display!r}->pricing_id from scripts/backfill_cursor_usage.py"
                )
            else:
                record["actual_model"] = None
                record["actual_model_source"] = None
                record.setdefault("observation_warnings", []).append(
                    f"No pricing-ID mapping for Cursor display model {display!r}"
                )
            record["notes"] = ((record.get("notes") or "") + " | usage backfilled from host.stdout.txt").strip(" |")
            write_json(dest / "record.json", record)
            write_json(dest / "usage.backfill.json", {"usage": usage, "display_model": display, "actual_model": actual})
        records.append(record)

    results_path = out / "results.jsonl"
    results_path.write_text("".join(json.dumps(row, sort_keys=True, allow_nan=False) + "\n" for row in records))
    summary = aggregate(records, read_json(ROOT / "pricing/prices.json"))
    summary["study_completion"] = {
        "planned_runs": len(plan["runs"]),
        "finalized_runs": len({r["run_id"] for r in records}),
        "pending_runs": len(plan["runs"]) - len({r["run_id"] for r in records}),
        "backfill_source": str(source),
    }
    summary_dir = out / "summary"
    summary_dir.mkdir(parents=True, exist_ok=True)
    write_json(summary_dir / "aggregate.json", summary)
    (summary_dir / "aggregate.md").write_text(render_markdown(summary))
    print(json.dumps({"out": str(out), "records": len(records), "groups": len(summary.get("groups", []))}, indent=2))


if __name__ == "__main__":
    main()
