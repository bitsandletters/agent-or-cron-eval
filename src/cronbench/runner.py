"""Controller: immutable study plans, fresh packets, offline execution and imports."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import random
import shutil
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone

from .baseline import build_report, render_markdown
from .scoring import score
from .usage import normalize_usage, parse_usage_artifact

VERSION = "1.0"
ROOT = Path(__file__).resolve().parents[2]
EXECUTION_STYLES = {"A": "deterministic_pipeline", "B": "prepared_evidence", "C": "tool_driven", "D": "tool_driven", "E": "saved_script"}
BREADTH_INSTRUCTIONS = {
    "none": "No model prompt is involved in this deterministic pipeline.",
    "narrow": "Use a narrow procedural scope: report source-specific weekly KPIs, identify the largest supported changes, state data limitations, and list concrete validation checks. Follow the assigned execution method and avoid exploring unrelated questions.",
    "broad": "Use a broad goal-directed scope: assess what these weekly analytics tell the operator, decide which evidence matters most, and choose useful follow-up checks. Exercise judgment within the same synthetic data, source distinctions, output contract, and assigned execution method.",
}


def read_json(path):
    return json.loads(Path(path).read_text(), parse_constant=lambda x: (_ for _ in ()).throw(ValueError(f"Invalid JSON {x}")))


def write_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(obj, indent=2, sort_keys=True, allow_nan=False) + "\n")
    temporary.replace(path)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def target_arms(target):
    """Allow configs to name experimental factors directly, with legacy arm aliases."""
    if "execution_styles" not in target:
        return target.get("arms", ["B", "C", "D", "E"])
    if "arms" in target:
        raise ValueError("Choose execution_styles or arms, not both")
    styles = target["execution_styles"]
    if not isinstance(styles, list) or not styles or len(set(styles)) != len(styles):
        raise ValueError("execution_styles must be a nonempty unique list")
    breadths = target.get("prompt_breadths", ["narrow", "broad"])
    if not isinstance(breadths, list) or not breadths or len(set(breadths)) != len(breadths):
        raise ValueError("prompt_breadths must be a nonempty unique list")
    if "deterministic_pipeline" in styles:
        if styles != ["deterministic_pipeline"] or breadths != ["none"]:
            raise ValueError("The deterministic baseline has no prompt breadth and requires a separate target with ['none']")
    elif any(b not in ("narrow", "broad") for b in breadths):
        raise ValueError("Model workflows require narrow or broad prompt breadth")
    arms = []
    for style in styles:
        if style == "tool_driven":
            arms.extend(arm for breadth, arm in (("narrow", "C"), ("broad", "D")) if breadth in breadths)
        elif style in ("deterministic_pipeline", "prepared_evidence", "saved_script"):
            arms.append({"deterministic_pipeline": "A", "prepared_evidence": "B", "saved_script": "E"}[style])
        else:
            raise ValueError("Unknown execution_style")
    if not arms:
        raise ValueError("No meaningful factor combinations selected")
    return arms


def manifest(root=ROOT):
    paths = []
    for directory in ("fixtures", "schemas", "prompts", "src", "pricing"):
        paths.extend(p for p in (root / directory).rglob("*") if p.is_file() and p.suffix in (".json", ".py", ".md", ".txt"))
    return {"version": VERSION, "files": {str(p.relative_to(root)): digest(p) for p in sorted(paths)}}


def verify(root=ROOT):
    expected = read_json(root / "manifest.json")
    actual = manifest(root)
    if expected != actual:
        different = sorted(k for k in set(expected["files"]) | set(actual["files"]) if expected["files"].get(k) != actual["files"].get(k))
        raise ValueError("Fixture/protocol/code integrity mismatch: " + ", ".join(different))
    return {"verified": True, "files": len(actual["files"]), "manifest_sha256": digest(root / "manifest.json")}


def create_plan(config_path, out, root=ROOT):
    verify(root)
    config = read_json(config_path)
    out = Path(out).resolve()
    if (out / "plan.json").exists():
        raise ValueError("Study exists; resume it or choose a new output directory")
    repeats = config.get("repeats", 5)
    if type(repeats) is not int or repeats < 1:
        raise ValueError("repeats must be a positive integer")
    split = config.get("split", "development")
    if split not in ("development", "heldout"):
        raise ValueError("Unknown fixture split")
    fixtures = sorted((root / "fixtures" / split).glob("*.json"))
    if config.get("fixtures"):
        fixtures = [p for p in fixtures if p.stem in config["fixtures"] or read_json(p)["fixture_id"] in config["fixtures"]]
    if not fixtures:
        raise ValueError("No fixtures selected")
    targets = config["targets"]
    if not targets or len({t["id"] for t in targets}) != len(targets):
        raise ValueError("Targets must have unique IDs")
    fingerprint = hashlib.sha256(json.dumps({"config": config, "manifest": digest(root / "manifest.json")}, sort_keys=True).encode()).hexdigest()
    runs = []
    for target in targets:
        if target.get("runner", "manual") not in ("baseline", "mock", "manual", "command"):
            raise ValueError("Unknown runner")
        for arm in target_arms(target):
            if arm not in "ABCDE" or len(arm) != 1:
                raise ValueError("Unknown arm")
            if arm == "A" and target.get("runner") != "baseline":
                raise ValueError("Arm A requires the deterministic baseline runner")
            if target.get("runner") == "baseline" and arm != "A":
                raise ValueError("Baseline runner implements only A")
            for fixture_path in fixtures:
                fixture = read_json(fixture_path)
                for repeat in range(1, repeats + 1):
                    breadths = {"A": ["none"], "C": ["narrow"], "D": ["broad"]}.get(arm, target.get("prompt_breadths", ["narrow", "broad"]))
                    if not isinstance(breadths, list) or not breadths or len(set(breadths)) != len(breadths) or any(b not in ("narrow", "broad", "none") for b in breadths) or (arm != "A" and "none" in breadths):
                        raise ValueError("Invalid prompt_breadths for this treatment")
                    pair = f"{fingerprint}|{target['id']}|{fixture['fixture_id']}|{repeat}"
                    for breadth in breadths:
                        identity = f"{pair}|{arm}|{breadth}"
                        runs.append({"run_id": hashlib.sha256(identity.encode()).hexdigest()[:20], "pair_id": hashlib.sha256(pair.encode()).hexdigest()[:20], "target": target,
                                     "arm": arm, "factors": {"prompt_breadth": breadth, "execution_style": EXECUTION_STYLES[arm]},
                                     "fixture_id": fixture["fixture_id"], "fixture_path": str(fixture_path.relative_to(root)),
                                     "split": split, "repeat": repeat})
    random.Random(config.get("seed", 20261008)).shuffle(runs)
    plan = {"version": VERSION, "created_at": timestamp(), "study_id": fingerprint[:20], "manifest_sha256": digest(root / "manifest.json"),
            "config": config, "runs": runs}
    write_json(out / "plan.json", plan)
    shutil.copyfile(root / "manifest.json", out / "manifest.json")
    return plan


def load_plan(study, root=ROOT):
    verify(root)
    plan = read_json(Path(study) / "plan.json")
    if plan["manifest_sha256"] != digest(root / "manifest.json"):
        raise ValueError("Study protocol differs from this checkout; restore its committed version")
    return plan


def tool(packet, name, source=None):
    args = [sys.executable, str(packet / "tool.py"), name]
    if source:
        args.append(source)
    result = subprocess.run(args, cwd=packet, capture_output=True, text=True, timeout=30, check=False)
    if result.returncode:
        raise RuntimeError(result.stdout.strip() or result.stderr.strip())
    return json.loads(result.stdout)


def prepare_evidence(packet):
    for source in ("search_console", "posthog"):
        for attempt in range(3):
            try:
                tool(packet, "fetch", source)
                break
            except RuntimeError:
                if attempt == 2:
                    raise
    return tool(packet, "calculate")


def prepare_attempt(study, run_id, root=ROOT):
    started = time.monotonic()
    study = Path(study).resolve()
    plan = load_plan(study, root)
    run = next((r for r in plan["runs"] if r["run_id"] == run_id), None)
    if not run:
        raise ValueError("Unknown run ID")
    run_dir = study / "runs" / run_id
    existing = sorted(run_dir.glob("attempt-*/attempt.json"))
    if existing and not (existing[-1].parent / "record.json").exists():
        raise ValueError("An unfinished attempt exists; import or mark it failed before retrying")
    attempt = len(existing) + 1
    attempt_dir = run_dir / f"attempt-{attempt:03d}"
    packet = attempt_dir / "packet"
    packet.mkdir(parents=True)
    shutil.copyfile(root / run["fixture_path"], packet / "fixture.json")
    shutil.copyfile(root / "src/cronbench/runtime.py", packet / "runtime.py")
    shutil.copyfile(root / "src/cronbench/reporting.py", packet / "reporting.py")
    shutil.copyfile(root / "src/cronbench/packet_tool.py", packet / "tool.py")
    for schema in ("report.schema.json", "tools.schema.json"):
        shutil.copyfile(root / "schemas" / schema, packet / schema)
    if run["arm"] == "E":
        source = (root / "src/cronbench/baseline.py").read_text().replace("from .runtime import", "from runtime import").replace("from .reporting import", "from reporting import")
        (packet / "baseline.py").write_text(source)
    common = (root / "prompts/common.md").read_text()
    arm_prompt = (root / "prompts" / f"{run['arm']}.md").read_text()
    prompt = common + "\n\n" + arm_prompt + "\n\n## Prompt breadth: " + run["factors"]["prompt_breadth"] + "\n\n" + BREADTH_INSTRUCTIONS[run["factors"]["prompt_breadth"]] + "\n\nWrite report.json and report.md in this working directory. Use only this packet. Do not inspect the controller repository, scoring code, other fixtures or other runs. Start a fresh conversation; do not resume a previous session.\n"
    (packet / "prompt.md").write_text(prompt)
    write_json(packet / "run.json", {k: run[k] for k in ("run_id", "pair_id", "arm", "factors", "fixture_id", "repeat")})
    setup_seconds = time.monotonic() - started
    prep_started = time.monotonic()
    preparation_error = None
    if run["arm"] == "B":
        try:
            prepare_evidence(packet)
        except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
            preparation_error = str(exc)
    preparation_seconds = time.monotonic() - prep_started if run["arm"] == "B" else 0.0
    metadata = {"status": "completed", "actual_model": None, "actual_model_source": None,
                "usage": normalize_usage({}), "latency_seconds": None, "host_version": None,
                "subscription_route": "unverified", "fresh_context": None, "native_configuration": {},
                "observed_models": None, "observed_models_source": None, "routing_mode": "host_native_opaque",
                "invocation_mode": "fresh_context", "schedule_evidence": None,
                "cache_state": "unknown", "notes": "Populate only verified exported metadata; never infer actual model from requested model."}
    write_json(packet / "metadata.template.json", metadata)
    info = {"run": run, "attempt": attempt, "created_at": timestamp(), "setup_seconds": setup_seconds,
            "preparation_seconds": preparation_seconds, "preparation_error": preparation_error,
            "preparation_tool_event_count": len((packet / "tool_events.jsonl").read_text().splitlines()) if (packet / "tool_events.jsonl").exists() else 0,
            "packet_checksums": {p.name: digest(p) for p in packet.iterdir() if p.is_file() and p.name not in (".tool_state.json", "tool_events.jsonl")}}
    write_json(attempt_dir / "attempt.json", info)
    return attempt_dir


def collect_records(study):
    return [read_json(p) for p in sorted((Path(study) / "runs").glob("*/attempt-*/record.json"))]


def finalize(study, attempt_dir, metadata, root=ROOT, usage_artifact=None):
    study, attempt_dir = Path(study).resolve(), Path(attempt_dir).resolve()
    if not attempt_dir.is_relative_to(study / "runs"):
        raise ValueError("Attempt must be in this study")
    load_plan(study, root)
    if (attempt_dir / "record.json").exists():
        raise ValueError("Attempt already finalized; never overwrite retained outcomes")
    info = read_json(attempt_dir / "attempt.json")
    run, packet = info["run"], attempt_dir / "packet"
    target = run["target"]
    metadata = dict(metadata)
    status = metadata.get("status", "completed")
    if status not in ("completed", "failed", "quota_exhausted", "timeout", "protocol_error"):
        raise ValueError("Unknown status")
    usage = normalize_usage(metadata.get("usage", {}))
    if usage_artifact:
        artifact = Path(usage_artifact)
        artifact_text = artifact.read_text()
        shutil.copyfile(artifact, attempt_dir / "usage.raw.txt")
        usage = parse_usage_artifact(artifact_text, target["host"])
    actual = metadata.get("actual_model")
    if actual and not metadata.get("actual_model_source"):
        raise ValueError("An actual model ID requires an exported source/provenance")
    observed_models = metadata.get("observed_models")
    if observed_models is not None and (not isinstance(observed_models, list) or not all(isinstance(m, str) and m for m in observed_models)):
        raise ValueError("observed_models must be null or a list of exported model identifiers")
    if observed_models and not metadata.get("observed_models_source"):
        raise ValueError("Observed models require an exported source/provenance")
    observation_warnings = []
    if observed_models and len(set(observed_models)) > 1:
        actual = None  # Aggregate tokens cannot be priced as the main model's usage.
        observation_warnings.append("Multiple models observed; aggregate usage has no single-model price attribution")
    elif actual and observed_models and actual not in observed_models:
        actual = None
        observation_warnings.append("Conflicting actual_model and observed_models; actual model attribution is unknown")
    routing_mode = metadata.get("routing_mode", target.get("routing_mode", "explicit" if target["runner"] in ("baseline", "mock") else "host_native_opaque"))
    if routing_mode not in ("explicit", "host_native_opaque", "unknown"):
        raise ValueError("Unknown routing_mode")
    invocation_mode = metadata.get("invocation_mode", target.get("invocation_mode", "fresh_context"))
    if invocation_mode not in ("fresh_context", "scheduled"):
        raise ValueError("Unknown invocation_mode")
    if invocation_mode == "scheduled" and not metadata.get("schedule_evidence"):
        raise ValueError("Actually scheduled invocation requires schedule_evidence")
    if metadata.get("cache_state", "unknown") not in ("cold", "warm", "unknown"):
        raise ValueError("cache_state must be cold, warm, or unknown")
    events = []
    violations = ["Malformed host metadata; raw artifact retained"] if metadata.get("metadata_errors") else []
    trace_complete = True
    if (packet / "tool_events.jsonl").exists():
        for number, line in enumerate((packet / "tool_events.jsonl").read_text(errors="replace").splitlines(), 1):
            if not line.strip():
                continue
            try:
                event = json.loads(line)
                if not isinstance(event, dict) or not isinstance(event.get("tool"), str) or not isinstance(event.get("status"), str):
                    raise ValueError("Expected tool/status strings")
                events.append(event)
            except (ValueError, TypeError):
                trace_complete = False
                violations.append(f"Malformed tool trace at line {number}; raw artifact retained")
    for name, expected in info["packet_checksums"].items():
        if not (packet / name).exists() or digest(packet / name) != expected:
            violations.append(f"Packet input modified: {name}")
    if run["arm"] != "E" and (packet / "baseline.py").exists():
        violations.append("Complete report shortcut introduced outside E")
    treatment = None
    if target["runner"] in ("baseline", "mock"):
        treatment = True
    elif metadata.get("fresh_context") is False:
        violations.append("Context was reused")
        treatment = False
    elif metadata.get("fresh_context") is True:
        treatment = True
    if run["arm"] in ("C", "D", "E") and status == "completed":
        needed = "saved-report" if run["arm"] == "E" else "calculate"
        if not any(event["tool"] == needed and event["status"] == "ok" for event in events):
            violations.append(f"Missing required natural tool evidence: {needed}")
    result_score = None
    if status == "completed":
        try:
            report = read_json(packet / "report.json")
            markdown = (packet / "report.md").read_text()
            result_score = score(report, read_json(root / run["fixture_path"]), markdown)
        except (ValueError, OSError, TypeError, KeyError) as exc:
            status = "protocol_error"
            violations.append(f"Invalid or missing output: {exc}")
    if violations:
        treatment = False
        if status == "completed":
            status = "protocol_error"
    latency = metadata.get("latency_seconds")
    if latency is not None and (type(latency) not in (float, int) or latency < 0):
        raise ValueError("latency_seconds must be nonnegative or null")
    events_known = trace_complete and (bool(events) or target["runner"] in ("baseline", "mock"))
    record = {"version": VERSION, **{k: run[k] for k in ("run_id", "pair_id", "arm", "factors", "fixture_id", "split", "repeat")},
              "attempt": info["attempt"], "target_id": target["id"], "host": target["host"],
              "requested_model": target.get("requested_model"), "actual_model": actual,
              "actual_model_source": metadata.get("actual_model_source") if actual else None,
              "configured_main_model": target.get("configured_main_model", target.get("requested_model")),
              "configured_auxiliary_models": target.get("configured_auxiliary_models"),
              "observed_models": observed_models, "observed_models_source": metadata.get("observed_models_source"),
              "routing_mode": routing_mode, "invocation_mode": invocation_mode, "schedule_evidence": metadata.get("schedule_evidence"),
              "configuration": {**target.get("configuration", {}), "native": metadata.get("native_configuration", {}),
                                "host_version": metadata.get("host_version"), "treatment_verified": treatment,
                                "subscription_route": metadata.get("subscription_route", "unverified")},
              "cache_state": metadata.get("cache_state", "unknown"), "status": status, "score": result_score,
              "usage": usage, "tool_count": len(events) if events_known else None,
              "setup_usage": normalize_usage({"input_tokens": 0, "output_tokens": 0, "cached_input_tokens": 0,
                                               "cache_write_tokens": 0, "reasoning_output_tokens": 0, "request_count": 0,
                                               "provenance": "measured", "source": "deterministic_no_llm"}),
              "setup_actual_model": None,
              "low_level_tool_count": sum(e["tool"] in ("fetch", "calculate") for e in events) if events_known else None,
              "tool_failures": sum(e["status"] != "ok" for e in events) if events_known else None,
              "latency_seconds": latency + info["preparation_seconds"] if latency is not None else None,
              "setup_seconds": info["setup_seconds"], "preparation_seconds": info["preparation_seconds"],
              "mock": target["runner"] == "mock", "treatment_verified": treatment,
              "observation_warnings": observation_warnings, "tool_trace_complete": trace_complete,
              "violations": violations, "failure": metadata.get("failure"), "notes": metadata.get("notes"),
              "metadata_errors": metadata.get("metadata_errors", []),
              "created_at": timestamp(), "manifest_sha256": digest(root / "manifest.json"),
              "artifacts": {str(p.relative_to(attempt_dir)): digest(p) for p in sorted(attempt_dir.rglob("*")) if p.is_file() and "__pycache__" not in p.parts}}
    write_json(attempt_dir / "metadata.imported.json", metadata)
    write_json(attempt_dir / "record.json", record)
    rows = collect_records(study)
    (study / "results.jsonl").write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))
    return record


def execute(study, attempt_dir, root=ROOT):
    info = read_json(attempt_dir / "attempt.json")
    run, packet = info["run"], attempt_dir / "packet"
    target = run["target"]
    runner = target.get("runner", "manual")
    if runner == "manual":
        raise ValueError("Manual runner: use export then import")
    started = time.monotonic()
    metadata = {"status": "completed", "actual_model": None, "fresh_context": True,
                "usage": {}, "subscription_route": "not_applicable"}
    if info.get("preparation_error"):
        return finalize(study, attempt_dir, {"status": "failed", "failure": {"kind": "deterministic_preparation", "message": info["preparation_error"]}}, root)
    if runner in ("baseline", "mock"):
        outcomes = target.get("mock_outcomes", ["completed"])
        outcome = outcomes[min(info["attempt"] - 1, len(outcomes) - 1)] if runner == "mock" else "completed"
        metadata["status"] = outcome
        if outcome == "completed":
            if run["arm"] == "E":
                report = tool(packet, "saved-report")
            else:
                if run["arm"] != "B":
                    prepare_evidence(packet)
                report = build_report(read_json(packet / "fixture.json"))
                if target.get("mock_bad_output"):
                    report["sources"]["search_console"]["kpis"]["clicks"]["current"] += 999
                write_json(packet / "report.json", report)
                (packet / "report.md").write_text(render_markdown(report))
        if runner == "baseline":
            metadata["usage"] = {"input_tokens": 0, "output_tokens": 0, "cached_input_tokens": 0, "cache_write_tokens": 0,
                                 "reasoning_output_tokens": 0, "request_count": 0, "provenance": "measured", "source": "deterministic_no_llm"}
        else:
            # Synthetic usage is explicitly estimated; never evidence about a model.
            metadata["usage"] = {"input_tokens": 1200, "output_tokens": 400, "cached_input_tokens": 0,
                                 "cache_write_tokens": 0, "reasoning_output_tokens": 50,
                                 "request_count": 1 if run["arm"] == "B" else 2, "provenance": "estimated", "source": "synthetic_mock"}
            if target.get("mock_missing_usage"):
                metadata["usage"] = {}
            metadata["notes"] = "SYNTHETIC MOCK: exercises harness only; not a real model evaluation"
        metadata["latency_seconds"] = time.monotonic() - started
    elif runner == "command":
        if target.get("billing_route") != "subscription":
            raise ValueError("Command configuration must state its subscription billing route; API execution is not implemented")
        argv = target.get("argv")
        if not isinstance(argv, list) or not argv or not all(isinstance(x, str) for x in argv):
            raise ValueError("Command runner requires an argv array, never a shell command")
        replacements = {"{packet}": str(packet), "{prompt}": str(packet / "prompt.md"), "{model}": target.get("requested_model") or ""}
        argv = [replace_all(arg, replacements) for arg in argv]
        # API keys are never needed by this harness. Host credentials remain the host's responsibility.
        env = {k: v for k, v in os.environ.items() if k not in {"OPENAI_API_KEY", "ANTHROPIC_API_KEY", "XAI_API_KEY", "CURSOR_API_KEY", "AMP_API_KEY"}}
        with (attempt_dir / "host.stdout.txt").open("w") as stdout, (attempt_dir / "host.stderr.txt").open("w") as stderr:
            process = subprocess.Popen(argv, cwd=packet, stdout=stdout, stderr=stderr, env=env, start_new_session=True)
            try:
                code = process.wait(timeout=target.get("timeout_seconds", 900))
                metadata["status"] = "completed" if code == 0 else "failed"
                if code:
                    metadata["failure"] = {"kind": "process_exit", "returncode": code}
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
                metadata["status"] = "timeout"
                metadata["failure"] = {"kind": "timeout"}
        metadata["latency_seconds"] = time.monotonic() - started
        metadata["subscription_route"] = "operator_configured_unverified"
        metadata["fresh_context"] = None
        if (packet / "metadata.json").exists():
            try:
                imported = read_json(packet / "metadata.json")
                if not isinstance(imported, dict):
                    raise ValueError("Host metadata must be a JSON object")
                # Preserve observed process failures and wall time even when host metadata is incomplete.
                observed_status = metadata["status"]
                imported.pop("latency_seconds", None)
                metadata.update(imported)
                if observed_status in ("timeout", "failed") and metadata.get("status") != "quota_exhausted":
                    metadata["status"] = observed_status
            except (OSError, ValueError, TypeError) as exc:
                if metadata["status"] == "completed":
                    metadata["status"] = "protocol_error"
                metadata["metadata_errors"] = [str(exc)]
                if not metadata.get("failure"):
                    metadata["failure"] = {"kind": "invalid_host_metadata", "message": str(exc)}
        parsed_usage = parse_usage_artifact((attempt_dir / "host.stdout.txt").read_text(), target["host"])
        if parsed_usage["provenance"] != "unavailable" or not metadata.get("usage"):
            metadata["usage"] = parsed_usage
    return finalize(study, attempt_dir, metadata, root)


def replace_all(value, replacements):
    for key, replacement in replacements.items():
        value = value.replace(key, replacement)
    return value


def run_study(study, mode="offline", retry_failed=False, limit=None, root=ROOT):
    plan = load_plan(study, root)
    records = collect_records(study)
    latest = {}
    for record in records:
        if record["attempt"] > latest.get(record["run_id"], {}).get("attempt", 0):
            latest[record["run_id"]] = record
    results = []
    for run in plan["runs"]:
        runner = run["target"].get("runner", "manual")
        if runner == "manual" or (mode == "offline" and runner == "command"):
            continue
        old = latest.get(run["run_id"])
        if old and not (retry_failed and (old["status"] != "completed" or not (old.get("score") or {}).get("passed"))):
            continue
        attempt_dir = prepare_attempt(study, run["run_id"], root)
        try:
            results.append(execute(study, attempt_dir, root))
        except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
            if (attempt_dir / "record.json").exists():
                raise
            results.append(finalize(study, attempt_dir, {"status": "failed", "failure": {"kind": type(exc).__name__, "message": str(exc)}}, root))
        if limit is not None and len(results) >= limit:
            break
    return results
