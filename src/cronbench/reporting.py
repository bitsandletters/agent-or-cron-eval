"""Answer-free canonical rendering shared unchanged by all arms."""
from __future__ import annotations


def _display(value: int | float | None) -> str:
    return "unknown" if value is None else f"{value:.6f}".rstrip("0").rstrip(".") if isinstance(value, float) else str(value)



def render_markdown(report: dict) -> str:
    """Canonical human-readable rendering shared by all arms after report import."""
    lines = [f"# Weekly analytics: {report['fixture_id']}", "", report["summary"], "",
             f"Previous: {report['periods']['previous']['start']} to {report['periods']['previous']['end']}",
             f"Current: {report['periods']['current']['start']} to {report['periods']['current']['end']}", ""]
    metric_order = {"search_console": ("clicks", "impressions", "position", "ctr"),
                    "posthog": ("sessions", "users", "conversions", "conversion_rate")}
    for source, metrics in metric_order.items():
        block = report["sources"][source]
        lines.extend([f"## {source}", "", "| Metric | Previous | Current | Change | WoW % | Unit | Status |",
                      "| --- | ---: | ---: | ---: | ---: | --- | --- |"])
        for metric in metrics:
            kpi = block["kpis"][metric]
            values = [_display(kpi[field]) for field in ("previous", "current", "absolute_change", "wow_pct")]
            lines.append(f"| {metric} | {' | '.join(values)} | {kpi['unit']} | {kpi['status']} |")
        lines.append("")
    lines.extend(["## Findings", ""])
    for finding in report["findings"]:
        lines.append(f"- {finding['statement']} Evidence: {', '.join(finding['evidence_refs'])}.")
    if not report["findings"]:
        lines.append("No finding is asserted.")
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {item['detail']} ({item['code']})" for item in report["limitations"])
    lines.extend(["", "## Next checks", ""])
    lines.extend(f"- {item}" for item in report["next_checks"])
    return "\n".join(lines) + "\n"
