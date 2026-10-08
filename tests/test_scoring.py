"""Scorer regression tests use adversarial reports, never model judging."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cronbench.baseline import build_report, render_markdown
from cronbench.scoring import score


def fixtures():
    paths = sorted((ROOT / "fixtures" / "development").glob("*.json"))
    paths += sorted((ROOT / "fixtures" / "heldout").glob("*.json"))
    return [(path, json.loads(path.read_text(encoding="utf-8"))) for path in paths]


class ScoringTests(unittest.TestCase):
    def assert_fails(self, report, fixture, markdown=None):
        result = score(report, fixture, markdown=markdown)
        self.assertFalse(result["passed"], result)

    def test_all_deterministic_baselines_pass(self):
        cases = fixtures()
        self.assertTrue(cases)
        for path, fixture in cases:
            with self.subTest(fixture=path.name):
                report = build_report(fixture)
                result = score(report, fixture, markdown=render_markdown(report))
                self.assertTrue(result["passed"], result)

    def test_scoring_is_deterministic_and_does_not_mutate_inputs(self):
        _, fixture = fixtures()[0]
        report = build_report(fixture)
        original_report, original_fixture = copy.deepcopy(report), copy.deepcopy(fixture)
        self.assertEqual(score(report, fixture), score(report, fixture))
        self.assertEqual(report, original_report)
        self.assertEqual(fixture, original_fixture)

    def test_numeric_tampering_fails(self):
        for path, fixture in fixtures():
            report = build_report(fixture)
            changed = False
            for source in report["sources"].values():
                for kpi in source["kpis"].values():
                    if kpi["current"] is not None:
                        kpi["current"] += 999
                        changed = True
                        break
                if changed:
                    break
            with self.subTest(fixture=path.name):
                self.assertTrue(changed)
                self.assert_fails(report, fixture)

    def test_structured_claim_tampering_and_unknown_refs_fail(self):
        tested = 0
        for path, fixture in fixtures():
            original = build_report(fixture)
            for index, finding in enumerate(original["findings"]):
                for claim_index, claim in enumerate(finding["claims"]):
                    if isinstance(claim["value"], (int, float)):
                        tested += 1
                        report = copy.deepcopy(original)
                        report["findings"][index]["claims"][claim_index]["value"] += 999
                        with self.subTest(fixture=path.name, mutation="claim_value"):
                            self.assert_fails(report, fixture)
                        report = copy.deepcopy(original)
                        report["findings"][index]["claims"][claim_index]["ref"] = "invented.metric.current"
                        with self.subTest(fixture=path.name, mutation="claim_ref"):
                            self.assert_fails(report, fixture)
                        report = copy.deepcopy(original)
                        report["findings"][index]["evidence_refs"].append("invented.metric.current")
                        with self.subTest(fixture=path.name, mutation="evidence_ref"):
                            self.assert_fails(report, fixture)
                        break
        self.assertGreater(tested, 0)

    def test_omitting_material_changes_fails(self):
        seen = False
        for path, fixture in fixtures():
            report = build_report(fixture)
            material = [
                finding for finding in report["findings"]
                if finding["kind"] == "change"
                and finding["metric"] in ("clicks", "sessions")
                and any(
                    claim["ref"].endswith(".wow_pct")
                    and claim["value"] is not None and abs(claim["value"]) >= 10
                    for claim in finding["claims"]
                )
            ]
            if material:
                seen = True
                report["findings"] = []
                with self.subTest(fixture=path.name):
                    self.assert_fails(report, fixture)
        self.assertTrue(seen, "A material change is needed to test omission penalties")

    def test_omitting_required_limitations_fails(self):
        seen = set()
        for path, fixture in fixtures():
            original = build_report(fixture)
            for limitation in original["limitations"]:
                if limitation["code"] in ("incomplete_data", "missing_values", "zero_denominator"):
                    seen.add(limitation["code"])
                    report = copy.deepcopy(original)
                    report["limitations"] = [
                        item for item in report["limitations"] if item != limitation
                    ]
                    with self.subTest(fixture=path.name, code=limitation["code"]):
                        self.assert_fails(report, fixture)
        self.assertTrue({"incomplete_data", "zero_denominator"} <= seen, seen)

    def test_schema_rejects_unknown_fields_and_excess_findings(self):
        _, fixture = fixtures()[0]
        original = build_report(fixture)
        report = copy.deepcopy(original)
        report["invented_kpi"] = 99
        self.assert_fails(report, fixture)
        with_findings = next((f for _, f in fixtures() if build_report(f)["findings"]), None)
        self.assertIsNotNone(with_findings)
        report = build_report(with_findings)
        report["findings"] = [copy.deepcopy(report["findings"][0]) for _ in range(4)]
        self.assert_fails(report, with_findings)

    def test_misidentified_fixture_and_tampered_coverage_fail(self):
        _, fixture = fixtures()[0]
        report = build_report(fixture)
        report["fixture_id"] = "a-different-fixture"
        self.assert_fails(report, fixture)
        report = build_report(fixture)
        coverage = report["sources"]["search_console"]["completeness"]["current"]
        coverage["observed_days"] = 0 if coverage["observed_days"] else 7
        self.assert_fails(report, fixture)

    def test_boolean_and_nonfinite_kpi_values_fail(self):
        _, fixture = fixtures()[0]
        for invalid in (True, float("nan"), float("inf")):
            report = build_report(fixture)
            report["sources"]["search_console"]["kpis"]["clicks"]["current"] = invalid
            with self.subTest(value=invalid):
                self.assert_fails(report, fixture)

    def test_malformed_reports_fail_without_crashing(self):
        _, fixture = fixtures()[0]
        for malformed in (None, [], "not a report", {}, {"sources": []}):
            with self.subTest(report=malformed):
                self.assert_fails(malformed, fixture)

    def test_empty_markdown_fails_when_markdown_is_provided(self):
        _, fixture = fixtures()[0]
        self.assert_fails(build_report(fixture), fixture, markdown="")

    def test_unsupported_numbers_and_contradictory_directions_fail(self):
        fixture = next(
            fixture for _, fixture in fixtures()
            if any(finding["kind"] == "change" for finding in build_report(fixture)["findings"])
        )
        original = build_report(fixture)
        index = next(i for i, finding in enumerate(original["findings"]) if finding["kind"] == "change")
        report = copy.deepcopy(original)
        report["findings"][index]["statement"] += " The total was 987654321."
        self.assert_fails(report, fixture)
        report = copy.deepcopy(original)
        finding = report["findings"][index]
        value = next(claim["value"] for claim in finding["claims"] if claim["ref"].endswith(".wow_pct"))
        finding["statement"] = "The metric decreased." if value > 0 else "The metric increased."
        self.assert_fails(report, fixture)

    def test_unsupported_causality_and_source_equivalence_fail(self):
        _, fixture = fixtures()[0]
        for statement in (
            "Paid marketing caused the observed change.",
            "The change was due to a search ranking improvement.",
            "Search Console clicks are sessions.",
            "PostHog sessions equal clicks.",
        ):
            report = build_report(fixture)
            report["summary"] = statement
            with self.subTest(statement=statement):
                self.assert_fails(report, fixture)

    def test_markdown_corruption_and_unrelated_markdown_fail(self):
        _, fixture = fixtures()[0]
        report = build_report(fixture)
        correct = render_markdown(report)
        for corrupted in (
            correct + "\nAn unsupported finding: total traffic was 987654321.\n",
            correct.replace("search_console.clicks", "posthog.sessions"),
            "# Weather report\nA sunny day is expected.\n",
        ):
            with self.subTest(markdown=corrupted[:70]):
                self.assertNotEqual(corrupted, correct)
                self.assert_fails(report, fixture, markdown=corrupted)
        self.assertTrue(score(report, fixture, markdown=correct.replace("\n", "\r\n"))["passed"])

    def test_nested_malformed_values_fail_without_crashing(self):
        fixture = next(fixture for _, fixture in fixtures() if build_report(fixture)["findings"])
        original = build_report(fixture)
        paths = (
            ("periods",), ("periods", "current"), ("sources",),
            ("sources", "search_console"), ("sources", "search_console", "kpis"),
            ("sources", "search_console", "kpis", "clicks"),
            ("sources", "search_console", "kpis", "clicks", "evidence_refs"),
            ("sources", "search_console", "completeness", "current"),
            ("findings", 0), ("findings", 0, "source"),
            ("findings", 0, "evidence_refs"), ("findings", 0, "claims"),
            ("findings", 0, "claims", 0), ("findings", 0, "claims", 0, "ref"),
            ("limitations", 0), ("limitations", 0, "code"), ("next_checks",),
        )
        for path in paths:
            for invalid in (None, True, 0, [], {}):
                report = copy.deepcopy(original)
                parent = report
                for key in path[:-1]:
                    parent = parent[key]
                parent[path[-1]] = invalid
                with self.subTest(path=path, value=invalid):
                    self.assert_fails(report, fixture)


if __name__ == "__main__":
    unittest.main()
