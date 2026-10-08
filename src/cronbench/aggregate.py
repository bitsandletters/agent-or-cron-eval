"""Aggregate immutable attempts without hiding failures or missing usage."""

from __future__ import annotations

import json
import math
import statistics
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping
from typing import Any

from .costs import estimate_cost
from .usage import USAGE_FIELDS, normalize_usage


def _number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _stats(values: list[Any]) -> dict[str, Any]:
    known = sorted(float(value) for value in values if _number(value) and value >= 0)
    if not known:
        return {"observed": 0, "missing": len(values), "mean": None, "median": None, "p95": None, "min": None, "max": None, "population_stdev": None}
    position = (len(known) - 1) * 0.95
    lower = int(position)
    p95 = known[lower] + (known[min(lower + 1, len(known) - 1)] - known[lower]) * (position - lower)
    return {
        "observed": len(known),
        "missing": len(values) - len(known),
        "mean": statistics.fmean(known),
        "median": statistics.median(known),
        "p95": p95,
        "min": known[0],
        "max": known[-1],
        "population_stdev": statistics.pstdev(known),
    }


def _coverage(values: list[int | float | None]) -> dict[str, Any]:
    known = [value for value in values if value is not None]
    return {
        "observed": len(known),
        "missing": len(values) - len(known),
        "known_sum": sum(known) if known else None,
        "complete_sum": sum(known) if known and len(known) == len(values) else None,
    }


def _passed(record: Mapping[str, Any]) -> bool:
    score = record.get("score")
    return record.get("status") == "completed" and isinstance(score, dict) and score.get("passed") is True


def _outcomes(records: list[dict[str, Any]]) -> dict[str, Any]:
    status_counts = dict(sorted(Counter(record.get("status", "unknown") for record in records).items()))
    scored = [record["score"] for record in records if isinstance(record.get("score"), dict)]
    scores = [score.get("score") for score in scored]
    passing = sum(_passed(record) for record in records)
    metric_values: dict[str, list[Any]] = defaultdict(list)
    for score in scored:
        for key, value in (score.get("metrics") or {}).items():
            if _number(value):
                metric_values[key].append(value)
    return {
        "count": len(records),
        "status_counts": status_counts,
        "completion_rate": status_counts.get("completed", 0) / len(records) if records else None,
        "execution_failure_rate": sum(record.get("status") != "completed" for record in records) / len(records) if records else None,
        "scored_count": len(scored),
        "passing_count": passing,
        "pass_rate": passing / len(records) if records else None,
        "scored_pass_rate": passing / len(scored) if scored else None,
        "score": _stats(scores),
        "metrics": {key: _stats(values) for key, values in sorted(metric_values.items())},
        "latency_seconds": _stats([record.get("latency_seconds") for record in records]),
        "setup_seconds": _stats([record.get("setup_seconds") for record in records]),
    }


def _identity(record: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "host": record.get("host"),
        "requested_model": record.get("requested_model"),
        "actual_model": record.get("actual_model"),
        "configuration": record.get("configuration", {}),
        "arm": record.get("arm"),
        "split": record.get("split"),
        "cache_state": record.get("cache_state", "unknown"),
        "mock": record.get("mock"),
        "factors": record.get("factors", {}),
        "configured_main_model": record.get("configured_main_model"),
        "configured_auxiliary_models": record.get("configured_auxiliary_models"),
        "observed_models": record.get("observed_models"),
        "routing_mode": record.get("routing_mode", "unknown"),
        "invocation_mode": record.get("invocation_mode", "unknown"),
    }


def _key(record: Mapping[str, Any]) -> str:
    return json.dumps(_identity(record), sort_keys=True, separators=(",", ":"), allow_nan=False)


