"""Blinded human review export; no model judge is required or called."""
import csv
import hashlib
import random
import shutil
from pathlib import Path

from .runner import collect_records, read_json, write_json


def export_review(study, out):
    study, out = Path(study).resolve(), Path(out).resolve()
    if out.exists() and any(out.iterdir()):
        raise ValueError("Review output must be empty to avoid mixing blind identities")
    out.mkdir(parents=True, exist_ok=True)
    plan = read_json(study / "plan.json")
    rows = collect_records(study)
    seed = int(hashlib.sha256((plan["study_id"] + "review-v1").encode()).hexdigest(), 16)
    random.Random(seed).shuffle(rows)
    mapping, rubric = [], []
    for index, row in enumerate(rows, 1):
        blind = f"review-{index:04d}"
        attempt = study / "runs" / row["run_id"] / f"attempt-{row['attempt']:03d}"
        packet = attempt / "packet"
        dest = out / blind
        dest.mkdir()
        available = []
        for name in ("report.json", "report.md", "fixture.json"):
            if (packet / name).exists():
                shutil.copyfile(packet / name, dest / name)
                available.append(name)
        if "report.json" not in available:
            (dest / "NO_REPORT.txt").write_text("No report was produced for this attempt. Retained to avoid survivorship bias.\n")
        mapping.append({"blind_id": blind, "run_id": row["run_id"], "attempt": row["attempt"], "host": row["host"],
                        "requested_model": row.get("requested_model"), "actual_model": row.get("actual_model"), "arm": row["arm"], "status": row["status"]})
        rubric.append({"blind_id": blind, "usefulness_1_to_5": "", "prioritization_1_to_5": "", "clarity_1_to_5": "",
                       "unsupported_prose_claims": "", "notes": ""})
    write_json(study / "review-key.private.json", mapping)
    with (out / "ratings.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rubric[0]) if rubric else ["blind_id", "notes"])
        writer.writeheader()
        writer.writerows(rubric)
    (out / "README.md").write_text("# Blinded human review\n\nRate each report against its synthetic fixture. Do not access the controller or mapping key.\n\nUsefulness: 1 unusable, 3 usable with edits, 5 immediately useful. Prioritization: 1 misses major issues, 3 mixed, 5 selects the most relevant evidence. Clarity: 1 confusing, 3 understandable, 5 concise and precise. Flag unsupported causal explanations, recommendations, or numeric prose even if machine scoring passed. Retain missing reports. Two independent reviewers are preferable; reconcile disagreement after ratings. Content may reveal treatment through writing style; this is metadata blinding, not guaranteed anonymity.\n")
    return {"reports": len(rows), "export": str(out), "private_key": str(study / "review-key.private.json")}
