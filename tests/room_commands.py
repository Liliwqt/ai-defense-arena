"""Offline helpers for existing room fixtures during the coordinator migration."""

from backend import game_server as server
from backend.rooms.coordinator import CatchUpDeadline
from backend.rooms.questions import QuestionWork, run_question


async def catch_up_deadline(room, expected_id=None):
    await server._coordinator(room).execute(CatchUpDeadline(expected_id, room.run_id))


async def generate_question(room, generation_id, first):
    # Existing isolated state-machine fixtures drive the real worker directly;
    # tracked scheduling is covered by execute/view and transport tests.
    await run_question(server._coordinator(room), QuestionWork(generation_id, first, room.run_id))