def _summary(
    attempts: list[dict[str, Any]],
    final: list[dict[str, Any]],
    pricing: Mapping[str, Any],
    first: list[dict[str, Any]],
) -> dict[str, Any]:
    usages = [normalize_usage(record.get("usage")) for record in attempts]
    runtime_costs = [estimate_cost(record.get("usage"), record.get("actual_model"), pricing) for record in attempts]
    setup_costs = [estimate_cost(record.get("setup_usage"), record.get("setup_actual_model", record.get("actual_model")), pricing) for record in attempts]
    runtime_coverage = _coverage([cost["total_usd"] for cost in runtime_costs])
    setup_coverage = _coverage([cost["total_usd"] for cost in setup_costs])
    total_cost = runtime_coverage["complete_sum"]
    passing = sum(_passed(record) for record in final)
    per_scheduled_report = total_cost / len(final) if total_cost is not None and final else None
    histories: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in attempts:
        histories[record["run_id"]].append(record)
    run_latencies = []
    for record in final:
        values = [attempt.get("latency_seconds") for attempt in histories[record["run_id"]]]
        run_latencies.append(sum(values) if values and all(_number(value) and value >= 0 for value in values) else None)
    projections = []
    for count in (4, 13, 52):
        projections.append(
            {
                "weekly_reports": count,
                "weeks": count,
                "runtime_api_equivalent_usd": per_scheduled_report * count if per_scheduled_report is not None else None,
                "assumptions": [
                    "One report per week with this observed fixture/model/configuration mix.",
                    "Observed attempt and retry pattern repeats; all recorded attempts are included.",
                    "Same configured prices and cache mix; setup costs are excluded and shown separately.",
                    "Not a forecast of subscription charges; no allowance for future model or price changes.",
                ],
            }
        )
    return {
        "attempts": _outcomes(attempts),
        "first_attempts": _outcomes(first),
        "final_runs": _outcomes(final),
        "retried_run_count": sum(len(history) > 1 for history in histories.values()),
        "additional_attempt_count": sum(max(0, len(history) - 1) for history in histories.values()),
        "total_attempt_latency_per_final_run_seconds": _stats(run_latencies),
        "fixture_counts": dict(sorted(Counter(record.get("fixture_id", "unknown") for record in final).items())),
        "repeat_values": sorted({record["repeat"] for record in final if isinstance(record.get("repeat"), int)}),
        "usage": {key: _coverage([usage[key] for usage in usages]) for key in USAGE_FIELDS},
        "usage_provenance_counts": dict(sorted(Counter(usage["provenance"] for usage in usages).items())),
        "tool_count": _coverage([record.get("tool_count") for record in attempts]),
        "runtime_api_equivalent_usd": runtime_coverage,
        "runtime_known_partial_subtotal_usd": _coverage([cost["known_subtotal_usd"] for cost in runtime_costs]),
        "setup_api_equivalent_usd": setup_coverage,
        "conditional_pricing_attempt_count": sum(cost["conditional"] for cost in runtime_costs),
        "runtime_api_equivalent_cost_per_passing_report_usd": total_cost / passing if total_cost is not None and passing else None,
        "runtime_api_equivalent_cost_per_scheduled_report_usd": per_scheduled_report,
        "weekly_projections": projections,
    }


