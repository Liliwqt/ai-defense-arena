"""Content-free timing comparison/replay harness for synthetic operation records.

The replay/summary path reads content-free records from `backend.room_operations`.
The executable runner uses only explicit synthetic inputs, a temporary local
database and mocked provider HTTP; its exported records contain no input text.

Mocked timings establish instrumentation and comparable structure. They are not a
real speed result; actual inference and quality remain a separate gate.
"""

from __future__ import annotations

import argparse
import asyncio
from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import json
import math
import os
import re
import statistics
import sys
import tempfile
from collections import Counter
from pathlib import Path
from unittest.mock import patch

USAGE_FIELDS = ("input_tokens", "output_tokens", "reasoning_tokens", "cost_nano")
VALID_EVENTS = {"stage", "total"}


@dataclass(frozen=True)
class SyntheticDefenseCase:
    case_id: str
    source_name: str
    source_text: str
    answer: str
    question_ms: int = 250
    interpretation_ms: int = 150
    start_ms: int = 1_000
    defense_type: str = "research"
    mapping_ms: int = 400
    coaching_ms: int = 200

    @property
    def fingerprint(self) -> str:
        data = [self.source_name, self.source_text, self.answer, self.defense_type]
        return hashlib.sha256(json.dumps(data, ensure_ascii=False).encode()).hexdigest()


DEFAULT_SYNTHETIC_CASES = (
    SyntheticDefenseCase(
        "synthetic-research",
        "synthetic_paper.md",
        "The proposal compares campus queue waiting times with consenting volunteers.\n",
        "We will limit the comparison to the campus pilot and explain that limitation.",
    ),
    SyntheticDefenseCase(
        "synthetic-mixed", "synthetic_paper.md",
        "The proposal compares campus queue waiting times with a software prototype.\n",
        "The prototype supports a bounded campus comparison rather than a general claim.",
        defense_type="mixed",
    ),
)


class SyntheticClock:
    def __init__(self, now_ms: int):
        self.now_ms = now_ms

    def now(self) -> int:
        return self.now_ms

    def advance(self, milliseconds: int) -> None:
        self.now_ms += max(0, milliseconds)


class _CollectingSink:
    def __init__(self):
        self.records = []

    def emit(self, record):
        self.records.append(record)


def parse_records(lines) -> list[dict]:
    records = []
    for number, line in enumerate(lines, 1):
        text = line.strip()
        if not text:
            continue
        if text.startswith("operation_timing "):
            text = text[len("operation_timing "):]
        try:
            record = json.loads(text)
        except json.JSONDecodeError as error:
            raise ValueError(f"line {number} is not valid JSON: {error.msg}") from error
        if not isinstance(record, dict):
            raise ValueError(f"line {number} is not an object")
        if record.get("event") not in VALID_EVENTS:
            raise ValueError(f"line {number} has an unknown event")
        if not isinstance(record.get("kind"), str) or not record["kind"]:
            raise ValueError(f"line {number} has no operation kind")
        if type(record.get("duration_ms")) is not int or record["duration_ms"] < 0:
            raise ValueError(f"line {number} has no valid duration_ms")
        if not isinstance(record.get("outcome"), str) or not record["outcome"]:
            raise ValueError(f"line {number} has no outcome")
        records.append(record)
    return records


def _annotate(records, case: SyntheticDefenseCase, condition: str, run_id: str):
    return [{**record, "case_id": case.case_id, "case_fingerprint": case.fingerprint,
             "defense_type": case.defense_type, "condition": condition, "run_id": run_id}
            for record in records]


