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


async def interpret_pending(room, interpretation_id):
    from backend.rooms.submissions import InterpretationWork, capture_interpretation, run_interpretation
    owner = server._coordinator(room)
    async with room.lock:
        work = InterpretationWork(interpretation_id, room.run_id, room.pending_submission)
        if not owner._interpretation_current(work):
            return
        request = capture_interpretation(room, work.pending)
    await run_interpretation(owner, work, request)


async def prepare_research_plan(room, version):
    from backend.rooms.planning import PlanWork, PlanInput, run_plan
    owner = server._coordinator(room)
    async with room.lock:
        work = PlanWork(version, room.run_id)
        request = PlanInput(tuple(room.files), room.defense_type, room.research_stage)
    await run_plan(owner, work, request)


async def generate_coaching(room, version):
    from backend.rooms.coaching import CoachingWork, capture_coaching, run_coaching
    owner = server._coordinator(room)
    async with room.lock:
        work = CoachingWork(version, room.run_id)
        if not owner._coaching_current(work):
            return
        request = capture_coaching(room)
    await run_coaching(owner, work, request)


async def publish_room(room):
    from backend.rooms.commands import PublishRoom
    await server._coordinator(room).execute(PublishRoom())


async def observe_absence(room):
    from backend.rooms.commands import ObserveAbsence
    await server._coordinator(room).execute(ObserveAbsence())