def aggregate(records: Iterable[Mapping[str, Any]], pricing: Mapping[str, Any]) -> dict[str, Any]:
    """Group host + actual/requested model + configuration + arm + cache + split.

    A run's final outcome is its greatest recorded attempt number. Every attempt
    still counts toward latency/usage/cost and failure summaries. Duplicate IDs
    are rejected rather than silently double counted. Missing earlier artifacts
    are reported; they cannot be reconstructed or priced.
    """
    attempts = [dict(record) for record in records]
    seen: set[tuple[str, int]] = set()
    by_run: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in attempts:
        run_id, attempt = record.get("run_id"), record.get("attempt")
        if not isinstance(run_id, str) or not run_id:
            raise ValueError("Every attempt requires a nonempty run_id")
        if isinstance(attempt, bool) or not isinstance(attempt, int) or attempt < 1:
            raise ValueError("Every attempt requires an integer attempt >= 1")
        identity = (run_id, attempt)
        if identity in seen:
            raise ValueError(f"Duplicate attempt: {run_id}/{attempt}")
        seen.add(identity)
        by_run[run_id].append(record)
    attempts.sort(key=lambda record: (record["run_id"], record["attempt"]))
    final = [max(history, key=lambda record: record["attempt"]) for _, history in sorted(by_run.items())]
    first = [record for record in attempts if record["attempt"] == 1]
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    final_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    first_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in attempts:
        groups[_key(record)].append(record)
    for record in final:
        final_groups[_key(record)].append(record)
    for record in first:
        first_groups[_key(record)].append(record)
    incomplete_history = []
    for run_id, history in sorted(by_run.items()):
        observed = sorted(record["attempt"] for record in history)
        missing = sorted(set(range(1, max(observed) + 1)) - set(observed))
        if missing:
            incomplete_history.append({"run_id": run_id, "missing_attempt_numbers": missing})
    result = {
        "schema_version": "1.0",
        "pricing_as_of": pricing.get("as_of"),
        "notes": [
            "Pass rate includes failed, timeout, protocol-error, quota-exhausted, and unscored final outcomes in its denominator.",
            "First-attempt outcomes include recorded attempt 1 only; final-run outcomes use the greatest recorded attempt number. All attempts remain visible.",
            "Retries never replace earlier attempts in the usage, cost, or attempt-failure totals.",
            "Total attempt latency per final run sums recorded attempts, excludes gaps between retries, and is unknown if any attempt latency or history is missing.",
            "Unknown actual model IDs form a separate group; display names are not inferred model IDs.",
            "Mock, cache state, split, host, requested/actual model, configuration, prompt/execution factors, configured/observed models, routing mode, and invocation mode are separate groups.",
            "Opaque host routing and multiple requests are observed configuration/outcomes, not disqualifications. A single-model price requires verified run-wide token attribution; otherwise actual model and total cost remain unknown.",
            "Overall mixes are descriptive totals, not evidence that different hosts or model configurations are causally comparable.",
            "A known partial subtotal is not a complete cost. Cost per passing report and projections require complete attempt costs.",
            "Canonical input includes cache subsets and canonical output includes reasoning subsets; do not sum these columns together.",
            "Setup cost is unknown unless setup_usage was explicitly recorded; runtime projections exclude setup.",
        ],
        "incomplete_attempt_histories": incomplete_history,
        "overall": _summary(attempts, final, pricing, first),
        "groups": [
            {"identity": json.loads(key), **_summary(group, final_groups.get(key, []), pricing, first_groups.get(key, []))}
            for key, group in sorted(groups.items())
        ],
        "attempt_costs": [
            {
                "run_id": record["run_id"],
                "attempt": record["attempt"],
                "runtime": estimate_cost(record.get("usage"), record.get("actual_model"), pricing),
                "setup": estimate_cost(record.get("setup_usage"), record.get("setup_actual_model", record.get("actual_model")), pricing),
            }
            for record in attempts
        ],
    }
    cross_group_runs = {
        run_id for run_id, history in by_run.items() if len({_key(record) for record in history}) > 1
    }
    for group in result["groups"]:
        run_ids = sorted({record["run_id"] for record in attempts if _identity(record) == group["identity"]})
        group["cross_group_run_ids"] = sorted(set(run_ids) & cross_group_runs)
        if group["cross_group_run_ids"]:
            # A failed attempt with unknown model must not disappear
            # from the denominator of a retry that later acquires metadata.
            group["runtime_api_equivalent_cost_per_passing_report_usd"] = None
            group["runtime_api_equivalent_cost_per_scheduled_report_usd"] = None
            group["total_attempt_latency_per_final_run_seconds"] = _stats([None] * group["final_runs"]["count"])
            for projection in group["weekly_projections"]:
                projection["runtime_api_equivalent_usd"] = None
    if cross_group_runs:
        result["notes"].append("Some retry histories span group identities (for example unknown then known actual model). Group cost-per-report and projections are unavailable for those histories; overall retains every attempt.")
    if incomplete_history:
        result["notes"].append("Some attempt histories are incomplete; totals cover only supplied artifacts and understate any missing attempt consumption.")
        # Even fully priced supplied attempts cannot represent the complete
        # experimental cost when earlier attempts are absent.
        affected = {item["run_id"] for item in incomplete_history}
        summaries = [result["overall"]]
        summaries.extend(
            group for group in result["groups"]
            if any(record["run_id"] in affected and _identity(record) == group["identity"] for record in attempts)
        )
        for summary in summaries:
            summary["runtime_api_equivalent_cost_per_passing_report_usd"] = None
            summary["runtime_api_equivalent_cost_per_scheduled_report_usd"] = None
            summary["total_attempt_latency_per_final_run_seconds"] = _stats([None] * summary["final_runs"]["count"])
            for projection in summary["weekly_projections"]:
                projection["runtime_api_equivalent_usd"] = None
    return result