class _SyntheticProvider:
    """Structured SSE fixtures at the actual funded HTTP boundary."""

    def __init__(self, case, clock, latency_scale):
        self.case, self.clock, self.scale = case, clock, latency_scale
        self.room = None

    def __call__(self, request):
        import httpx
        from backend.question_generator import RESEARCH_PANELISTS
        from tests.research_coaching_fixtures import cards_for

        body = json.loads(request.content)
        name = body["response_format"]["json_schema"]["name"]
        content = body["messages"][-1]["content"]
        if name == "ResearchPlanDraft":
            milliseconds = self.case.mapping_ms
            output = {"topics": [
                {"title": title, "objective": "Explain the proposal's " + title.lower(),
                 "panelist": role, "references": [{"source_file": 1, "evidence_line": 1}],
                 "gaps": []}
                for title, role in zip(("Study design", "Participant safeguards", "Expected impact",
                                        "Limitations"), RESEARCH_PANELISTS)],
                "uncertainties": [],
                "profile": {"fields": ["Research methods"], "approaches": ["quantitative"],
                            "setting": "Campus pilot", "explanation": "A bounded proposal comparison.",
                            "references": [{"source_file": 1, "evidence_line": 1}], "uncertainties": []}}
        elif name in {"PlanDraft", "QuestionDraft"}:
            milliseconds = self.case.question_ms
            context = json.JSONDecoder().raw_decode(
                content.split("Server research context (data):\n")[1])[0]
            previous = context["previous_turn"]
            if name == "PlanDraft":
                assessment = None if previous is None else {
                    "turn": previous, "topic_id": context["previous_topic"], "status": "discussed",
                    "reason": "The defender explained a bounded proposal decision."}
                complete = context["budget_exhausted"]
                output = {"action": "complete" if complete else "ask", "assessment": assessment,
                          **({"panelist": None, "topic_id": None, "is_follow_up": False} if complete
                             else next(option for option in context["question_options"]
                                       if not option["is_follow_up"]))}
            else:
                output = {"lead_in": "", "question": f"How will you justify proposal decision {context['generated_questions']+1}?",
                          "source_file": 2 if self.case.defense_type == "mixed" and previous is not None else 1,
                          "evidence_line": 1}
        elif name in {"SubmissionDraft", "CombinedSubmissionDraft"}:
            milliseconds = self.case.interpretation_ms
            output = {"action": "answer", "clarification": None, "probe": None}
            if name == "CombinedSubmissionDraft":
                context = json.JSONDecoder().raw_decode(
                    content.split("Planning context (data):\n")[1])[0]
                previous = context["previous_turn"]
                assessment = None if previous is None else {
                    "turn": previous, "topic_id": context["previous_topic"], "status": "discussed",
                    "reason": "The defender explained a bounded proposal decision."}
                complete = context["budget_exhausted"]
                output.update(assessment=assessment,
                              **({"panelist": None, "topic_id": None, "is_follow_up": False} if complete
                                 else next(option for option in context["question_options"]
                                           if not option["is_follow_up"])))
        elif name in {"CoachingDraft", "ResearchCoachingDraft"}:
            milliseconds = self.case.coaching_ms
            output = {"summary": "The team discussed the proposal's scope.", "strengths": [],
                      "improvements": [], "next_step": "Practice explaining the limits.", "closing": ""}
            if name == "ResearchCoachingDraft":
                match = re.search(r"only these required zero-based turn indices: (\[[0-9, ]+\])",
                                  body["messages"][0]["content"])
                if match is None:
                    raise AssertionError("Synthetic coaching request omitted section membership")
                turns = json.loads(match.group(1))
                output["answer_cards"] = [card for card in cards_for(self.room.defense.coaching_history())
                                          if card["turn"] in turns]
        else:
            raise AssertionError(f"Unexpected synthetic provider schema: {name}")
        self.clock.advance(round(milliseconds * self.scale))
        events = [
            {"choices": [{"index": 0, "delta": {"content": json.dumps(output)}, "finish_reason": None}]},
            {"choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]},
            {"choices": [], "usage": {"prompt_tokens": 500, "completion_tokens": 300, "cost": 0.0005}},
        ]
        return httpx.Response(200, text="".join("data: " + json.dumps(event) + "\n\n"
                                              for event in events) + "data: [DONE]\n\n")


@contextmanager
def _synthetic_environment(provider):
    import httpx
    from backend import account_store

    http_client = httpx.Client
    with tempfile.TemporaryDirectory(prefix="operation-timing-") as folder, patch.dict(os.environ, {
        "DATABASE_URL": "", "PAYMENTS_MODE": "test",
        "PAYMONGO_TEST_DB_PATH": str(Path(folder) / "synthetic.sqlite3"),
        "AUTH_SESSION_SECRET": "synthetic-session-secret-not-a-real-credential",
        "AUTH_PUBLIC_BASE_URL": "http://127.0.0.1:8000",
        "FREE_ACCESS_VOUCHER": "synthetic-timing-voucher",
        "OPENROUTER_API_KEY": "synthetic-not-a-real-key",
        "OPENROUTER_RUN_USD": "5", "OPENROUTER_PREPARATION_USD": "0.75",
        "OPENROUTER_MAPPING_MODEL": "z-ai/glm-5.3-flash",
        "OPENROUTER_MAPPING_REASONING_EFFORT": "low",
        "OPENROUTER_MAPPING_MAX_OUTPUT_TOKENS": "65536", "AI_OWNER_PER_MINUTE": "1000",
    }), patch("httpx.Client", side_effect=lambda **kwargs: http_client(
        transport=httpx.MockTransport(provider))):
        token, _ = account_store.create_google_session("synthetic-host", "host@example.test", "Host")
        account = account_store.session_account(token)
        account_store.redeem_voucher(account["id"], "synthetic-timing-voucher")
        yield account["id"]


async def run_synthetic_defense(case: SyntheticDefenseCase, condition: str, *,
                                latency_scale: float = 1.0,
                                run_id: str | None = None) -> list[dict]:
    from backend.project_files import ProjectFile
    from backend.room_operations import install_timing_sink, reset_timing_sink
    from backend.rooms.coordinator import RoomCoordinator, RoomWorkflows
    from backend.rooms.model import Player, Room
    from backend.rooms.commands import CatchUpDeadline, VerifiedActor, decode_command
    from tests.async_room import wait_until

    if case.defense_type not in {"research", "mixed"}:
        raise ValueError("Synthetic timing cases must use research or mixed defenses")
    if not case.source_text.strip():
        raise ValueError("Synthetic timing cases require nonempty source text")

    sink = _CollectingSink()
    install_timing_sink(sink)
    clock = SyntheticClock(case.start_ms)
    provider = _SyntheticProvider(case, clock, latency_scale)

    async def wait(seconds):
        await asyncio.Event().wait()

    async def deliver(socket, payload):
        return None

    try:
        with _synthetic_environment(provider) as account_id:
            host = Player("synthetic-host", "Synthetic Host", 0, True, {object()})
            guest = Player("synthetic-defender", "Synthetic Defender", 1, sockets={object()})
            files = [ProjectFile(case.source_name, case.source_text, "research_text")]
            if case.defense_type == "mixed":
                files.append(ProjectFile("synthetic_queue.py", "queue = []\n"))
            room = Room("SYNTH", files, {host.token: host, guest.token: guest},
                        defense_type=case.defense_type, research_stage="proposal", owner_account_id=account_id)
            provider.room = room
            coordinator = RoomCoordinator(room, RoomWorkflows(deliver=deliver, now=clock.now, sleep=wait))
            actors = [VerifiedActor(host.token, account_id), VerifiedActor(guest.token)]

            async def command(message, actor=actors[0]):
                result = await coordinator.execute(decode_command(message), actor)
                if not result.accepted:
                    raise AssertionError(f"Synthetic command rejected: {result.error}")

            async def ready(predicate):
                await wait_until(lambda: predicate() or bool(room.error) or bool(room.research_plan_error), timeout=5)
                if room.error or room.research_plan_error:
                    raise AssertionError(room.error or room.research_plan_error)

            try:
                await command({"type": "prepare_research_plan"})
                await ready(lambda: room.research_planning_status == "ready")
                await command({"type": "approve_research_plan", "plan_id": room.research_plan.id,
                               "question_budget": 4, "confirm_profile": True})
                await command({"type": "start", "plan_id": room.research_plan.id,
                               "question_budget": 4, "confirm_cost": True})
                for index in range(4):
                    await ready(lambda: room.phase == "voting")
                    for actor in actors:
                        await command({"type": "cast_vote", "seat": index % 2}, actor)
                    clock.advance(room.vote_deadline_ms - clock.now())
                    await coordinator.execute(CatchUpDeadline())
                    await command({"type": "submit_answer", "turn": index, "answer": case.answer},
                                  actors[index % 2])
                await ready(lambda: room.feedback_status == "ready")
                if not room.settled or len(room.feedback.answer_cards) != 4:
                    raise AssertionError("Synthetic defense did not complete all coaching and settlement")
                if [turn.answer for turn in room.defense.turns] != [case.answer] * 4:
                    raise AssertionError("Synthetic defense did not retain the submitted answers")
                if coordinator.view(actors[0])["turns"] != coordinator.view(actors[1])["turns"]:
                    raise AssertionError("Synthetic defenders disagree about the shared transcript")
            finally:
                await coordinator.shutdown()
    finally:
        reset_timing_sink()
    return _annotate(sink.records, case, condition,
                     run_id or f"{condition}:{case.case_id}")


async def run_synthetic_suite(cases=DEFAULT_SYNTHETIC_CASES, *,
                              baseline_condition: str = "baseline",
                              candidate_condition: str = "candidate",
                              baseline_scale: float = 1.0,
                              candidate_scale: float = 1.0) -> tuple[list[dict], list[dict]]:
    baseline, candidate = [], []
    for case in cases:
        baseline.extend(await run_synthetic_defense(
            case, baseline_condition, latency_scale=baseline_scale))
        candidate.extend(await run_synthetic_defense(
            case, candidate_condition, latency_scale=candidate_scale))
    return baseline, candidate


def _percentile(values: list[int], fraction: float) -> int:
    ordered = sorted(values)
    index = max(0, math.ceil(len(ordered) * fraction) - 1)
    return ordered[min(index, len(ordered) - 1)]


def _usage(records: list[dict]) -> dict:
    usage = {}
    for field in USAGE_FIELDS:
        known = [record[field] for record in records
                 if type(record.get(field)) in (int, float)]
        usage[field] = {
            "sum": sum(known) if known else None,
            "known_records": len(known),
            "unknown_records": len(records) - len(known),
        }
    return usage


def summarize(records: list[dict]) -> dict:
    groups: dict[tuple, list[dict]] = {}
    for record in records:
        stage = record.get("stage") if record["event"] == "stage" else None
        groups.setdefault((record["event"], record["kind"], stage), []).append(record)
    summary = {}
    for (event, kind, stage), items in sorted(
            groups.items(), key=lambda item: (item[0][0], item[0][1], item[0][2] or "")):
        durations = [int(item["duration_ms"]) for item in items]
        key = f"{event}:{kind}" + (f":{stage}" if stage else "")
        summary[key] = {
            "event": event,
            "kind": kind,
            "stage": stage,
            "count": len(items),
            "outcomes": dict(sorted(Counter(item["outcome"] for item in items).items())),
            "failure_classes": dict(sorted(
                Counter(item["failure_class"] for item in items if item.get("failure_class")).items())),
            "duration_ms": {
                "median": statistics.median(durations),
                "p95": _percentile(durations, 0.95),
                "min": min(durations),
                "max": max(durations),
            },
            "usage": _usage(items),
        }
    return summary


def _compare_records(baseline: list[dict], candidate: list[dict]) -> dict:
    before, after = summarize(baseline), summarize(candidate)
    keys = sorted(set(before) | set(after))
    groups = {}
    for key in keys:
        left, right = before.get(key), after.get(key)
        groups[key] = {
            "baseline": left,
            "candidate": right,
            "median_delta_ms": (right["duration_ms"]["median"] - left["duration_ms"]["median"]
                                if left and right else None),
            "p95_delta_ms": (right["duration_ms"]["p95"] - left["duration_ms"]["p95"]
                             if left and right else None),
            "count_delta": (right["count"] - left["count"] if left and right else None),
        }
    return {"groups": groups,
            "only_in_baseline": sorted(set(before) - set(after)),
            "only_in_candidate": sorted(set(after) - set(before))}


def compare(baseline: list[dict], candidate: list[dict]) -> dict:
    baseline_cases = {record.get("case_id") for record in baseline if record.get("case_id")}
    candidate_cases = {record.get("case_id") for record in candidate if record.get("case_id")}
    if not baseline_cases and not candidate_cases:
        return _compare_records(baseline, candidate)
    if (sum(1 for record in baseline if record.get("case_id")) != len(baseline)
            or sum(1 for record in candidate if record.get("case_id")) != len(candidate)):
        raise ValueError("case-aware comparison requires case_id on every record")
    common = sorted(baseline_cases & candidate_cases)
    cases = {}
    for case_id in common:
        left_fingerprints = {record.get("case_fingerprint") for record in baseline
                             if record.get("case_id") == case_id}
        right_fingerprints = {record.get("case_fingerprint") for record in candidate
                              if record.get("case_id") == case_id}
        if left_fingerprints != right_fingerprints or len(left_fingerprints) != 1:
            raise ValueError("case-aware comparison requires identical synthetic inputs")
        cases[case_id] = _compare_records(
            [record for record in baseline if record.get("case_id") == case_id],
            [record for record in candidate if record.get("case_id") == case_id],
        )
    conditions = {
        "baseline": sorted({record.get("condition") for record in baseline
                            if record.get("condition")}),
        "candidate": sorted({record.get("condition") for record in candidate
                             if record.get("condition")}),
    }
    return {
        "cases": cases,
        "conditions": conditions,
        "only_in_baseline_cases": sorted(baseline_cases - candidate_cases),
        "only_in_candidate_cases": sorted(candidate_cases - baseline_cases),
    }


def replay(records: list[dict]) -> dict:
    return summarize(records)


def read_records(paths: list[str]) -> list[dict]:
    lines = []
    for path in paths:
        lines.extend(Path(path).read_text(encoding="utf-8").splitlines())
    return parse_records(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", action="append", default=[],
                        help="JSONL timing record file for the baseline run (repeatable)")
    parser.add_argument("--candidate", action="append", default=[],
                        help="JSONL timing record file for the candidate run (repeatable)")
    parser.add_argument("--json", action="store_true", help="print the full summary")
    parser.add_argument("--run-synthetic", action="store_true",
                        help="run comparable synthetic defenses instead of reading records")
    parser.add_argument("--case", action="append", default=[],
                        help="synthetic case id to run (repeatable; default all)")
    parser.add_argument("--baseline-condition", default="baseline")
    parser.add_argument("--candidate-condition", default="candidate")
    parser.add_argument("--candidate-scale", type=float, default=1.0)
    parser.add_argument("--output", help="write emitted synthetic JSONL records here")
    args = parser.parse_args(argv)
    if not args.run_synthetic and not args.baseline and not args.candidate:
        parser.error("provide synthetic cases or at least one --baseline/--candidate file")
    if args.run_synthetic:
        cases = [case for case in DEFAULT_SYNTHETIC_CASES
                 if not args.case or case.case_id in args.case]
        if not cases:
            parser.error("no matching synthetic cases")
        if args.case and len(cases) != len(set(args.case)):
            parser.error("unknown synthetic case id")
        baseline, candidate = asyncio.run(run_synthetic_suite(
            cases, baseline_condition=args.baseline_condition,
            candidate_condition=args.candidate_condition,
            candidate_scale=args.candidate_scale))
        if args.output:
            Path(args.output).write_text("\n".join(
                json.dumps(record, sort_keys=True) for record in baseline + candidate) + "\n",
                encoding="utf-8")
        result = compare(baseline, candidate)
    else:
        baseline = read_records(args.baseline)
        candidate = read_records(args.candidate)
        if args.baseline and args.candidate:
            result = compare(baseline, candidate)
        else:
            result = {"summary": summarize(candidate or baseline)}
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        groups = result["summary"] if "summary" in result else result.get("groups")
        if groups is not None:
            for key, item in groups.items():
                print(f"{key}: {json.dumps(item, sort_keys=True)}")
        else:
            print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
