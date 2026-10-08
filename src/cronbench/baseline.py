"""Deterministic complete-report pipeline. Available as a shortcut only to arm E."""
from __future__ import annotations

import copy

from .runtime import prepare
from .reporting import _display, render_markdown


def material_metrics(evidence: dict) -> list[tuple[str, str]]:
    """Preregistered objective coverage requirement; kept out of evaluated contexts."""
    return [(source, metric) for source, metric in (("search_console", "clicks"), ("posthog", "sessions"))
            if evidence["sources"][source]["kpis"][metric]["status"] == "ok"
            and abs(evidence["sources"][source]["kpis"][metric]["wow_pct"]) >= 10]


def build_report(fixture: dict) -> dict:
    evidence = prepare(fixture)
    findings = []
    for source, metric in material_metrics(evidence):
        kpi = evidence["sources"][source]["kpis"][metric]
        refs = [f"{source}.{metric}.{field}" for field in ("previous", "current", "wow_pct")]
        direction = "increased" if kpi["wow_pct"] > 0 else "decreased"
        findings.append({"id": f"f{len(findings) + 1}", "kind": "change", "source": source, "metric": metric,
                         "statement": f"{source} {metric} {direction} from {_display(kpi['previous'])} to {_display(kpi['current'])} ({_display(kpi['wow_pct'])}% week over week).",
                         "evidence_refs": refs,
                         "claims": [{"ref": ref, "value": evidence["evidence"][ref]} for ref in refs]})
    if not findings:
        for source, metric in (("search_console", "clicks"), ("posthog", "sessions")):
            kpi = evidence["sources"][source]["kpis"][metric]
            if kpi["status"] != "ok":
                ref = f"{source}.{metric}.wow_pct"
                findings.append({"id": f"f{len(findings) + 1}", "kind": "insufficient_evidence", "source": source,
                                 "metric": metric, "statement": f"{source} {metric} has insufficient evidence for a comparable percentage change ({kpi['status']}).",
                                 "evidence_refs": [ref], "claims": [{"ref": ref, "value": None}]})
    limitations = [{"code": "synthetic_data", "source": None, "detail": "This report uses synthetic fixture data only."},
                   {"code": "source_distinction", "source": None, "detail": "Search Console clicks and PostHog sessions measure different populations and are not interchangeable."}]
    limitations.extend(copy.deepcopy(evidence["warnings"]))
    next_checks = ["Check source collection coverage before drawing conclusions.",
                   "Segment each source by page and acquisition channel before proposing causes."]
    return {"schema_version": "1.0", "fixture_id": fixture["fixture_id"], "periods": copy.deepcopy(evidence["periods"]),
            "summary": "Synthetic weekly analytics report. Changes describe observed source metrics; causal explanations require additional evidence.",
            "sources": copy.deepcopy(evidence["sources"]), "findings": findings[:3],
            "limitations": limitations, "next_checks": next_checks}
