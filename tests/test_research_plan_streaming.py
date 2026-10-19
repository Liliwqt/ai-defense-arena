"""Real streaming/progress boundaries with AI responses mocked."""

import asyncio
import json
from threading import Event
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from backend.project_files import ProjectFile
from backend.question_generator import QuestionGenerationError
from backend.research_plan import generate_research_plan, ResearchPlanProgress
from backend.research_plan_stream import CompletedTopicDecoder
from backend.rooms.commands import GenerateResearchPlan
from backend.rooms.coordinator import RoomCoordinator, RoomWorkflows
from backend import game_server
from tests.test_research_plan import PAPER, draft, fixture_plan
from tests import test_research_plan as fixtures
from tempfile import TemporaryDirectory


class StreamingClient:
    def __init__(self, output=None, chunks=None, final=None):
        self.output = output if output is not None else draft()
        text = json.dumps(self.output)
        self.chunks = chunks if chunks is not None else [text[i:i+17] for i in range(0, len(text), 17)]
        self.final = final if final is not None else self.output
        self.responses = self
        self.calls = []
        self.closed = False

    def stream(self, **kwargs):
        self.calls.append(kwargs)
        return self

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.closed = True

    def __iter__(self):
        yield SimpleNamespace(type="response.reasoning_summary_text.delta", delta="PRIVATE REASONING")
        for chunk in self.chunks:
            yield SimpleNamespace(type="response.output_text.delta", delta=chunk, output_index=1, content_index=0)

    def get_final_response(self):
        return SimpleNamespace(output_parsed=self.final)


class StreamedMapTests(unittest.TestCase):
    def generate(self, client, events):
        return generate_research_plan([ProjectFile("study.md", PAPER, "research_text")],
            "offline-key", client=client, on_progress=events.append)

    def test_one_request_emits_complete_grounded_topics_then_validates(self):
        events = []
        client = StreamingClient()
        plan = self.generate(client, events)
        self.assertEqual(len(client.calls), 1)
        self.assertEqual(client.calls[0]["model"], "server-assigned")
        self.assertEqual([len(event.topics) for event in events], [0, 1, 2, 3, 4, 4])
        self.assertEqual(events[-1].stage, "validating")
        self.assertEqual(events[-1].topics, plan.topics)
        self.assertEqual(events[1].topics[0].references[0].evidence_text, PAPER.splitlines()[3])
        self.assertNotIn("PRIVATE REASONING", str(events))
        self.assertTrue(client.closed)

    def test_partial_json_and_escaped_braces_never_become_partial_topics(self):
        output = draft()
        output["topics"][0]["title"] = 'Purpose [a] {b} "quoted" Cebuano: pangutana'
        text = json.dumps(output, ensure_ascii=False)
        decoder = CompletedTopicDecoder()
        topics = []
        for char in text:
            topics.extend(decoder.feed(char))
        self.assertEqual(topics, output["topics"])
        self.assertEqual(decoder.feed(" "), [])
        with self.assertRaises(QuestionGenerationError):
            CompletedTopicDecoder().feed("x" * 1_000_001)

    def test_invalid_reference_stops_stream_without_publishing_that_topic(self):
        output = draft()
        output["topics"][1]["references"][0]["evidence_line"] = 999
        client, events = StreamingClient(output), []
        with self.assertRaises(QuestionGenerationError):
            self.generate(client, events)
        self.assertEqual([len(event.topics) for event in events], [0, 1])
        self.assertTrue(client.closed)

    def test_final_disagreement_or_invalid_uncertainty_cannot_approve_drafts(self):
        changed = draft()
        changed["topics"][0]["title"] = "Changed title"
        with self.assertRaisesRegex(QuestionGenerationError, "streamed research map changed"):
            self.generate(StreamingClient(final=changed), [])
        invalid = draft()
        invalid["uncertainties"] = ["x" * 301]
        with self.assertRaises(QuestionGenerationError):
            self.generate(StreamingClient(invalid), [])


class MappingPublicationTests(unittest.IsolatedAsyncioTestCase):
    async def test_reconnect_reads_progress_and_retired_work_cannot_publish_more(self):
        host = game_server.Player("host", "Host", 0, True)
        room = game_server.Room("STREAM", [ProjectFile("study.md", PAPER, "research_text")],
            {host.token: host}, "research", research_planning_status="planning", research_plan_generation_id=1)
        ready = asyncio.Event()
        captured = []
        plan = fixture_plan()

        async def request(value):
            captured.append(value.on_progress)
            await value.on_progress(ResearchPlanProgress("mapping", plan.topics[:1]))
            ready.set()
            await asyncio.Event().wait()

        owner = RoomCoordinator(room, RoomWorkflows(plan_request=request))
        self.addAsyncCleanup(owner.shutdown)
        await owner.execute(GenerateResearchPlan(1))
        await asyncio.wait_for(ready.wait(), 1)
        snapshot = room.snapshot(host)
        self.assertEqual(snapshot["research_plan_progress"]["topics"][0]["title"], plan.topics[0].title)
        self.assertIsNone(snapshot["research_plan"])
        self.assertFalse(snapshot["research_plan_approved"])
        async with room.lock:
            owner._retire_work()
            room.research_plan_progress = None
            room.research_planning_status = "none"
        self.assertFalse(await captured[0](ResearchPlanProgress("validating", plan.topics)))
        self.assertIsNone(room.research_plan_progress)


