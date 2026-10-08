"""Public low-level tool executable copied to each fresh evaluation packet."""
import argparse
import json
import time
from pathlib import Path

from runtime import prepare

ROOT = Path(__file__).resolve().parent


def read(name):
    return json.loads((ROOT / name).read_text())


def write(name, value):
    (ROOT / name).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def log(name, arguments, started, result, internal=False):
    with (ROOT / "tool_events.jsonl").open("a") as stream:
        stream.write(json.dumps({"tool": name, "arguments": arguments,
                                 "latency_seconds": time.monotonic() - started,
                                 "status": result, "internal": internal}) + "\n")


def fetch(source, internal=False):
    started = time.monotonic()
    fixture = read("fixture.json")
    if source not in fixture["sources"]:
        raise ValueError("Unknown source")
    state = read(".tool_state.json") if (ROOT / ".tool_state.json").exists() else {"calls": {}, "fetched": {}}
    state["calls"][source] = state["calls"].get(source, 0) + 1
    failures = fixture.get("tool_failures", {}).get(source, 0)
    if state["calls"][source] <= failures:
        write(".tool_state.json", state)
        log("fetch", {"source": source}, started, "recoverable_error", internal)
        raise RuntimeError("Synthetic recoverable source failure; retry is permitted")
    state["fetched"][source] = fixture["sources"][source]
    write(".tool_state.json", state)
    log("fetch", {"source": source}, started, "ok", internal)
    return {"source": source, "data": state["fetched"][source]}


def calculate(internal=False):
    started = time.monotonic()
    fixture = read("fixture.json")
    state = read(".tool_state.json") if (ROOT / ".tool_state.json").exists() else {"fetched": {}}
    if set(state["fetched"]) != set(fixture["sources"]):
        log("calculate", {}, started, "missing_fetch", internal)
        raise RuntimeError("Fetch both sources successfully before calculate")
    fixture["sources"] = state["fetched"]
    result = prepare(fixture)
    write("evidence.json", result)
    log("calculate", {}, started, "ok", internal)
    return result


def pipeline():
    """Only accessible when controller includes baseline.py (arm E)."""
    from baseline import build_report, render_markdown
    started = time.monotonic()
    for source in ("search_console", "posthog"):
        for attempt in range(3):
            try:
                fetch(source, internal=True)
                break
            except RuntimeError:
                if attempt == 2:
                    raise
    calculate(internal=True)
    report = build_report(read("fixture.json"))
    write("report.json", report)
    (ROOT / "report.md").write_text(render_markdown(report))
    log("saved-report", {}, started, "ok")
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("tool", choices=["fetch", "calculate", "render", "saved-report"])
    parser.add_argument("source", nargs="?")
    args = parser.parse_args()
    try:
        if args.tool == "fetch":
            result = fetch(args.source)
        elif args.tool == "calculate":
            result = calculate()
        elif args.tool == "render":
            from reporting import render_markdown
            started = time.monotonic()
            (ROOT / "report.md").write_text(render_markdown(read("report.json")))
            log("render", {}, started, "ok")
            result = {"written": "report.md"}
        elif (ROOT / "baseline.py").exists():
            result = pipeline()
        else:
            raise ValueError("Complete-report shortcut is available only in arm E")
        print(json.dumps(result, allow_nan=False))
    except (ValueError, RuntimeError, OSError) as exc:
        print(json.dumps({"error": str(exc), "recoverable": isinstance(exc, RuntimeError)}))
        raise SystemExit(2)


if __name__ == "__main__":
    main()
