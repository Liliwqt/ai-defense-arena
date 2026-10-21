"""Synthetic replay comparison for the content-free operation timing harness."""

import json
import tempfile
import unittest
from pathlib import Path

from tests.operation_timing_harness import (
    SyntheticDefenseCase, compare, parse_records, read_records, replay,
    run_synthetic_defense, summarize,
)


def record(event, kind, duration_ms, *, stage=None, outcome="succeeded", **extra):
    item = {"event": event, "kind": kind, "duration_ms": duration_ms, "outcome": outcome,
            "operation_id": f"{kind}:1"}
    if stage:
        item["stage"] = stage
    item.update(extra)
    return item


class OperationTimingHarnessTests(unittest.TestCase):
    def test_replay_aggregates_stages_outcomes_and_missing_usage_separately(self):
        records = parse_records([
            json.dumps(record("stage", "question", 1000, stage="generating")),
            "operation_timing " + json.dumps(record(
                "total", "question", 1200, outcome="failed", failure_class="APIStatusError",
                input_tokens=10)),
            json.dumps(record("total", "question", 800, cost_nano=None)),
        ])
        summary = replay(records)
        stage = summary["stage:question:generating"]
        self.assertEqual(stage["count"], 1)
        self.assertEqual(stage["usage"]["input_tokens"],
                         {"sum": None, "known_records": 0, "unknown_records": 1})
        total = summary["total:question"]
        self.assertEqual(total["outcomes"], {"failed": 1, "succeeded": 1})
        self.assertEqual(total["failure_classes"], {"APIStatusError": 1})
        self.assertEqual(total["duration_ms"]["median"], 1000)
        self.assertEqual(total["usage"]["input_tokens"],
                         {"sum": 10, "known_records": 1, "unknown_records": 1})
        self.assertIsNone(total["usage"]["cost_nano"]["sum"])
        self.assertEqual(total["usage"]["cost_nano"]["unknown_records"], 2)

    def test_compare_reports_stage_deltas_without_claiming_speed(self):
        baseline = [record("total", "question", 1200),
                    record("stage", "mapping", 500, stage="preparing")]
        candidate = [record("total", "question", 900),
                     record("stage", "mapping", 400, stage="preparing"),
                     record("total", "coaching", 300)]
        result = compare(baseline, candidate)
        self.assertEqual(result["groups"]["total:question"]["median_delta_ms"], -300)
        self.assertEqual(result["groups"]["stage:mapping:preparing"]["median_delta_ms"], -100)
        self.assertEqual(result["only_in_candidate"], ["total:coaching"])
        self.assertEqual(result["only_in_baseline"], [])

    def test_unknown_groups_are_not_zero_filled(self):
        result = compare([record("stage", "mapping", 500, stage="preparing")],
                         [record("stage", "coaching", 400, stage="answers")])
        self.assertEqual(result["only_in_baseline"], ["stage:mapping:preparing"])
        self.assertEqual(result["only_in_candidate"], ["stage:coaching:answers"])
        self.assertIsNone(result["groups"]["stage:mapping:preparing"]["median_delta_ms"])

    def test_invalid_records_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "unknown event"):
            parse_records([json.dumps({"event": "prompt", "kind": "question",
                                       "duration_ms": 1, "outcome": "succeeded"})])
        with self.assertRaisesRegex(ValueError, "duration_ms"):
            parse_records([json.dumps({"event": "total", "kind": "question",
                                       "duration_ms": -1, "outcome": "succeeded"})])
        with self.assertRaisesRegex(ValueError, "valid JSON"):
            parse_records(["{"])

    def test_reads_log_prefixed_files(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder, "timing.jsonl")
            path.write_text("\n".join([
                "operation_timing " + json.dumps(record("total", "question", 10)),
                "",
            ]), encoding="utf-8")
            self.assertEqual(len(read_records([str(path)])), 1)

    def test_summary_ignores_extra_private_fields(self):
        summary = summarize([record("total", "question", 10,
                                    prompt="private", answer="private", api_key="secret")])
        serialized = json.dumps(summary)
        self.assertNotIn("private", serialized)
        self.assertNotIn("secret", serialized)


