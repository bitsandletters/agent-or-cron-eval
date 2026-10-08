"""Offline checks for honest token accounting, costs, and failure denominators."""

import copy
import json
import unittest

from cronbench.aggregate import aggregate
from cronbench.costs import estimate_cost
from cronbench.usage import USAGE_FIELDS, normalize_usage, parse_usage_artifact


PRICING = {
    "as_of": "2026-10-08",
    "currency": "USD",
    "models": [
        {
            "model_id": "test-model",
            "aliases": ["verified-test-alias"],
            "input_usd_per_million": 2,
            "output_usd_per_million": 10,
            "cached_input_usd_per_million": 0.5,
            "cache_write_usd_per_million": 3,
            "source_url": "https://example.invalid/synthetic-test-pricing",
            "rate_scope": "test-short",
            "assumptions": ["Synthetic prices for offline tests only."],
            "alternative_regimes": [
                {"rate_scope": "test-long", "input_usd_per_million": 4, "output_usd_per_million": 20,
                 "cached_input_usd_per_million": 1, "cache_write_usd_per_million": 6}
            ],
        },
        {"model_id": "unknown-hosting", "input_usd_per_million": None, "output_usd_per_million": None},
    ],
}


def usage(**updates):
    result = {
        "input_tokens": 1000, "output_tokens": 200, "cached_input_tokens": 100,
        "cache_write_tokens": 50, "reasoning_output_tokens": 100, "request_count": 2,
        "provenance": "measured", "source": "synthetic_test_fixture",
    }
    result.update(updates)
    return result


def record(run_id="r1", attempt=1, **updates):
    result = {
        "run_id": run_id, "attempt": attempt, "arm": "C", "fixture_id": "test-fixture",
        "split": "development", "repeat": 1, "host": "test-host", "requested_model": "test-model",
        "actual_model": "test-model", "configuration": {"seed": 1}, "cache_state": "cold",
        "status": "completed", "score": {"passed": True, "score": 1.0, "metrics": {"numeric_accuracy": 1}},
        "usage": usage(), "tool_count": 3, "latency_seconds": 2.0, "setup_seconds": None,
        "mock": True, "factors": {"prompt_breadth": "narrow", "execution_style": "tool_driven"},
        "configured_main_model": "test-model", "configured_auxiliary_models": None, "observed_models": ["test-model"],
        "routing_mode": "explicit", "invocation_mode": "fresh_context",
    }
    result.update(updates)
    return result


class UsageTests(unittest.TestCase):
    def test_missing_usage_is_null_not_zero(self):
        normalized = normalize_usage()
        self.assertTrue(all(normalized[field] is None for field in USAGE_FIELDS))
        self.assertIsNone(normalized["total_tokens"])
        self.assertEqual(normalized["provenance"], "unavailable")

    def test_cache_and_reasoning_are_subsets(self):
        normalized = normalize_usage(usage())
        self.assertEqual(normalized["total_tokens"], 1200)

    def test_reject_invalid_or_inconsistent_counters(self):
        for values in (
            {"input_tokens": -1}, {"output_tokens": True}, {"input_tokens": 1.5},
            {"input_tokens": 10, "cached_input_tokens": 11},
            {"input_tokens": 10, "cached_input_tokens": 6, "cache_write_tokens": 6},
            {"output_tokens": 5, "reasoning_output_tokens": 6},
        ):
            with self.subTest(values=values), self.assertRaises(ValueError):
                normalize_usage(values)

    def test_codex_documented_usage_only(self):
        artifact = "\n".join([
            "diagnostic line",
            json.dumps({"type": "item.completed", "usage": {"input_tokens": 999}}),
            json.dumps({"type": "turn.completed", "usage": {"input_tokens": 100, "output_tokens": 10, "cached_input_tokens": 20}}),
            json.dumps({"type": "turn.completed", "usage": {"input_tokens": 50, "output_tokens": 5, "cached_input_tokens": 0}}),
        ])
        result = parse_usage_artifact(artifact, "codex")
        self.assertEqual(result["input_tokens"], 150)
        self.assertEqual(result["total_tokens"], 165)
        self.assertEqual(result["cached_input_tokens"], 20)
        self.assertIsNone(result["request_count"])
        self.assertIsNone(result["cache_write_tokens"])
        self.assertIsNone(result["reasoning_output_tokens"])

    def test_partial_codex_turn_counter_cannot_be_complete_sum(self):
        artifact = json.dumps([
            {"type": "turn.completed", "usage": {"input_tokens": 100, "output_tokens": 10}},
            {"type": "turn.completed", "usage": {"output_tokens": 5}},
        ])
        result = parse_usage_artifact(artifact, "codex")
        self.assertIsNone(result["input_tokens"])
        self.assertEqual(result["output_tokens"], 15)

    def test_amp_terminal_usage_not_double_counted(self):
        native = {"input_tokens": 10, "output_tokens": 5, "cache_creation_input_tokens": 100, "cache_read_input_tokens": 20}
        result = parse_usage_artifact(json.dumps([
            {"type": "assistant", "message": {"usage": native}},
            {"type": "result", "usage": native},
        ]), "amp")
        self.assertEqual(result["output_tokens"], 5)
        self.assertEqual(result["cache_write_tokens"], 100)
        self.assertEqual(result["cached_input_tokens"], 20)
        self.assertIsNone(result["input_tokens"])  # Host-wide cache semantics not promised.
        self.assertIsNone(result["request_count"])

    def test_amp_assistant_usage_and_unknown_optional_fields(self):
        result = parse_usage_artifact(json.dumps([
            {"type": "assistant", "message": {"usage": {"input_tokens": 10, "output_tokens": 5}}},
            {"type": "assistant", "message": {"usage": {"input_tokens": 15, "output_tokens": 7}}},
        ]), "amp")
        self.assertEqual(result["output_tokens"], 12)
        self.assertIsNone(result["cached_input_tokens"])
        self.assertIsNone(result["input_tokens"])

    def test_unknown_shape_and_cursor_usage_unavailable(self):
        for host in ("cursor", "other", "codex", "amp"):
            with self.subTest(host=host):
                result = parse_usage_artifact('{"usage":{"input_tokens":100},"model":"Pretty name"}', host)
                self.assertIsNone(result["input_tokens"])
                self.assertEqual(result["provenance"], "unavailable")

    def test_estimated_usage_stays_estimated(self):
        self.assertEqual(normalize_usage(usage(provenance="estimated"))["provenance"], "estimated")


