"""Independent invariants for fixture preparation and the deterministic arm."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cronbench.baseline import build_report, render_markdown
from cronbench.runtime import calculate, prepare, validate_fixture


def fixtures():
    paths = sorted((ROOT / "fixtures" / "development").glob("*.json"))
    paths += sorted((ROOT / "fixtures" / "heldout").glob("*.json"))
    return [(path, json.loads(path.read_text(encoding="utf-8"))) for path in paths]


class RuntimeTests(unittest.TestCase):
    def test_calculate_known_cases_including_rounding_and_missing_values(self):
        growth = calculate(100, 125)
        self.assertEqual(growth["absolute_change"], 25)
        self.assertEqual(growth["wow_pct"], 25)
        self.assertEqual(calculate(100, 80)["wow_pct"], -20)
        self.assertEqual(calculate(1 / 3, 1 / 2)["wow_pct"], 50)
        self.assertIsNone(calculate(0, 10)["wow_pct"])
        self.assertEqual(calculate(0, 10)["absolute_change"], 10)
        self.assertEqual(calculate(None, 10)["status"], "missing")
        self.assertIsNone(calculate(None, 10)["absolute_change"])
        self.assertIsNone(calculate(10, None)["wow_pct"])
        self.assertEqual(calculate(10, 20, comparable=False)["status"], "incomplete")

    def test_calculate_rejects_nonfinite_values_and_booleans(self):
        for value in (float("inf"), float("-inf"), float("nan"), True, "10"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                calculate(10, value)

    def test_both_fixture_splits_exist(self):
        for split in ("development", "heldout"):
            self.assertTrue(list((ROOT / "fixtures" / split).glob("*.json")), split)

    def test_preparation_and_baseline_are_reproducible_without_mutation(self):
        for path, fixture in fixtures():
            with self.subTest(fixture=path.name):
                original = copy.deepcopy(fixture)
                first_evidence = prepare(fixture)
                self.assertEqual(first_evidence, prepare(copy.deepcopy(fixture)))
                first_report = build_report(fixture)
                self.assertEqual(first_report, build_report(copy.deepcopy(fixture)))
                self.assertEqual(render_markdown(first_report), render_markdown(first_report))
                self.assertEqual(fixture, original)

    def test_zero_denominators_are_unknown_not_infinite_or_zero_growth(self):
        seen = False
        for path, fixture in fixtures():
            evidence = prepare(fixture)
            for source, data in evidence["sources"].items():
                for metric, kpi in data["kpis"].items():
                    if kpi["previous"] == 0:
                        seen = True
                        with self.subTest(fixture=path.name, source=source, metric=metric):
                            self.assertIsNone(kpi["wow_pct"])
        self.assertTrue(seen, "The fixture suite must exercise zero denominators")

    def test_incomplete_observations_do_not_claim_reliable_changes(self):
        seen = False
        for path, fixture in fixtures():
            for source, data in prepare(fixture)["sources"].items():
                for metric, kpi in data["kpis"].items():
                    if kpi["status"] == "incomplete":
                        seen = True
                        with self.subTest(fixture=path.name, source=source, metric=metric):
                            self.assertIsNone(kpi["absolute_change"])
                            self.assertIsNone(kpi["wow_pct"])
        self.assertTrue(seen, "The fixture suite must exercise incomplete observations")

    def test_percentage_changes_match_arithmetic_for_complete_observations(self):
        seen = False
        for path, fixture in fixtures():
            for source, data in prepare(fixture)["sources"].items():
                for metric, kpi in data["kpis"].items():
                    if kpi["status"] == "ok" and kpi["previous"] not in (None, 0):
                        seen = True
                        with self.subTest(fixture=path.name, source=source, metric=metric):
                            delta = kpi["current"] - kpi["previous"]
                            self.assertAlmostEqual(kpi["absolute_change"], delta, places=5)
                            self.assertAlmostEqual(
                                kpi["wow_pct"], 100 * delta / kpi["previous"], places=4
                            )
        self.assertTrue(seen)

    def test_report_outputs_serialize_as_strict_json_and_nonempty_markdown(self):
        for path, fixture in fixtures():
            with self.subTest(fixture=path.name):
                report = build_report(fixture)
                json.dumps(report, allow_nan=False)
                markdown = render_markdown(report)
                self.assertIsInstance(markdown, str)
                self.assertGreater(len(markdown.strip()), 80)
                self.assertIn("search", markdown.lower())
                self.assertIn("posthog", markdown.lower())

    def test_canonical_markdown_is_invariant_to_json_object_key_order(self):
        for path, fixture in fixtures():
            with self.subTest(fixture=path.name):
                report = build_report(fixture)
                round_trip = json.loads(json.dumps(report, sort_keys=True))
                self.assertEqual(render_markdown(report), render_markdown(round_trip))

    def test_invalid_fixtures_are_rejected_before_calculation(self):
        _, original = fixtures()[0]
        mutations = (
            ("impossible_count", lambda f: f["sources"]["search_console"]["current"].update(clicks=-1)),
            ("boolean_count", lambda f: f["sources"]["search_console"]["current"].update(clicks=True)),
            ("fractional_count", lambda f: f["sources"]["search_console"]["current"].update(clicks=0.5)),
            ("impossible_coverage", lambda f: f["sources"]["posthog"]["completeness"]["current"].update(observed_days=8)),
            ("nonfinite_position", lambda f: f["sources"]["search_console"]["current"].update(position=float("inf"))),
        )
        for label, mutate in mutations:
            fixture = copy.deepcopy(original)
            mutate(fixture)
            with self.subTest(mutation=label), self.assertRaises(ValueError):
                validate_fixture(fixture)


if __name__ == "__main__":
    unittest.main()
