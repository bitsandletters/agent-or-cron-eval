"""Deterministic scoring; never include this module in an evaluated packet.

Structured claims are machine-checked. Semantic support of unrestricted prose is
explicitly left to blinded human review; lexical checks here are conservative,
bounded checks, not an assertion that all hallucinations can be detected.
"""
from __future__ import annotations

import math
import re
from typing import Any

from .baseline import material_metrics, render_markdown
from .runtime import DERIVED_METRICS, RAW_METRICS, VALUE_FIELDS, prepare

COMPONENTS = ("schema", "numeric_accuracy", "evidence_support", "material_changes",
              "missing_data", "unsupported_claims", "markdown")


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _equal(actual: Any, expected: Any) -> bool:
    if expected is None:
        return actual is None
    if _is_number(expected):
        return _is_number(actual) and math.isclose(actual, expected, rel_tol=1e-7, abs_tol=1e-6)
    return actual == expected


def validate_report(report: Any) -> list[str]:
    """Validate the supported report JSON Schema without a third-party dependency."""
    errors: list[str] = []

    def fields(value: Any, keys: set[str], path: str) -> bool:
        if not isinstance(value, dict):
            errors.append(f"{path}: expected object")
            return False
        if set(value) != keys:
            errors.append(f"{path}: missing {sorted(keys - set(value))}, unexpected {sorted(set(value) - keys)}")
            return False
        return True

    def string(value: Any, path: str) -> None:
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{path}: expected nonempty text")

    def refs(value: Any, path: str) -> None:
        if not isinstance(value, list) or not value:
            errors.append(f"{path}: expected nonempty array")
            return
        for index, item in enumerate(value):
            string(item, f"{path}[{index}]")
        if all(isinstance(item, str) for item in value) and len(set(value)) != len(value):
            errors.append(f"{path}: entries must be unique")

    if not fields(report, {"schema_version", "fixture_id", "periods", "summary", "sources", "findings", "limitations", "next_checks"}, "report"):
        return errors
    if report["schema_version"] != "1.0":
        errors.append("schema_version: must be 1.0")
    string(report["fixture_id"], "fixture_id")
    string(report["summary"], "summary")
    if fields(report["periods"], {"previous", "current"}, "periods"):
        for period, values in report["periods"].items():
            if fields(values, {"start", "end"}, f"periods.{period}"):
                for key, value in values.items():
                    string(value, f"periods.{period}.{key}")
    if fields(report["sources"], set(RAW_METRICS), "sources"):
        for source, block in report["sources"].items():
            if not fields(block, {"completeness", "kpis"}, source):
                continue
            if fields(block["completeness"], {"previous", "current"}, f"{source}.completeness"):
                for period, value in block["completeness"].items():
                    if fields(value, {"expected_days", "observed_days", "reason"}, f"{source}.completeness.{period}"):
                        if value["expected_days"] != 7 or isinstance(value["expected_days"], bool):
                            errors.append("expected_days must be 7")
                        observed = value["observed_days"]
                        if isinstance(observed, bool) or not isinstance(observed, int) or not 0 <= observed <= 7:
                            errors.append("observed_days must be an integer in [0,7]")
                        if value["reason"] is not None:
                            string(value["reason"], "completeness.reason")
            metric_names = set(RAW_METRICS[source]) | {DERIVED_METRICS[source][0]}
            if fields(block["kpis"], metric_names, f"{source}.kpis"):
                for metric, value in block["kpis"].items():
                    path = f"{source}.kpis.{metric}"
                    if not fields(value, set(VALUE_FIELDS) | {"unit", "status", "evidence_refs"}, path):
                        continue
                    for key in VALUE_FIELDS:
                        if value[key] is not None and not _is_number(value[key]):
                            errors.append(f"{path}.{key}: expected finite number or null")
                    if value["unit"] not in ("count", "ratio", "position"):
                        errors.append(f"{path}.unit: invalid unit")
                    if value["status"] not in ("ok", "zero_baseline", "missing", "incomplete"):
                        errors.append(f"{path}.status: invalid status")
                    refs(value["evidence_refs"], f"{path}.evidence_refs")
    findings = report["findings"]
    if not isinstance(findings, list) or len(findings) > 3:
        errors.append("findings: expected array with at most three items")
    else:
        ids = []
        for index, item in enumerate(findings):
            path = f"findings[{index}]"
            if not fields(item, {"id", "kind", "source", "metric", "statement", "evidence_refs", "claims"}, path):
                continue
            string(item["id"], f"{path}.id")
            if isinstance(item["id"], str):
                ids.append(item["id"])
            string(item["statement"], f"{path}.statement")
            if item["kind"] not in ("change", "insufficient_evidence"):
                errors.append(f"{path}.kind: invalid kind")
            source = item["source"]
            if not isinstance(source, str) or source not in RAW_METRICS:
                errors.append(f"{path}.source: unknown source")
            elif not isinstance(item["metric"], str) or item["metric"] not in set(RAW_METRICS[source]) | {DERIVED_METRICS[source][0]}:
                errors.append(f"{path}.metric: metric does not belong to source")
            refs(item["evidence_refs"], f"{path}.evidence_refs")
            if not isinstance(item["claims"], list) or not item["claims"]:
                errors.append(f"{path}.claims: expected nonempty array")
            else:
                for claim in item["claims"]:
                    if fields(claim, {"ref", "value"}, f"{path}.claims"):
                        string(claim["ref"], f"{path}.claims.ref")
                        if claim["value"] is not None and not _is_number(claim["value"]):
                            errors.append(f"{path}.claims.value: expected finite number or null")
        if len(set(ids)) != len(ids):
            errors.append("findings: ids must be unique")
    if not isinstance(report["limitations"], list) or not report["limitations"]:
        errors.append("limitations: expected nonempty array")
    else:
        for item in report["limitations"]:
            if fields(item, {"code", "source", "detail"}, "limitations"):
                string(item["code"], "limitations.code")
                string(item["detail"], "limitations.detail")
                if item["source"] is not None and item["source"] not in tuple(RAW_METRICS):
                    errors.append("limitations.source: unknown source")
    refs(report["next_checks"], "next_checks")
    return errors