class CostTests(unittest.TestCase):
    def test_no_double_count_of_cache_or_reasoning(self):
        cost = estimate_cost(usage(), "test-model", PRICING)
        # 850 fresh * $2 + 100 cache-read * $.5 + 50 write * $3 + 200 output * $10, per million.
        self.assertAlmostEqual(cost["total_usd"], 0.0039)
        self.assertIsNone(cost["actual_subscription_charge_usd"])
        self.assertTrue(cost["conditional"])
        self.assertEqual(cost["pricing_as_of"], "2026-10-08")

    def test_reasoning_unknown_does_not_block_output_price(self):
        self.assertAlmostEqual(estimate_cost(usage(reasoning_output_tokens=None), "test-model", PRICING)["total_usd"], 0.0039)

    def test_cache_unknown_blocks_complete_discounted_price(self):
        cost = estimate_cost(usage(cached_input_tokens=None), "test-model", PRICING)
        self.assertIsNone(cost["total_usd"])
        self.assertAlmostEqual(cost["known_subtotal_usd"], 0.00215)

    def test_unknown_cache_write_blocks_distinct_rate(self):
        self.assertIsNone(estimate_cost(usage(cache_write_tokens=None), "test-model", PRICING)["total_usd"])

    def test_equal_cache_write_rate_needs_no_write_breakdown(self):
        table = copy.deepcopy(PRICING)
        table["models"][0]["cache_write_usd_per_million"] = 2
        cost = estimate_cost(usage(cache_write_tokens=None), "test-model", table)
        self.assertAlmostEqual(cost["total_usd"], 0.00385)

    def test_explicit_zero_tokens_require_no_rates_or_model(self):
        cost = estimate_cost({"input_tokens": 0, "output_tokens": 0, "source": "deterministic_no_llm"}, None, PRICING)
        self.assertEqual(cost["total_usd"], 0)
        self.assertFalse(cost["conditional"])

    def test_missing_usage_and_model_not_inferred(self):
        self.assertIsNone(estimate_cost(None, "test-model", PRICING)["total_usd"])
        self.assertIsNone(estimate_cost(usage(), None, PRICING)["total_usd"])
        self.assertIsNone(estimate_cost(usage(), "Requested display name", PRICING)["total_usd"])

    def test_verified_alias_only(self):
        self.assertIsNotNone(estimate_cost(usage(), "verified-test-alias", PRICING)["total_usd"])
        self.assertIsNone(estimate_cost(usage(), "test", PRICING)["total_usd"])

    def test_open_weight_unknown_hosting_price_remains_null(self):
        self.assertIsNone(estimate_cost(usage(), "unknown-hosting", PRICING)["total_usd"])

    def test_explicit_scope_selects_alternative(self):
        cost = estimate_cost(usage(pricing_scope="test-long"), "test-model", PRICING)
        self.assertAlmostEqual(cost["total_usd"], 0.0078)
        self.assertEqual(cost["rate_scope"], "test-long")
        self.assertTrue(cost["pricing_scope_verified"])
        self.assertFalse(cost["conditional"])

    def test_known_mismatching_scope_does_not_use_default(self):
        self.assertIsNone(estimate_cost(usage(pricing_scope="different"), "test-model", PRICING)["total_usd"])


