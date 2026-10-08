"""Shared, answer-free data validation and arithmetic for every study arm.

This module may be copied into evaluated contexts. It deliberately contains no
finding selection, report construction, scoring thresholds, or scoring keys.
"""
from __future__ import annotations

import copy
import math
from datetime import date
from typing import Any

SCHEMA_VERSION = "1.0"
RAW_METRICS = {
    "search_console": {"clicks": "count", "impressions": "count", "position": "position"},
    "posthog": {"sessions": "count", "users": "count", "conversions": "count"},
}
DERIVED_METRICS = {"search_console": ("ctr", "clicks", "impressions"),
                   "posthog": ("conversion_rate", "conversions", "sessions")}
PERIODS = ("previous", "current")
VALUE_FIELDS = ("previous", "current", "absolute_change", "wow_pct")


def _number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def validate_fixture(fixture: dict) -> None:
    """Raise ValueError for structurally invalid or impossible synthetic input."""
    if not isinstance(fixture, dict) or fixture.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("Unsupported fixture schema_version")
    if not isinstance(fixture.get("fixture_id"), str) or not fixture["fixture_id"]:
        raise ValueError("fixture_id must be a nonempty string")
    for period in PERIODS:
        block = fixture.get("periods", {}).get(period, {})
        try:
            start, end = date.fromisoformat(block["start"]), date.fromisoformat(block["end"])
        except (ValueError, KeyError, TypeError) as exc:
            raise ValueError(f"Invalid dates for {period}") from exc
        if (end - start).days != 6:
            raise ValueError("Each weekly interval must contain seven inclusive days")
    previous_end = date.fromisoformat(fixture["periods"]["previous"]["end"])
    current_start = date.fromisoformat(fixture["periods"]["current"]["start"])
    if (current_start - previous_end).days != 1:
        raise ValueError("Weekly intervals must be contiguous")
    if set(fixture.get("sources", {})) != set(RAW_METRICS):
        raise ValueError("Exactly search_console and posthog sources are required")
    for source, metrics in RAW_METRICS.items():
        block = fixture["sources"][source]
        for period in PERIODS:
            values = block.get(period, {})
            if set(values) != set(metrics):
                raise ValueError(f"Unexpected metrics for {source}.{period}")
            for metric, value in values.items():
                if value is not None and (not _number(value) or value < 0):
                    raise ValueError(f"Invalid value for {source}.{period}.{metric}")
                if value is not None and metrics[metric] == "count" and int(value) != value:
                    raise ValueError("Count metrics must be whole numbers")
            complete = block.get("completeness", {}).get(period, {})
            if complete.get("expected_days") != 7:
                raise ValueError("expected_days must be 7")
            observed = complete.get("observed_days")
            if isinstance(observed, bool) or not isinstance(observed, int) or not 0 <= observed <= 7:
                raise ValueError("observed_days must be an integer in [0,7]")
            if complete.get("reason") is not None and not isinstance(complete["reason"], str):
                raise ValueError("completeness.reason must be null or text")
            if source == "search_console":
                numerator, denominator = values["clicks"], values["impressions"]
            else:
                numerator, denominator = values["conversions"], values["sessions"]
                if values["users"] is not None and denominator is not None and values["users"] > denominator:
                    raise ValueError("Synthetic users cannot exceed sessions")
            if numerator is not None and denominator is not None and numerator > denominator:
                raise ValueError("Synthetic numerator cannot exceed its denominator")
    for source, failures in fixture.get("tool_failures", {}).items():
        if source not in RAW_METRICS or isinstance(failures, bool) or not isinstance(failures, int) or failures < 0:
            raise ValueError("tool_failures must map a source to a nonnegative integer")


def calculate(previous: int | float | None, current: int | float | None,
              *, comparable: bool = True) -> dict:
    """Calculate arithmetic; null means missing or not safely comparable, never zero."""
    for value in (previous, current):
        if value is not None and not _number(value):
            raise ValueError("Calculation operands must be finite numbers or null")
    if not comparable:
        return {"previous": previous, "current": current, "absolute_change": None,
                "wow_pct": None, "status": "incomplete"}
    if previous is None or current is None:
        return {"previous": previous, "current": current, "absolute_change": None,
                "wow_pct": None, "status": "missing"}
    change = current - previous
    return {"previous": previous, "current": current, "absolute_change": round(change, 6),
            "wow_pct": round(change / previous * 100, 6) if previous else None,
            "status": "ok" if previous else "zero_baseline"}


def prepare(fixture: dict) -> dict:
    """Validate source data and expose unranked calculations with stable evidence IDs."""
    validate_fixture(fixture)
    result = {"schema_version": SCHEMA_VERSION, "fixture_id": fixture["fixture_id"],
              "periods": copy.deepcopy(fixture["periods"]), "sources": {},
              "evidence": {}, "warnings": []}
    for source, raw_metrics in RAW_METRICS.items():
        block = fixture["sources"][source]
        comparable = all(block["completeness"][period]["observed_days"] == 7 for period in PERIODS)
        values = {period: copy.deepcopy(block[period]) for period in PERIODS}
        derived, numerator, denominator = DERIVED_METRICS[source]
        for period in PERIODS:
            n, d = values[period][numerator], values[period][denominator]
            values[period][derived] = round(n / d, 9) if n is not None and d is not None and d != 0 else None
        kpis = {}
        for metric, unit in {**raw_metrics, derived: "ratio"}.items():
            value = calculate(values["previous"][metric], values["current"][metric], comparable=comparable)
            value["unit"] = unit
            value["evidence_refs"] = [f"{source}.{metric}.{field}" for field in VALUE_FIELDS]
            kpis[metric] = value
            result["evidence"].update({f"{source}.{metric}.{field}": value[field] for field in VALUE_FIELDS})
        result["sources"][source] = {"completeness": copy.deepcopy(block["completeness"]), "kpis": kpis}
        if not comparable:
            result["warnings"].append({"code": "incomplete_data", "source": source,
                                       "detail": "At least one week has fewer than seven observed days; changes are withheld."})
        if any(block[period][metric] is None for period in PERIODS for metric in raw_metrics):
            result["warnings"].append({"code": "missing_values", "source": source,
                                       "detail": "Source metrics contain null values; do not replace them with zero."})
        if any(values[period][denominator] == 0 for period in PERIODS) or any(kpi["status"] == "zero_baseline" for kpi in kpis.values()):
            result["warnings"].append({"code": "zero_denominator", "source": source,
                                       "detail": "A zero denominator or baseline makes at least one ratio or percentage change undefined."})
    return result
