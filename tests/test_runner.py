"""Controller integration tests; no subscription host or paid API is launched."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cronbench.baseline import build_report, render_markdown
from cronbench import runner
from cronbench.usage import USAGE_FIELDS


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="cronbench-runner-test-")
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.root = self.directory / "checkout"
        self.root.mkdir()
        for name in ("src", "fixtures", "schemas", "prompts", "pricing"):
            shutil.copytree(
                ROOT / name, self.root / name,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
            )
        shutil.copytree(ROOT / "scripts", self.root / "scripts")
        shutil.copy2(ROOT / "cronbench", self.root / "cronbench")
        runner.write_json(self.root / "manifest.json", runner.manifest(self.root))
        self.study = self.directory / "study"

    def plan(self, targets=None, *, repeats=1, fixtures=None, out=None):
        if targets is None:
            targets = [{"id": "mock", "host": "mock", "runner": "mock", "arms": ["B"], "prompt_breadths": ["narrow"]}]
        config = {
            "seed": 20261008,
            "split": "development",
            "fixtures": fixtures or ["dev-growth"],
            "repeats": repeats,
            "targets": targets,
        }
        config_path = self.directory / "config.json"
        runner.write_json(config_path, config)
        return runner.create_plan(config_path, out or self.study, root=self.root)

    def manual_attempt(self, arm="B"):
        plan = self.plan([{
            "id": "manual-codex", "host": "codex", "runner": "manual",
            "requested_model": "requested-placeholder", "arms": [arm], "prompt_breadths": ["narrow"],
        }])
        return runner.prepare_attempt(self.study, plan["runs"][0]["run_id"], root=self.root)

    def write_valid_outputs(self, attempt):
        packet = attempt / "packet"
        report = build_report(runner.read_json(packet / "fixture.json"))
        runner.write_json(packet / "report.json", report)
        (packet / "report.md").write_text(render_markdown(report), encoding="utf-8")

    def assert_raw_records(self, count):
        records = [json.loads(line) for line in (self.study / "results.jsonl").read_text().splitlines()]
        self.assertEqual(len(records), count)
        self.assertEqual(records, runner.collect_records(self.study))
        return records

    def cli(self, *arguments, expected_code=0):
        environment = dict(os.environ)
        environment["PYTHONPATH"] = str(self.root / "src")
        result = subprocess.run(
            [sys.executable, "-m", "cronbench.cli", *map(str, arguments)],
            cwd=self.root, env=environment, text=True, capture_output=True,
            check=False, timeout=30,
        )
        self.assertEqual(result.returncode, expected_code, result.stderr or result.stdout)
        return json.loads(result.stdout) if expected_code == 0 else result

    def test_stable_ids_and_reproducible_randomized_order(self):
        targets = [
            {"id": "pipeline", "host": "python", "runner": "baseline", "arms": ["A"]},
            {"id": "mock", "host": "mock", "runner": "mock", "arms": ["B", "C", "D", "E"]},
        ]
        fixtures = ["dev-growth", "dev-decline"]
        first = self.plan(targets, repeats=3, fixtures=fixtures)
        second = self.plan(targets, repeats=3, fixtures=fixtures, out=self.directory / "study-copy")
        self.assertEqual(first["study_id"], second["study_id"])
        self.assertEqual(first["runs"], second["runs"])
        ids = [run["run_id"] for run in first["runs"]]
        self.assertEqual(len(ids), 42)
        self.assertEqual(len(set(ids)), len(ids))
        breadths = {"A": ["none"], "B": ["narrow", "broad"], "C": ["narrow"], "D": ["broad"], "E": ["narrow", "broad"]}
        observed = [(r["target"]["id"], r["arm"], r["factors"]["prompt_breadth"], r["fixture_id"], r["repeat"]) for r in first["runs"]]
        canonical = [
            (target["id"], arm, breadth, fixture, repeat)
            for target in targets for arm in target["arms"]
            for breadth in breadths[arm]
            for fixture in sorted(fixtures) for repeat in range(1, 4)
        ]
        self.assertCountEqual(observed, canonical)
        self.assertNotEqual(observed, canonical, "Run order should be randomized before execution")
        pair_groups = {}
        for run in first["runs"]:
            key = (run["target"]["id"], run["fixture_id"], run["repeat"])
            pair_groups.setdefault(key, set()).add(run["pair_id"])
            self.assertIsInstance(run["factors"]["execution_style"], str)
            self.assertTrue(run["factors"]["execution_style"])
        self.assertEqual(len(pair_groups), 12)
        self.assertTrue(all(len(values) == 1 for values in pair_groups.values()))
        self.assertEqual(len(set.union(*pair_groups.values())), 12)
        with self.assertRaisesRegex(ValueError, "Study exists"):
            self.plan(targets)

    def test_prompt_breadth_restriction_applies_to_b_and_e_only(self):
        plan = self.plan([{
            "id": "restricted", "host": "mock", "runner": "mock",
            "arms": ["B", "C", "D", "E"], "prompt_breadths": ["broad"],
        }])
        self.assertEqual(len(plan["runs"]), 4)
        self.assertEqual(
            {run["arm"]: run["factors"]["prompt_breadth"] for run in plan["runs"]},
            {"B": "broad", "C": "narrow", "D": "broad", "E": "broad"},
        )
        self.assertEqual(len({run["pair_id"] for run in plan["runs"]}), 1)

    def test_factor_first_configuration_expands_to_seven_cells(self):
        plan = self.plan([
            {
                "id": "pipeline", "host": "python", "runner": "baseline",
                "execution_styles": ["deterministic_pipeline"], "prompt_breadths": ["none"],
            },
            {
                "id": "factor-mock", "host": "mock", "runner": "mock",
                "execution_styles": ["prepared_evidence", "tool_driven", "saved_script"],
                "prompt_breadths": ["narrow", "broad"],
            },
        ])
        expected = {
            ("deterministic_pipeline", "none"),
            ("prepared_evidence", "narrow"), ("prepared_evidence", "broad"),
            ("tool_driven", "narrow"), ("tool_driven", "broad"),
            ("saved_script", "narrow"), ("saved_script", "broad"),
        }
        self.assertEqual(len(plan["runs"]), 7)
        self.assertEqual({
            (run["factors"]["execution_style"], run["factors"]["prompt_breadth"])
            for run in plan["runs"]
        }, expected)
        subset = self.plan([{
            "id": "broad-tools", "host": "mock", "runner": "mock",
            "execution_styles": ["tool_driven"], "prompt_breadths": ["broad"],
        }], out=self.directory / "broad-only")
        self.assertEqual(len(subset["runs"]), 1)
        self.assertEqual(subset["runs"][0]["arm"], "D")
        self.assertEqual(subset["runs"][0]["factors"], {
            "execution_style": "tool_driven", "prompt_breadth": "broad",
        })
        with self.assertRaisesRegex(ValueError, "execution_styles or arms"):
            self.plan([{
                "id": "ambiguous", "host": "mock", "runner": "mock",
                "arms": ["B"], "execution_styles": ["prepared_evidence"],
            }], out=self.directory / "ambiguous")

    def test_fixture_checksum_alteration_is_detected(self):
        self.assertTrue(runner.verify(self.root)["verified"])
        fixture_path = self.root / "fixtures/development/dev-growth.json"
        fixture = runner.read_json(fixture_path)
        fixture["sources"]["search_console"]["current"]["clicks"] += 1
        runner.write_json(fixture_path, fixture)
        with self.assertRaisesRegex(ValueError, "dev-growth.json"):
            runner.verify(self.root)
        with self.assertRaisesRegex(ValueError, "integrity mismatch"):
            self.plan()

    def test_all_offline_arms_pass_and_resume_without_overwriting(self):
        targets = [
            {"id": "pipeline", "host": "python", "runner": "baseline", "arms": ["A"]},
            {"id": "mock", "host": "mock", "runner": "mock", "arms": ["B", "C", "D", "E"]},
        ]
        plan = self.plan(targets, fixtures=["dev-growth", "dev-retry"])
        first = runner.run_study(self.study, limit=3, root=self.root)
        self.assertEqual(len(first), 3)
        before = {p: p.read_bytes() for p in self.study.glob("runs/*/attempt-*/record.json")}
        rest = runner.run_study(self.study, root=self.root)
        records = first + rest
        self.assertEqual(len(records), len(plan["runs"]))
        planned_runs = {run["run_id"]: run for run in plan["runs"]}
        for record in records:
            with self.subTest(arm=record["arm"], fixture=record["fixture_id"]):
                self.assertEqual(record["status"], "completed", record)
                self.assertTrue(record["score"]["passed"], record["score"])
                self.assertEqual(record["attempt"], 1)
                self.assertEqual(record["factors"], planned_runs[record["run_id"]]["factors"])
                self.assertEqual(record["pair_id"], planned_runs[record["run_id"]]["pair_id"])
                if record["arm"] == "A":
                    self.assertEqual(record["usage"]["total_tokens"], 0)
                    self.assertEqual(record["usage"]["request_count"], 0)
                    self.assertFalse(record["mock"])
                else:
                    self.assertTrue(record["mock"])
                    self.assertEqual(record["usage"]["provenance"], "estimated")
                if record["fixture_id"] == "dev-retry":
                    self.assertGreater(record["tool_failures"], 0)
        for path, original in before.items():
            self.assertEqual(path.read_bytes(), original)
        self.assertEqual(runner.run_study(self.study, root=self.root), [])
        self.assert_raw_records(14)

    def test_quota_exhaustion_and_retry_are_retained_as_separate_attempts(self):
        plan = self.plan([{
            "id": "quota-mock", "host": "mock", "runner": "mock", "arms": ["B"], "prompt_breadths": ["narrow"],
            "mock_outcomes": ["quota_exhausted", "completed"],
        }])
        first = runner.run_study(self.study, root=self.root)[0]
        self.assertEqual(first["status"], "quota_exhausted")
        self.assertIsNone(first["score"])
        self.assertEqual(runner.run_study(self.study, root=self.root), [])
        second = runner.run_study(self.study, retry_failed=True, root=self.root)[0]
        self.assertEqual(first["run_id"], second["run_id"])
        self.assertEqual(second["run_id"], plan["runs"][0]["run_id"])
        self.assertEqual(second["attempt"], 2)
        self.assertEqual(second["status"], "completed")
        self.assertTrue(second["score"]["passed"])
        rows = self.assert_raw_records(2)
        self.assertEqual([row["status"] for row in rows], ["quota_exhausted", "completed"])
        self.assertEqual(runner.run_study(self.study, retry_failed=True, root=self.root), [])

    def test_missing_usage_stays_null_and_does_not_invent_actual_model(self):
        self.plan([{
            "id": "unknown", "host": "mock", "runner": "mock", "arms": ["B"], "prompt_breadths": ["narrow"],
            "requested_model": "requested-placeholder", "mock_missing_usage": True,
        }])
        record = runner.run_study(self.study, root=self.root)[0]
        self.assertTrue(record["score"]["passed"])
        for field in (*USAGE_FIELDS, "total_tokens"):
            self.assertIsNone(record["usage"][field], field)
        self.assertEqual(record["usage"]["provenance"], "unavailable")
        self.assertEqual(record["requested_model"], "requested-placeholder")
        self.assertIsNone(record["actual_model"])
        self.assertIsNone(record["actual_model_source"])

    def test_bad_mock_output_is_scored_failed_and_retained(self):
        self.plan([{
            "id": "bad", "host": "mock", "runner": "mock", "arms": ["B"], "prompt_breadths": ["narrow"],
            "mock_bad_output": True,
        }])
        record = runner.run_study(self.study, root=self.root)[0]
        self.assertEqual(record["status"], "completed")
        self.assertFalse(record["score"]["passed"])
        self.assert_raw_records(1)

    def test_packets_exclude_scorer_other_fixtures_and_shortcut_except_e(self):
        targets = [
            {"id": "pipeline", "host": "python", "runner": "baseline", "arms": ["A"]},
            {"id": "manual", "host": "codex", "runner": "manual", "arms": ["B", "C", "D", "E"]},
        ]
        plan = self.plan(targets)
        prompts_by_factor = {}
        for run in plan["runs"]:
            attempt = runner.prepare_attempt(self.study, run["run_id"], root=self.root)
            packet = attempt / "packet"
            names = {p.name for p in packet.rglob("*") if p.is_file()}
            with self.subTest(arm=run["arm"]):
                self.assertNotIn("scoring.py", names)
                self.assertNotIn("runner.py", names)
                self.assertFalse(any("holdout" in name or "heldout" in name for name in names))
                self.assertFalse(any(name.startswith("dev-") for name in names))
                self.assertEqual("baseline.py" in names, run["arm"] == "E")
                self.assertEqual((packet / "evidence.json").exists(), run["arm"] == "B")
                self.assertEqual(runner.read_json(packet / "fixture.json")["fixture_id"], run["fixture_id"])
                packet_run = runner.read_json(packet / "run.json")
                self.assertEqual(packet_run["factors"], run["factors"])
                prompts_by_factor[(run["arm"], run["factors"]["prompt_breadth"])] = (packet / "prompt.md").read_text()
                if run["arm"] != "E":
                    result = subprocess.run(
                        [sys.executable, str(packet / "tool.py"), "saved-report"],
                        cwd=packet, text=True, capture_output=True, check=False, timeout=10,
                    )
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("only in arm E", result.stdout)
        for arm in ("B", "E"):
            self.assertNotEqual(prompts_by_factor[(arm, "narrow")], prompts_by_factor[(arm, "broad")])

    def test_missing_import_outputs_are_retained_as_protocol_error(self):
        attempt = self.manual_attempt()
        record = runner.finalize(self.study, attempt, {}, root=self.root)
        self.assertEqual(record["status"], "protocol_error")
        self.assertIsNone(record["score"])
        self.assertTrue(any("missing output" in violation for violation in record["violations"]))
        self.assert_raw_records(1)
        with self.assertRaisesRegex(ValueError, "already finalized"):
            runner.finalize(self.study, attempt, {}, root=self.root)

    def test_tampered_packet_is_flagged_even_with_valid_report(self):
        attempt = self.manual_attempt()
        self.write_valid_outputs(attempt)
        with (attempt / "packet/prompt.md").open("a", encoding="utf-8") as stream:
            stream.write("\nTampered instructions\n")
        record = runner.finalize(self.study, attempt, {}, root=self.root)
        self.assertEqual(record["status"], "protocol_error")
        self.assertTrue(record["score"]["passed"])
        self.assertFalse(record["treatment_verified"])
        self.assertIn("Packet input modified: prompt.md", record["violations"])

    def test_unfinished_attempt_cannot_be_overwritten_or_implicitly_retried(self):
        plan = self.plan()
        run_id = plan["runs"][0]["run_id"]
        attempt = runner.prepare_attempt(self.study, run_id, root=self.root)
        before = (attempt / "attempt.json").read_bytes()
        with self.assertRaisesRegex(ValueError, "unfinished attempt"):
            runner.prepare_attempt(self.study, run_id, root=self.root)
        with self.assertRaisesRegex(ValueError, "unfinished attempt"):
            runner.run_study(self.study, retry_failed=True, root=self.root)
        self.assertEqual((attempt / "attempt.json").read_bytes(), before)
        self.assertEqual(len(list(attempt.parent.glob("attempt-*"))), 1)
        first = runner.finalize(self.study, attempt, {"status": "failed", "failure": {"kind": "interrupted"}}, root=self.root)
        self.assertEqual(first["failure"]["kind"], "interrupted")
        retry = runner.run_study(self.study, retry_failed=True, root=self.root)[0]
        self.assertEqual(retry["attempt"], 2)
        self.assertTrue(retry["score"]["passed"])

    def test_b_unknown_request_count_does_not_disqualify_valid_output(self):
        attempt = self.manual_attempt()
        self.write_valid_outputs(attempt)
        record = runner.finalize(self.study, attempt, {"fresh_context": True}, root=self.root)
        self.assertEqual(record["status"], "completed")
        self.assertTrue(record["score"]["passed"])
        self.assertIsNone(record["usage"]["request_count"])
        self.assertTrue(record["treatment_verified"])
        self.assertEqual(record["violations"], [])

    def test_b_multiple_requests_and_natural_tools_are_valid_observations(self):
        attempt = self.manual_attempt()
        runner.prepare_evidence(attempt / "packet")
        self.write_valid_outputs(attempt)
        record = runner.finalize(self.study, attempt, {
            "fresh_context": True,
            "usage": {"request_count": 2, "source": "synthetic-test-request-log"},
        }, root=self.root)
        self.assertEqual(record["status"], "completed")
        self.assertTrue(record["score"]["passed"])
        self.assertTrue(record["treatment_verified"])
        self.assertEqual(record["usage"]["request_count"], 2)
        self.assertGreater(record["low_level_tool_count"], 3)
        self.assertEqual(record["violations"], [])

    def test_exported_usage_is_preserved_without_guessing_request_count(self):
        attempt = self.manual_attempt()
        self.write_valid_outputs(attempt)
        artifact = self.directory / "host-export.jsonl"
        artifact.write_text(json.dumps({
            "type": "turn.completed", "usage": {
                "input_tokens": 100, "cached_input_tokens": 30, "output_tokens": 20,
            },
        }) + "\n", encoding="utf-8")
        record = runner.finalize(
            self.study, attempt, {"fresh_context": True},
            root=self.root, usage_artifact=artifact,
        )
        self.assertEqual((attempt / "usage.raw.txt").read_bytes(), artifact.read_bytes())
        self.assertEqual(record["usage"]["total_tokens"], 120)
        self.assertEqual(record["usage"]["cached_input_tokens"], 30)
        self.assertIsNone(record["usage"]["request_count"])
        self.assertIsNone(record["usage"]["reasoning_output_tokens"])
        self.assertIsNone(record["actual_model"])
        self.assertTrue(record["treatment_verified"])

    def test_actual_model_requires_provenance(self):
        attempt = self.manual_attempt()
        self.write_valid_outputs(attempt)
        with self.assertRaisesRegex(ValueError, "requires an exported source"):
            runner.finalize(self.study, attempt, {"actual_model": "invented"}, root=self.root)
        self.assertFalse((attempt / "record.json").exists())

    def test_unknown_host_routing_is_recorded_without_inventing_model_observations(self):
        attempt = self.manual_attempt()
        self.write_valid_outputs(attempt)
        record = runner.finalize(self.study, attempt, {"fresh_context": True}, root=self.root)
        self.assertEqual(record["configured_main_model"], "requested-placeholder")
        self.assertIsNone(record["configured_auxiliary_models"])
        self.assertIsNone(record["observed_models"])
        self.assertIsNone(record["observed_models_source"])
        self.assertIsNone(record["actual_model"])
        self.assertEqual(record["routing_mode"], "host_native_opaque")
        self.assertEqual(record["invocation_mode"], "fresh_context")
        self.assertIsNone(record["schedule_evidence"])

    def test_configured_and_observed_models_stay_distinct_for_routed_execution(self):
        plan = self.plan([{
            "id": "routed-host", "host": "codex", "runner": "manual",
            "arms": ["B"], "prompt_breadths": ["narrow"],
            "requested_model": "requested-placeholder",
            "configured_main_model": "configured-main-placeholder",
            "configured_auxiliary_models": ["configured-helper-placeholder"],
            "routing_mode": "explicit",
        }])
        attempt = runner.prepare_attempt(self.study, plan["runs"][0]["run_id"], root=self.root)
        self.write_valid_outputs(attempt)
        record = runner.finalize(self.study, attempt, {
            "fresh_context": True,
            "actual_model": "observed-main-placeholder",
            "actual_model_source": "synthetic-test-main-event",
            "observed_models": ["observed-main-placeholder", "observed-helper-placeholder"],
            "observed_models_source": "synthetic-test-routing-export",
            "usage": {"input_tokens": 100, "output_tokens": 20, "request_count": 2},
        }, root=self.root)
        self.assertEqual(record["status"], "completed")
        self.assertTrue(record["score"]["passed"])
        self.assertEqual(record["requested_model"], "requested-placeholder")
        self.assertEqual(record["configured_main_model"], "configured-main-placeholder")
        self.assertEqual(record["configured_auxiliary_models"], ["configured-helper-placeholder"])
        self.assertEqual(record["observed_models"], ["observed-main-placeholder", "observed-helper-placeholder"])
        self.assertEqual(record["observed_models_source"], "synthetic-test-routing-export")
        self.assertEqual(record["routing_mode"], "explicit")
        self.assertEqual(record["usage"]["total_tokens"], 120)
        self.assertIsNone(record["actual_model"], "Aggregate routed usage must not be attributed to the main model alone")
        self.assertIsNone(record["actual_model_source"])

    def test_observed_models_require_exported_provenance(self):
        attempt = self.manual_attempt()
        self.write_valid_outputs(attempt)
        with self.assertRaisesRegex(ValueError, "Observed models require an exported source"):
            runner.finalize(self.study, attempt, {"observed_models": ["unverified-placeholder"]}, root=self.root)
        self.assertFalse((attempt / "record.json").exists())

    def test_conflicting_exported_model_ids_warn_without_failing_valid_report(self):
        attempt = self.manual_attempt()
        self.write_valid_outputs(attempt)
        record = runner.finalize(self.study, attempt, {
            "fresh_context": True,
            "actual_model": "model-A",
            "actual_model_source": "synthetic-test-primary-export",
            "observed_models": ["model-B"],
            "observed_models_source": "synthetic-test-observation-export",
            "usage": {"input_tokens": 100, "output_tokens": 20, "request_count": 2},
        }, root=self.root)
        self.assertEqual(record["status"], "completed")
        self.assertTrue(record["score"]["passed"])
        self.assertTrue(record["treatment_verified"])
        self.assertEqual(record["violations"], [])
        self.assertIsNone(record["actual_model"])
        self.assertIsNone(record["actual_model_source"])
        self.assertEqual(record["observed_models"], ["model-B"])
        self.assertTrue(record["observation_warnings"])
        self.cli("aggregate", "--study", self.study)
        aggregate = runner.read_json(self.study / "summary/aggregate.json")
        self.assertIsNone(aggregate["attempt_costs"][0]["runtime"]["total_usd"])

    def test_provenance_without_model_ids_does_not_invent_model_observations(self):
        attempt = self.manual_attempt()
        self.write_valid_outputs(attempt)
        record = runner.finalize(self.study, attempt, {
            "fresh_context": True,
            "actual_model": None, "actual_model_source": "synthetic-export-with-no-model-id",
            "observed_models": None, "observed_models_source": "synthetic-export-with-no-routing-ids",
        }, root=self.root)
        self.assertEqual(record["status"], "completed")
        self.assertIsNone(record["actual_model"])
        self.assertIsNone(record["actual_model_source"])
        self.assertIsNone(record["observed_models"])

    def test_scheduled_invocation_requires_and_retains_execution_evidence(self):
        attempt = self.manual_attempt()
        self.write_valid_outputs(attempt)
        metadata = {"fresh_context": True, "invocation_mode": "scheduled"}
        with self.assertRaisesRegex(ValueError, "requires schedule_evidence"):
            runner.finalize(self.study, attempt, metadata, root=self.root)
        self.assertFalse((attempt / "record.json").exists())
        metadata["schedule_evidence"] = "synthetic-test-scheduler-export"
        record = runner.finalize(self.study, attempt, metadata, root=self.root)
        self.assertEqual(record["status"], "completed")
        self.assertEqual(record["invocation_mode"], "scheduled")
        self.assertEqual(record["schedule_evidence"], "synthetic-test-scheduler-export")

    def test_command_timeout_is_retained_and_offline_mode_never_launches_it(self):
        self.plan([{
            "id": "local-sleeper", "host": "mock-command", "runner": "command",
            "arms": ["B"], "prompt_breadths": ["narrow"], "billing_route": "subscription", "timeout_seconds": 0.05,
            "argv": [sys.executable, "-c", "import time; time.sleep(10)"],
        }])
        self.assertEqual(runner.run_study(self.study, mode="offline", root=self.root), [])
        self.assertFalse((self.study / "runs").exists())
        record = runner.run_study(self.study, mode="command", root=self.root)[0]
        self.assertEqual(record["status"], "timeout")
        self.assertEqual(record["failure"]["kind"], "timeout")
        self.assertLess(record["latency_seconds"], 5)
        self.assertIsNone(record["usage"]["total_tokens"])
        self.assert_raw_records(1)

    def test_missing_command_executable_is_retained(self):
        self.plan([{
            "id": "missing-command", "host": "mock-command", "runner": "command",
            "arms": ["B"], "prompt_breadths": ["narrow"], "billing_route": "subscription",
            "argv": [str(self.directory / "definitely-does-not-exist")],
        }])
        record = runner.run_study(self.study, mode="command", root=self.root)[0]
        self.assertEqual(record["status"], "failed")
        self.assertEqual(record["failure"]["kind"], "FileNotFoundError")
        self.assertIsNone(record["usage"]["total_tokens"])
        self.assert_raw_records(1)

    def test_command_preserves_explicit_usage_when_stdout_has_no_usage_mapping(self):
        metadata = {
            "status": "quota_exhausted",
            "usage": {
                "input_tokens": 100, "output_tokens": 20, "request_count": 1,
                "provenance": "measured", "source": "synthetic-test-export",
            },
        }
        script = (
            "from pathlib import Path; "
            f"Path('metadata.json').write_text({json.dumps(metadata)!r}); "
            "print('Synthetic command diagnostic, no native usage export')"
        )
        self.plan([{
            "id": "metadata-command", "host": "mock-command", "runner": "command",
            "arms": ["B"], "prompt_breadths": ["narrow"], "billing_route": "subscription",
            "argv": [sys.executable, "-c", script],
        }])
        record = runner.run_study(self.study, mode="command", root=self.root)[0]
        self.assertEqual(record["status"], "quota_exhausted")
        self.assertEqual(record["usage"]["input_tokens"], 100)
        self.assertEqual(record["usage"]["output_tokens"], 20)
        self.assertEqual(record["usage"]["request_count"], 1)
        self.assertEqual(record["usage"]["source"], "synthetic-test-export")
        self.assertEqual(record["usage"]["total_tokens"], 120)
        self.assertIsNone(record["actual_model"])

    def test_malformed_tool_events_retain_failed_command_and_raw_artifact(self):
        payloads = (
            '{"tool": "fetch"',
            'null\n',
            '{}\n',
            '{"tool": "fetch", "status": "ok"}\n{"tool":',
        )
        for index, payload in enumerate(payloads):
            with self.subTest(payload=payload):
                self.study = self.directory / f"malformed-events-{index}"
                script = (
                    "from pathlib import Path; import sys; "
                    f"Path('tool_events.jsonl').write_text({payload!r}); "
                    "sys.exit(1)"
                )
                plan = self.plan([{
                    "id": "broken-events", "host": "mock-command", "runner": "command",
                    "arms": ["B"], "prompt_breadths": ["narrow"], "billing_route": "subscription",
                    "argv": [sys.executable, "-c", script],
                }])
                records = runner.run_study(self.study, mode="command", root=self.root)
                self.assertEqual(len(records), 1)
                record = records[0]
                self.assertEqual(record["status"], "failed")
                self.assertEqual(record["failure"]["kind"], "process_exit")
                self.assertEqual(record["failure"]["returncode"], 1)
                self.assertTrue(record["violations"])
                attempt = self.study / "runs" / plan["runs"][0]["run_id"] / "attempt-001"
                raw_artifact = attempt / "packet/tool_events.jsonl"
                self.assertEqual(raw_artifact.read_text(), payload)
                self.assertEqual(record["artifacts"]["packet/tool_events.jsonl"], runner.digest(raw_artifact))
                self.assert_raw_records(1)

    def test_malformed_command_metadata_is_retained_and_preserves_process_outcome(self):
        cases = [
            (payload, exit_code, False)
            for payload in ("null", "[]", '"text"', "3", "true", '{"status":')
            for exit_code in (0, 1)
        ]
        cases.append(("null", 0, True))
        for index, (payload, exit_code, times_out) in enumerate(cases):
            with self.subTest(payload=payload, exit_code=exit_code, times_out=times_out):
                self.study = self.directory / f"malformed-metadata-{index}"
                script = (
                    "from pathlib import Path; import sys, time; "
                    f"Path('metadata.json').write_text({payload!r}); "
                    + ("time.sleep(5); " if times_out else "")
                    + f"sys.exit({exit_code})"
                )
                plan = self.plan([{
                    "id": "broken-metadata", "host": "mock-command", "runner": "command",
                    "arms": ["B"], "prompt_breadths": ["narrow"], "billing_route": "subscription",
                    "timeout_seconds": 0.5 if times_out else 5,
                    "argv": [sys.executable, "-c", script],
                }])
                records = runner.run_study(self.study, mode="command", root=self.root)
                self.assertEqual(len(records), 1)
                record = records[0]
                expected_status = "timeout" if times_out else "failed" if exit_code else "protocol_error"
                self.assertEqual(record["status"], expected_status)
                self.assertTrue(record["metadata_errors"])
                self.assertIsNone(record["actual_model"])
                self.assertIsNone(record["usage"]["total_tokens"])
                if times_out:
                    self.assertEqual(record["failure"]["kind"], "timeout")
                elif exit_code:
                    self.assertEqual(record["failure"]["returncode"], exit_code)
                attempt = self.study / "runs" / plan["runs"][0]["run_id"] / "attempt-001"
                raw_artifact = attempt / "packet/metadata.json"
                self.assertEqual(raw_artifact.read_text(), payload)
                self.assertEqual(record["artifacts"]["packet/metadata.json"], runner.digest(raw_artifact))
                self.assert_raw_records(1)

    def test_cli_copied_checkout_plan_run_status_aggregate_and_review(self):
        self.plan([
            {"id": "pipeline", "host": "python", "runner": "baseline", "arms": ["A"]},
            {"id": "mock", "host": "mock", "runner": "mock", "arms": ["B"], "prompt_breadths": ["narrow"]},
        ])
        self.study = self.directory / "cli-study"
        planned = self.cli("plan", "--config", self.directory / "config.json", "--out", self.study)
        self.assertEqual(planned["runs"], 2)
        self.assertTrue(self.cli("verify")["verified"])
        before = self.cli("status", "--study", self.study)
        self.assertEqual(before["recorded_attempts"], 0)
        executed = self.cli("run", "--study", self.study, "--mode", "offline")
        self.assertEqual(executed["executed"], 2)
        self.assertTrue(all(outcome["passed"] for outcome in executed["outcomes"]))
        self.assertEqual(self.cli("run", "--study", self.study)["executed"], 0)
        after = self.cli("status", "--study", self.study)
        self.assertEqual(after["recorded_attempts"], 2)
        summary = self.cli("aggregate", "--study", self.study)
        self.assertEqual(summary["study_completion"]["pending_runs"], 0)
        aggregate = runner.read_json(self.study / "summary/aggregate.json")
        self.assertEqual(aggregate["overall"]["attempts"]["passing_count"], 2)
        self.assertTrue((self.study / "summary/aggregate.md").is_file())
        review_directory = self.directory / "blinded-review"
        review = self.cli("review-export", "--study", self.study, "--out", review_directory)
        self.assertEqual(review["reports"], 2)
        self.assertEqual(len(list(review_directory.glob("review-*/report.json"))), 2)
        self.assertTrue((review_directory / "ratings.csv").is_file())
        self.assertTrue((self.study / "review-key.private.json").is_file())
        self.assertFalse((review_directory / "review-key.private.json").exists())
        self.assert_raw_records(2)

    def test_cli_manual_export_and_import_preserves_failure(self):
        plan = self.plan([{
            "id": "manual-codex", "host": "codex", "runner": "manual", "arms": ["B"], "prompt_breadths": ["narrow"],
        }])
        run_id = plan["runs"][0]["run_id"]
        exported = self.cli("export", "--study", self.study, "--run-id", run_id)
        self.assertEqual(exported["attempt"], 1)
        self.assertTrue((Path(exported["packet"]) / "prompt.md").is_file())
        metadata = self.directory / "interrupted.metadata.json"
        runner.write_json(metadata, {
            "status": "quota_exhausted", "failure": {"kind": "synthetic-test-quota"},
        })
        imported = self.cli(
            "import", "--study", self.study, "--run-id", run_id,
            "--attempt", "1", "--metadata", metadata,
        )
        self.assertEqual(imported["status"], "quota_exhausted")
        self.assertIsNone(imported["usage"]["total_tokens"])
        self.assert_raw_records(1)
        result = self.cli(
            "import", "--study", self.study, "--run-id", run_id,
            "--attempt", "1", "--metadata", metadata, expected_code=2,
        )
        self.assertIn("already finalized", result.stderr)

    def test_cli_rejects_integrity_changes_and_nonpositive_limits(self):
        self.plan()
        invalid_limit = self.cli("run", "--study", self.study, "--limit", "0", expected_code=2)
        self.assertIn("must be positive", invalid_limit.stderr)
        with (self.root / "fixtures/development/dev-growth.json").open("a", encoding="utf-8") as stream:
            stream.write("\n")
        changed = self.cli("verify", expected_code=2)
        self.assertIn("integrity mismatch", changed.stderr)

    def test_offline_install_from_clean_copy_needs_no_packages_and_protects_existing_files(self):
        environment = {key: value for key, value in os.environ.items() if key != "PYTHONPATH"}
        environment["PYTHONNOUSERSITE"] = "1"
        virtual_environment = self.directory / "clean-venv"
        command = [sys.executable, str(self.root / "scripts/install.py"), "--venv", str(virtual_environment)]
        installed = subprocess.run(
            command, cwd=self.root, env=environment, text=True, capture_output=True,
            check=False, timeout=30,
        )
        self.assertEqual(installed.returncode, 0, installed.stderr)
        launcher = virtual_environment / "bin/cronbench"
        original = launcher.read_bytes()
        self.assertFalse((virtual_environment / "bin/pip").exists())
        verified = subprocess.run(
            [str(launcher), "verify"], cwd=self.directory, env=environment,
            text=True, capture_output=True, check=False, timeout=10,
        )
        self.assertEqual(verified.returncode, 0, verified.stderr)
        self.assertTrue(json.loads(verified.stdout)["verified"])
        repeated = subprocess.run(
            command, cwd=self.root, env=environment, text=True, capture_output=True,
            check=False, timeout=10,
        )
        self.assertNotEqual(repeated.returncode, 0)
        self.assertIn("existing files are never overwritten", repeated.stderr)
        self.assertEqual(launcher.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