class SyntheticReplayTests(unittest.IsolatedAsyncioTestCase):
    async def test_synthetic_defense_runs_the_workflows_and_emits_linked_cases(self):
        case = SyntheticDefenseCase("case-a", "synthetic.py", "value = 1\n",
                                    "The synthetic value is retained.", 300, 200)
        records = await run_synthetic_defense(case, "baseline")
        self.assertTrue(records)
        self.assertEqual({record["case_id"] for record in records}, {"case-a"})
        self.assertEqual({record["condition"] for record in records}, {"baseline"})
        self.assertEqual({record["run_id"] for record in records}, {"baseline:case-a"})
        kinds = {record["kind"] for record in records}
        self.assertEqual(kinds, {"mapping", "question", "interpretation", "coaching"})
        outcomes = {(record["kind"], record["outcome"]) for record in records
                    if record["event"] == "total"}
        self.assertEqual(outcomes, {(kind, "succeeded") for kind in kinds})
        questions = [record for record in records
                     if record["event"] == "total" and record["kind"] == "question"]
        interpretations = [record for record in records
                           if record["event"] == "total" and record["kind"] == "interpretation"]
        self.assertEqual(len(questions), 5)  # Opening, three planned writers, and final completion.
        self.assertEqual([record["duration_ms"] for record in questions], [600, 300, 300, 300, 0])
        self.assertEqual([record["duration_ms"] for record in interpretations], [200]*4)
        self.assertTrue(all(record.get("input_tokens") for record in questions[:-1]))
        self.assertFalse(questions[-1].get("input_tokens"))
        serialized = json.dumps(records)
        self.assertNotIn(case.source_text.strip(), serialized)
        self.assertNotIn(case.answer, serialized)

    async def test_research_and_mixed_execute_funded_planning_and_complete_coaching(self):
        from unittest.mock import patch
        from backend.defense_session import ResearchDefenseSession
        from backend.openrouter_questions import RunQuestionClient
        from tests.operation_timing_harness import DEFAULT_SYNTHETIC_CASES

        original = RunQuestionClient.research_move
        with patch.object(RunQuestionClient, "research_move", autospec=True,
                          side_effect=original) as generate:
            for case in DEFAULT_SYNTHETIC_CASES:
                records = await run_synthetic_defense(case, "baseline")
                self.assertEqual({record["defense_type"] for record in records}, {case.defense_type})
                coaching = next(record for record in records
                                if record["event"] == "total" and record["kind"] == "coaching")
                self.assertEqual(coaching["outcome"], "succeeded")
                self.assertIn("saving_completion", [record["stage"] for record in records])
        self.assertEqual({call.kwargs["defense_type"] for call in generate.call_args_list},
                         {"research", "mixed"})
        self.assertEqual(generate.call_count, 10)
        self.assertTrue(all(isinstance(call.args[0].session, ResearchDefenseSession)
                            for call in generate.call_args_list))

    async def test_case_aware_comparison_does_not_mix_unrelated_cases(self):
        case = SyntheticDefenseCase("case-a", "synthetic.py", "value = 1\n",
                                    "The synthetic value is retained.", 300, 200)
        baseline = await run_synthetic_defense(case, "baseline")
        candidate = await run_synthetic_defense(case, "candidate", latency_scale=2)
        other = await run_synthetic_defense(
            SyntheticDefenseCase("case-b", "other.py", "value = 2\n", "A second answer."),
            "candidate")
        result = compare(baseline, candidate + other)
        self.assertEqual(result["conditions"], {
            "baseline": ["baseline"], "candidate": ["candidate"]})
        self.assertEqual(result["only_in_baseline_cases"], [])
        self.assertEqual(result["only_in_candidate_cases"], ["case-b"])
        question = result["cases"]["case-a"]["groups"]["total:question"]
        self.assertEqual(question["median_delta_ms"], 300)

    async def test_comparison_rejects_same_case_id_with_changed_sources_or_answers(self):
        from dataclasses import replace
        from tests.operation_timing_harness import DEFAULT_SYNTHETIC_CASES

        case = DEFAULT_SYNTHETIC_CASES[0]
        baseline = await run_synthetic_defense(case, "baseline")
        for changed in (replace(case, source_text="A different proposal."),
                        replace(case, answer="A different answer.")):
            candidate = await run_synthetic_defense(changed, "candidate")
            with self.assertRaisesRegex(ValueError, "identical synthetic inputs"):
                compare(baseline, candidate)


if __name__ == "__main__":
    unittest.main()