class AggregateTests(unittest.TestCase):
    def test_retry_costs_and_failures_retained(self):
        rows = [record(attempt=1, status="quota_exhausted", score=None, latency_seconds=1), record(attempt=2, latency_seconds=3)]
        summary = aggregate(rows, PRICING)["overall"]
        self.assertEqual(summary["attempts"]["count"], 2)
        self.assertEqual(summary["attempts"]["status_counts"]["quota_exhausted"], 1)
        self.assertEqual(summary["final_runs"]["count"], 1)
        self.assertEqual(summary["first_attempts"]["status_counts"], {"quota_exhausted": 1})
        self.assertEqual(summary["first_attempts"]["pass_rate"], 0)
        self.assertEqual(summary["retried_run_count"], 1)
        self.assertEqual(summary["additional_attempt_count"], 1)
        self.assertAlmostEqual(summary["runtime_api_equivalent_cost_per_passing_report_usd"], 0.0078)
        self.assertEqual(summary["attempts"]["latency_seconds"]["population_stdev"], 1)
        self.assertEqual(summary["total_attempt_latency_per_final_run_seconds"]["mean"], 4)
        self.assertAlmostEqual(summary["weekly_projections"][2]["runtime_api_equivalent_usd"], 0.0078 * 52)

    def test_missing_failed_attempt_usage_prevents_cheap_success_claim(self):
        summary = aggregate([record(attempt=1, status="timeout", score=None, usage=None), record(attempt=2)], PRICING)["overall"]
        self.assertIsNone(summary["runtime_api_equivalent_usd"]["complete_sum"])
        self.assertIsNone(summary["runtime_api_equivalent_cost_per_passing_report_usd"])
        self.assertIsNone(summary["weekly_projections"][0]["runtime_api_equivalent_usd"])
        self.assertEqual(summary["usage"]["input_tokens"]["missing"], 1)

    def test_final_quota_exhaustion_is_in_final_pass_denominator(self):
        summary = aggregate([record("good"), record("quota", status="quota_exhausted", score=None)], PRICING)["overall"]
        self.assertEqual(summary["final_runs"]["pass_rate"], 0.5)
        self.assertEqual(summary["final_runs"]["execution_failure_rate"], 0.5)

    def test_opaque_routing_and_multiple_requests_are_not_disqualified(self):
        summary = aggregate([record("explicit"), record("opaque", routing_mode="host_native_opaque", usage=usage(request_count=7))], PRICING)["overall"]
        self.assertEqual(summary["final_runs"]["passing_count"], 2)
        self.assertEqual(summary["final_runs"]["pass_rate"], 1)

    def test_group_dimensions_prevent_mock_cache_host_confounds(self):
        rows = [record("a"), record("b", mock=False), record("c", cache_state="warm"), record("d", host="other"),
                record("e", configuration={"seed": 2}), record("f", split="heldout"), record("g", routing_mode="host_native_opaque"),
                record("h", factors={"prompt_breadth": "broad", "execution_style": "tool_driven"}),
                record("i", invocation_mode="scheduled"), record("j", configured_auxiliary_models=["helper"])]
        self.assertEqual(len(aggregate(rows, PRICING)["groups"]), 10)

    def test_setup_usage_separate_and_unknown_by_default(self):
        summary = aggregate([record()], PRICING)["overall"]
        self.assertIsNone(summary["setup_api_equivalent_usd"]["complete_sum"])
        zero = {"input_tokens": 0, "output_tokens": 0, "source": "deterministic_setup"}
        summary = aggregate([record(setup_usage=zero, setup_actual_model=None)], PRICING)["overall"]
        self.assertEqual(summary["setup_api_equivalent_usd"]["complete_sum"], 0)

    def test_all_unknown_latency_remains_unknown(self):
        stats = aggregate([record(latency_seconds=None)], PRICING)["overall"]["attempts"]["latency_seconds"]
        self.assertIsNone(stats["mean"])
        self.assertEqual(stats["missing"], 1)

    def test_duplicate_attempts_rejected(self):
        with self.assertRaises(ValueError):
            aggregate([record(), record()], PRICING)

    def test_missing_earlier_attempt_disables_cost_per_report(self):
        result = aggregate([record(attempt=2)], PRICING)
        self.assertEqual(result["incomplete_attempt_histories"], [{"run_id": "r1", "missing_attempt_numbers": [1]}])
        self.assertEqual(result["overall"]["first_attempts"]["count"], 0)
        self.assertIsNone(result["overall"]["runtime_api_equivalent_cost_per_passing_report_usd"])

    def test_group_change_does_not_drop_unknown_failure_cost(self):
        result = aggregate([record(attempt=1, actual_model=None, status="failed", score=None), record(attempt=2)], PRICING)
        for group in result["groups"]:
            self.assertEqual(group["cross_group_run_ids"], ["r1"])
            self.assertIsNone(group["runtime_api_equivalent_cost_per_passing_report_usd"])

    def test_empty_study_has_no_fabricated_zeros(self):
        result = aggregate([], PRICING)
        self.assertEqual(result["groups"], [])
        self.assertIsNone(result["overall"]["final_runs"]["pass_rate"])
        self.assertIsNone(result["overall"]["runtime_api_equivalent_usd"]["complete_sum"])

    def test_order_independent_aggregation(self):
        rows = [record("b"), record("a")]
        self.assertEqual(aggregate(rows, PRICING), aggregate(list(reversed(rows)), PRICING))


if __name__ == "__main__":
    unittest.main()
