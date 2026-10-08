"""Dated API-equivalent estimates; these are never subscription invoices."""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
from typing import Any

from .usage import normalize_usage


RATE_FIELDS = (
    "input_usd_per_million",
    "output_usd_per_million",
    "cached_input_usd_per_million",
    "cache_write_usd_per_million",
)


def _rate(value: Any) -> Decimal | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = Decimal(str(value))
    except (ValueError, ArithmeticError):
        return None
    return number if number.is_finite() and number >= 0 else None


def _money(value: Decimal | None) -> float | None:
    return round(float(value), 12) if value is not None else None


def _charge(tokens: int | None, rate: Decimal | None) -> Decimal | None:
    if tokens == 0:
        return Decimal(0)
    if tokens is None or rate is None:
        return None
    return Decimal(tokens) * rate / Decimal(1_000_000)


def _match_model(actual_model: str | None, pricing: Mapping[str, Any]) -> dict[str, Any] | None:
    if not actual_model:
        return None
    for row in pricing.get("models", []):
        if not isinstance(row, dict):
            continue
        aliases = row.get("aliases", [])
        if actual_model == row.get("model_id") or (
            isinstance(aliases, list) and actual_model in aliases
        ):
            return row
    return None


def estimate_cost(
    usage: Mapping[str, Any] | None,
    actual_model: str | None,
    pricing: Mapping[str, Any],
) -> dict[str, Any]:
    """Estimate API-equivalent cost from known counters and an actual model ID.

    Never match requested model IDs implicitly. Cache/reasoning are subsets.
    Unknown discount or write counts make the total unavailable unless the
    relevant rate equals the base input rate. A known subtotal is explicitly
    partial and must not be used as a complete cost in aggregates.
    """
    canonical = normalize_usage(usage)
    row = _match_model(actual_model, pricing)
    scope_mismatch = False
    requested_scope = canonical.get("pricing_scope")
    if row is not None and requested_scope is not None and requested_scope != row.get("rate_scope"):
        regime = next(
            (item for item in row.get("alternative_regimes", []) if item.get("rate_scope") == requested_scope),
            None,
        )
        if regime is None:
            scope_mismatch = True
        else:
            row = {**row, **regime, "assumptions": regime.get("assumptions", [f"Explicitly selected pricing regime: {requested_scope}."])}
    result: dict[str, Any] = {
        "currency": "USD",
        "basis": "API-equivalent estimate; not an actual subscription charge",
        "actual_model": actual_model,
        "matched_model": row.get("model_id") if row else None,
        "total_usd": None,
        "known_subtotal_usd": None,
        "actual_subscription_charge_usd": None,
        "usage_provenance": canonical["provenance"],
        "usage_source": canonical["source"],
        "pricing_as_of": row.get("as_of", pricing.get("as_of")) if row else pricing.get("as_of"),
        "pricing_sources": [],
        "rates": {},
        "rate_scope": row.get("rate_scope") if row else None,
        "pricing_scope_verified": False,
        "conditional": True,
        "assumptions": list(pricing.get("assumptions", [])),
        "unavailable_reasons": [],
        "components_usd": {},
    }
    # Deterministic A and explicitly measured no-call setup do not need a model.
    if canonical["input_tokens"] == 0 and canonical["output_tokens"] == 0:
        result.update(total_usd=0.0, known_subtotal_usd=0.0, conditional=False)
        result["assumptions"].append("Explicitly recorded zero input and output tokens; no model rate is needed.")
        result["components_usd"] = {"input": 0.0, "output": 0.0}
        return result
    if pricing.get("currency", "USD") != "USD":
        result["unavailable_reasons"].append("Only USD pricing tables are supported.")
        return result
    if row is None:
        result["unavailable_reasons"].append(
            "Actual model ID is unknown." if not actual_model else "No configured price matches the actual model ID."
        )
        return result
    if scope_mismatch:
        result["unavailable_reasons"].append("Explicit pricing scope has no matching configured rate regime.")
        return result
    sources = row.get("source_urls", [])
    if isinstance(sources, str):
        sources = [sources]
    result["pricing_sources"] = list(sources)
    if row.get("source_url") and row["source_url"] not in result["pricing_sources"]:
        result["pricing_sources"].append(row["source_url"])
    result["rates"] = {key: row.get(key) for key in RATE_FIELDS}
    result["assumptions"].extend(row.get("assumptions", []))
    if row.get("notes"):
        result["assumptions"].append(row["notes"])
    scope = row.get("rate_scope")
    verified = canonical.get("pricing_scope") is not None and canonical["pricing_scope"] == scope
    result["pricing_scope_verified"] = verified
    result["conditional"] = not verified or canonical["provenance"] != "measured"
    if scope is not None and not verified:
        result["assumptions"].append("Configured pricing scope is assumed, not verified from the usage export.")
    result["assumptions"].append("Output tokens already include reasoning; reasoning tokens are not charged a second time.")
    rates = {key: _rate(row.get(key)) for key in RATE_FIELDS}
    inp, out = canonical["input_tokens"], canonical["output_tokens"]
    read, write = canonical["cached_input_tokens"], canonical["cache_write_tokens"]
    base = rates["input_usd_per_million"]
    read_rate, write_rate = rates["cached_input_usd_per_million"], rates["cache_write_usd_per_million"]
    output_cost = _charge(out, rates["output_usd_per_million"])
    input_cost: Decimal | None = None
    input_parts: dict[str, Decimal | None] = {}
    if inp == 0:
        input_cost = Decimal(0)
    elif inp is not None and read is not None and write is not None:
        input_parts = {
            "uncached_input": _charge(inp - read - write, base),
            "cached_input": _charge(read, read_rate),
            "cache_write": _charge(write, write_rate),
        }
        if all(value is not None for value in input_parts.values()):
            input_cost = sum(input_parts.values(), Decimal(0))
    elif inp is not None and base is not None:
        adjustments = []
        for count, special_rate in ((read, read_rate), (write, write_rate)):
            if count == 0 or special_rate == base:
                adjustments.append(Decimal(0))
            elif count is not None and special_rate is not None:
                adjustments.append(Decimal(count) * (special_rate - base) / Decimal(1_000_000))
            else:
                adjustments.append(None)
        if all(value is not None for value in adjustments):
            input_cost = _charge(inp, base) + sum(adjustments, Decimal(0))
    if input_cost is None:
        # Non-overlapping portions whose costs are actually known. Do not use
        # a full-price base charge as a subtotal when an unknown discount exists.
        if not input_parts:
            input_parts = {"cached_input": _charge(read, read_rate), "cache_write": _charge(write, write_rate)}
        result["unavailable_reasons"].append("Input usage or an applicable cache/base rate is incomplete.")
        known = [value for value in input_parts.values() if value is not None]
        result["components_usd"].update({key: _money(value) for key, value in input_parts.items()})
    else:
        known = [input_cost]
        result["components_usd"]["input"] = _money(input_cost)
    result["components_usd"]["output"] = _money(output_cost)
    if output_cost is None:
        result["unavailable_reasons"].append("Output usage or output rate is unavailable.")
    else:
        known.append(output_cost)
    result["known_subtotal_usd"] = _money(sum(known, Decimal(0))) if known else None
    if input_cost is not None and output_cost is not None:
        result["total_usd"] = _money(input_cost + output_cost)
    return result