def render_markdown(summary: Mapping[str, Any]) -> str:
    """Compact descriptive comparison; the JSON remains the full evidence."""
    overall = summary["overall"]
    attempts, final = overall["attempts"], overall["final_runs"]

    def number(value: Any, digits: int = 3) -> str:
        return f"{value:.{digits}f}" if value is not None else "unknown"

    def rate(value: Any) -> str:
        return f"{value:.1%}" if value is not None else "unknown"

    def cell(value: Any) -> str:
        return str(value).replace("|", "\\|").replace("\n", " ")

    lines = [
        "# Evaluation aggregate",
        "",
        "API-equivalent estimates are conditional comparisons, not subscription charges. Mock groups are synthetic harness checks, not model evaluations. Unknown values remain unknown.",
        "",
        f"Recorded {final['count']} final runs and {attempts['count']} attempts, including {overall['additional_attempt_count']} additional attempts and {attempts['status_counts'].get('quota_exhausted', 0)} quota-exhausted attempts.",
        f"Final pass rate: {rate(final['pass_rate'])}. Final execution failure rate: {rate(final['execution_failure_rate'])}.",
        "",
        "| Group | Host / actual model | Arm / prompt | Split / cache | Mock | First pass | Final pass | Attempt failure | Latency median / p95 / sd (s) | API equivalent / passing report |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for index, group in enumerate(summary["groups"], 1):
        identity = group["identity"]
        stats = group["attempts"]["latency_seconds"]
        cost = group["runtime_api_equivalent_cost_per_passing_report_usd"]
        lines.append("| " + " | ".join([
            f"G{index}",
            cell(f"{identity['host']} / {identity['actual_model'] or 'unknown'}"),
            cell(f"{identity['arm']} / {identity['factors'].get('prompt_breadth', 'unknown')}"),
            cell(f"{identity['split']} / {identity['cache_state']}"),
            cell(identity["mock"]),
            f"{group['first_attempts']['passing_count']}/{group['first_attempts']['count']}",
            f"{group['final_runs']['passing_count']}/{group['final_runs']['count']}",
            rate(group["attempts"]["execution_failure_rate"]),
            " / ".join(number(stats[key]) for key in ("median", "p95", "population_stdev")),
            f"${number(cost, 6)}" if cost is not None else "unknown",
        ]) + " |")
    lines.extend(["", "Group configuration and usage coverage:", ""])
    for index, group in enumerate(summary["groups"], 1):
        identity = group["identity"]
        coverage = group["runtime_api_equivalent_usd"]
        lines.append(
            f"- G{index}: requested model `{identity['requested_model']}`, routing `{identity['routing_mode']}`, invocation `{identity['invocation_mode']}`; "
            f"complete cost for {coverage['observed']}/{group['attempts']['count']} attempts; "
            f"factors `{json.dumps(identity['factors'], sort_keys=True)}`; configuration `{json.dumps(identity['configuration'], sort_keys=True)}`."
        )
    lines.extend(["", "Weekly projection of runtime API-equivalent cost:", "", "| Group | 4 reports | 13 reports | 52 reports |", "| --- | --- | --- | --- |"])
    for index, group in enumerate(summary["groups"], 1):
        cells = [f"G{index}"]
        for projection in group["weekly_projections"]:
            value = projection["runtime_api_equivalent_usd"]
            cells.append(f"${number(value, 6)}" if value is not None else "unknown")
        lines.append("| " + " | ".join(cells) + " |")
    lines.extend([
        "",
        "Projection assumptions: one report per week, the observed attempt/retry and fixture mix repeats, the configured prices and cache mix remain unchanged, and setup is excluded. These are arithmetic projections, not forecasts of subscription charges.",
        "",
        "Accounting and comparison limits:",
        "",
    ])
    lines.extend(f"- {note}" for note in summary["notes"])
    lines.extend(["", "See aggregate.json and retained per-attempt artifacts for rates, price dates and sources, partial subtotals, setup costs, detailed score components, configured/observed models, first-attempt outcomes, and unavailable reasons.", ""])
    return "\n".join(lines)
