"""Host decisions for validated, unpublished research opening candidates."""

from dataclasses import dataclass, field
import secrets
from typing import TYPE_CHECKING

from backend.account_store import AccessError, charge_run, release_run
from backend.defense_progression import prepare_progression, commit_progression
from backend.opening_history import OpeningQuestion, paper_key
from backend.question_generator import ResearchMove
from backend.resource_limits import limit
from backend.rooms.commands import CommandResult

if TYPE_CHECKING:
    from backend.rooms.coordinator import RoomCoordinator


@dataclass(frozen=True)
class OpeningCandidate:
    run_id: str
    generation_id: int
    plan_id: str
    paper: str
    move: ResearchMove
    id: str = field(default_factory=lambda: secrets.token_hex(24))

    def preview(self):
        question = self.move.question
        return {"id": self.id, "panelist": self.move.panelist, "question": question.question,
                "filename": question.filename, "evidence_text": question.evidence_text,
                "evidence_location": question.evidence_location or f"Line {question.evidence_line}"}

    def validate(self, room, candidate_id):
        if (candidate_id != self.id or room.phase != "retry" or room.run_id != self.run_id
                or room.generation_id != self.generation_id or not room.has_confirmed_research_profile
                or room.research_plan.id != self.plan_id or paper_key(room.files) != self.paper
                or room.defense is None or room.defense.turns
                or room.defense.plan.id != self.plan_id
                or room.defense.question_budget != room.research_budget_preview):
            raise AccessError("This opening choice has expired. Review the current room state.")
        question = self.move.question
        source = next((file for file in room.files if file.name == question.filename), None)
        lines = source.content.splitlines() if source else []
        if (source is None or type(question.evidence_line) is not int
                or not 1 <= question.evidence_line <= len(lines)
                or lines[question.evidence_line - 1] != question.evidence_text
                or source.kind != question.evidence_kind):
            raise AccessError("The candidate citation is no longer valid. Retry the opening question.")
        # Reapply against the current session, not a saved mutable session.
        return prepare_progression(room.defense).apply(self.move)


async def choose_opening(owner: "RoomCoordinator", actor, command):
    from backend.rooms.lifecycle import reserve_room_run
    room = owner._room
    clock = None
    generation = None
    async with room.lock:
        if room.closed:
            return CommandResult(False, "Room not found. Create a fresh room.")
        try:
            player = owner._player(actor)
            if not player.is_host:
                raise AccessError("Only the host can choose an opening question.")
            candidate = room.opening_candidate
            if candidate is None:
                raise AccessError("This opening choice has expired. Review the current room state.")
            session = candidate.validate(room, command.candidate_id)
            if not command.accept and not room.ai_budget.remaining('question:0', limit('AI_QUESTION_ATTEMPTS', 3, 10)):
                raise AccessError("No opening attempts remain. Accept this repeated question or start another run.")
            reserve_room_run(owner, actor.account_id, True, retry=True)
            if command.accept:
                turn = session.turns[0]
                try:
                    charge_run(actor.account_id, room.run_id, opening=OpeningQuestion(
                        candidate.paper, turn.question.question, turn.panelist, turn.topic_id), accept_repeat=True)
                except Exception:
                    try:
                        release_run(room.run_id)
                    except Exception:
                        return CommandResult(False, "Opening storage is unavailable. Your candidate is retained; retry when storage recovers.")
                    room.settled = True
                    return CommandResult(False, "The opening could not be saved. Nothing new was charged. Retry accepting when storage recovers.")
                owner._retire_work()
                room.defense = commit_progression(room.defense, session)
                room.present_question(room.defense, owner._workflows.now())
                clock = (room.clock_id, room.reaction_deadline_ms or room.vote_deadline_ms)
            else:
                owner._retire_work()
                room.phase = "generating"
                generation = room.generation_id
            room.error = None
            room.revision += 1
        except (AccessError, ValueError) as error:
            return CommandResult(False, str(error))
        except Exception:
            return CommandResult(False, "Opening storage is unavailable. Your candidate is retained; retry when storage recovers.")
    await owner._publish()
    if clock:
        owner._schedule_clock(*clock)
    if generation is not None:
        owner._schedule_question(generation, True)
    return CommandResult(True)