def score(report: Any, fixture: dict, markdown: str | None = None) -> dict:
    evidence = prepare(fixture)
    errors: dict[str, list[str]] = {name: [] for name in COMPONENTS}
    errors["schema"] = validate_report(report)
    if errors["schema"]:
        for name in COMPONENTS[1:]:
            errors[name].append("Not evaluated because report schema is invalid")
        return _result(errors)
    if report["fixture_id"] != fixture["fixture_id"] or report["periods"] != fixture["periods"]:
        errors["numeric_accuracy"].append("Report fixture or reporting periods do not match input")
    for source, block in evidence["sources"].items():
        actual = report["sources"][source]
        if actual["completeness"] != block["completeness"]:
            errors["missing_data"].append(f"{source}: completeness metadata changed")
        for metric, expected in block["kpis"].items():
            candidate = actual["kpis"][metric]
            for field in VALUE_FIELDS + ("unit", "status"):
                if not _equal(candidate[field], expected[field]):
                    errors["numeric_accuracy"].append(f"{source}.{metric}.{field}: expected {expected[field]!r}, got {candidate[field]!r}")
            if set(candidate["evidence_refs"]) != set(expected["evidence_refs"]):
                errors["evidence_support"].append(f"{source}.{metric}: KPI evidence references must match its values")
    for finding in report["findings"]:
        prefix = f"{finding['source']}.{finding['metric']}."
        refs = finding["evidence_refs"]
        claims = finding["claims"]
        claim_refs = [claim["ref"] for claim in claims]
        if len(set(claim_refs)) != len(claim_refs):
            errors["evidence_support"].append(f"{finding['id']}: duplicate claim references")
        if set(claim_refs) != set(refs):
            errors["evidence_support"].append(f"{finding['id']}: claims and cited evidence must cover the same references")
        for ref in refs:
            if ref not in evidence["evidence"] or not ref.startswith(prefix):
                errors["evidence_support"].append(f"{finding['id']}: unknown or mismatched evidence {ref}")
        for claim in claims:
            if claim["ref"] not in evidence["evidence"] or not _equal(claim["value"], evidence["evidence"].get(claim["ref"])):
                errors["evidence_support"].append(f"{finding['id']}: unsupported numeric claim {claim['ref']}")
        kpi = evidence["sources"][finding["source"]]["kpis"][finding["metric"]]
        if finding["kind"] == "change":
            if kpi["status"] != "ok" or prefix + "wow_pct" not in claim_refs:
                errors["evidence_support"].append(f"{finding['id']}: change requires a comparable cited percentage change")
        elif kpi["status"] == "ok":
            errors["evidence_support"].append(f"{finding['id']}: selected KPI has complete comparison evidence")
        statement = finding["statement"]
        for token in re.findall(r"(?<![\w.])[-+]?\d+(?:\.\d+)?%?", statement):
            number = float(token.rstrip("%"))
            supported = [claim["value"] for claim in claims if _is_number(claim["value"])]
            if token.endswith("%"):
                supported += [claim["value"] * 100 for claim in claims if _is_number(claim["value"]) and "." + finding["metric"] + "." in claim["ref"] and kpi["unit"] == "ratio" and not claim["ref"].endswith("wow_pct")]
            if not any(_equal(number, value) for value in supported):
                errors["unsupported_claims"].append(f"{finding['id']}: prose number {token} lacks a matching structured claim")
        change = kpi["wow_pct"]
        if change is not None:
            if change < 0 and re.search(r"\b(increased|rose|grew)\b", statement, re.I):
                errors["unsupported_claims"].append(f"{finding['id']}: prose direction contradicts decrease")
            if change > 0 and re.search(r"\b(decreased|fell|declined)\b", statement, re.I):
                errors["unsupported_claims"].append(f"{finding['id']}: prose direction contradicts increase")
    covered = {(item["source"], item["metric"]) for item in report["findings"] if item["kind"] == "change"}
    for source, metric in material_metrics(evidence):
        if (source, metric) not in covered:
            errors["material_changes"].append(f"Missing material change finding for {source}.{metric}")
    required = {(item["code"], item["source"]) for item in evidence["warnings"]}
    required |= {("synthetic_data", None), ("source_distinction", None)}
    supplied = {(item["code"], item["source"]) for item in report["limitations"]}
    for code, source in sorted(required - supplied, key=str):
        errors["missing_data"].append(f"Missing limitation {code} for {source}")
    for code, source in supplied - required:
        if code in {"incomplete_data", "missing_values", "zero_denominator"}:
            errors["missing_data"].append(f"Unsupported limitation {code} for {source}")
    prose = " ".join([report["summary"], *(item["statement"] for item in report["findings"])])
    if re.search(r"\b(caused|because|due to|driven by|proves|attributed to|resulted in)\b", prose, re.I):
        errors["unsupported_claims"].append("Causal attribution is unsupported by these aggregate weekly fixtures")
    if re.search(r"\bclicks\s+(?:are|equal|equals|=)\s+(?:the\s+)?sessions\b|\bsessions\s+(?:are|equal|equals|=)\s+(?:the\s+)?clicks\b", prose, re.I):
        errors["unsupported_claims"].append("Clicks and sessions are not interchangeable")
    if markdown is not None:
        if not isinstance(markdown, str) or markdown.replace("\r\n", "\n").strip() != render_markdown(report).strip():
            errors["markdown"].append("report.md must match the canonical rendering of report.json")
    return _result(errors)


def _result(errors: dict[str, list[str]]) -> dict:
    metrics = {name: int(not values) for name, values in errors.items()}
    return {"passed": all(metrics.values()), "score": sum(metrics.values()) / len(metrics),
            "components": {name: {"passed": not values, "errors": values} for name, values in errors.items()},
            "errors": [f"{name}: {item}" for name, values in errors.items() for item in values],
            "metrics": metrics, "human_review_required": True,
            "limitations": ["Automated support checks cover structured claims, numeric prose in findings, and bounded lexical contradictions.",
                            "Free-text meaning, causal wording outside those patterns, usefulness, and quality of next checks require blinded human review."]}