class MappingTransportTests(unittest.TestCase):
    create = fixtures.ResearchPlanRoomTests.create
    hello = fixtures.ResearchPlanRoomTests.hello
    until = fixtures.ResearchPlanRoomTests.until

    def setUp(self):
        directory = TemporaryDirectory(prefix="mapping-stream-tests-")
        self.addCleanup(directory.cleanup)
        env = patch.dict("os.environ", {"ROOM_DOCUMENT_DIR": directory.name})
        env.start()
        self.addCleanup(env.stop)
        fixtures.ResearchPlanRoomTests.setUp(self)

    def test_two_clients_see_drafts_before_completion_and_reconnect_keeps_them(self):
        host = self.create()
        guest = self.client.post(f"/api/rooms/{host['room_code']}/join", json={"name": "Guest"}).json()
        release = Event()
        self.addCleanup(release.set)
        output = draft()
        first = '{"topics":[' + json.dumps(output["topics"][0])
        rest = ',' + ','.join(json.dumps(topic) for topic in output["topics"][1:]) + '],"uncertainties":' + json.dumps(output["uncertainties"]) + '}'

        class PausedStream(StreamingClient):
            def __iter__(self):
                yield SimpleNamespace(type="response.output_text.delta", delta=first, output_index=0, content_index=0)
                if not release.wait(10):
                    raise RuntimeError("Fixture release missing")
                yield SimpleNamespace(type="response.output_text.delta", delta=rest, output_index=0, content_index=0)

        client = PausedStream()
        real_generate = generate_research_plan
        def generate(*args, **kwargs):
            kwargs['client'] = client
            return real_generate(*args, **kwargs)

        with patch('backend.rooms.planning.generate_research_plan', side_effect=generate), \
             self.client.websocket_connect(f"/ws/{host['room_code']}") as h, \
             self.client.websocket_connect(f"/ws/{host['room_code']}") as g:
            self.hello(h, host["player_token"])
            self.hello(g, guest["player_token"])
            h.send_json({"type": "prepare_research_plan"})
            for socket in (h, g):
                for _ in range(15):
                    state = socket.receive_json()["state"]
                    progress = state["research_plan_progress"]
                    if progress and progress["topics"]:
                        break
                self.assertEqual(len(progress["topics"]), 1)
                self.assertIsNone(state["research_plan"])
                self.assertEqual(state["turns"], [])
            with self.client.websocket_connect(f"/ws/{host['room_code']}") as reconnect:
                state = self.hello(reconnect, guest["player_token"])
                self.assertEqual(len(state["research_plan_progress"]["topics"]), 1)
            h.send_json({"type": "start"})
            for _ in range(10):
                event = h.receive_json()
                if event["type"] == "error":
                    break
            self.assertIn("Wait for", event["message"])
            release.set()
            for socket in (h, g):
                state = self.until(socket, research_planning_status="ready")
                self.assertIsNone(state["research_plan_progress"])
                self.assertEqual(len(state["research_plan"]["topics"]), 4)
            self.assertEqual(len(client.calls), 1)

    def test_failed_partial_map_clears_drafts_and_retry_starts_fresh(self):
        host = self.create()
        real_generate = generate_research_plan
        output = draft()
        output["topics"][1]["references"][0]["evidence_line"] = 999
        clients = iter([StreamingClient(output), StreamingClient()])
        def generate(*args, **kwargs):
            kwargs['client'] = next(clients)
            return real_generate(*args, **kwargs)
        with patch('backend.rooms.planning.generate_research_plan', side_effect=generate), \
             self.client.websocket_connect(f"/ws/{host['room_code']}") as h:
            self.hello(h, host["player_token"])
            h.send_json({"type": "prepare_research_plan"})
            state = self.until(h, research_planning_status="failed")
            self.assertIsNone(state["research_plan_progress"])
            self.assertIsNone(state["research_plan"])
            self.assertEqual(state["files"], ["study.md"])
            h.send_json({"type": "retry_research_plan"})
            state = self.until(h, research_planning_status="ready")
            self.assertEqual(len(state["research_plan"]["topics"]), 4)
