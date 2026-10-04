"""State transitions for a four-panel adaptive practice defense."""

from dataclasses import dataclass, field
from typing import MutableMapping

from project_files import ProjectFile
from question_generator import (
    AnsweredQuestion,
    ClarificationExchange,
    CRITICAL_JUDGE,
    DEFAULT_MODEL,
    GroundedQuestion,
    PanelMove,
    PRODUCT_JUDGE,
    RESEARCH_PANELISTS,
    SECURITY_REVIEWER,
    TECHNICAL_ARCHITECT,
    generate_next_move,
)

PANELIST_ORDER = (TECHNICAL_ARCHITECT, SECURITY_REVIEWER, PRODUCT_JUDGE, CRITICAL_JUDGE)
MAX_ANSWER_CHARS = 4_000


@dataclass
class DefenseTurn:
    panelist: str
    question: GroundedQuestion
    answer: str | None = None
    timed_out: bool = False
    assigned_seat: int | None = None
    clarifications: list[ClarificationExchange] = field(default_factory=list)
    speaker_name: str | None = None

    @property
    def resolved(self) -> bool:
        return self.answer is not None or self.timed_out


@dataclass
class DefenseSession:
    turns: list[DefenseTurn] = field(default_factory=list)
    finished: bool = False
    defense_type: str = "code"
    research_stage: str = "infer"

    @classmethod
    def start(cls, first_question: GroundedQuestion, defense_type: str = "code", research_stage: str = "infer") -> "DefenseSession":
        order = RESEARCH_PANELISTS if defense_type != "code" else PANELIST_ORDER
        return cls([DefenseTurn(order[0], first_question)], defense_type=defense_type, research_stage=research_stage)

    @property
    def panelist_order(self) -> tuple[str, ...]:
        return RESEARCH_PANELISTS if self.defense_type != "code" else PANELIST_ORDER

    @property
    def completed(self) -> bool:
        return self.finished and bool(self.turns) and self.turns[-1].resolved

    @property
    def needs_question(self) -> bool:
        return bool(self.turns) and self.turns[-1].resolved and not self.finished

    @property
    def awaiting_answer(self) -> bool:
        return bool(self.turns) and not self.turns[-1].resolved

    @property
    def allowed_next_panelists(self) -> tuple[str, ...]:
        if not self.needs_question:
            return ()
        current = self.turns[-1].panelist
        index = self.panelist_order.index(current)
        count = sum(turn.panelist == current for turn in self.turns)
        allowed = (current,) if count == 1 else ()
        if index + 1 < len(self.panelist_order):
            allowed += (self.panelist_order[index + 1],)
        return allowed

    @property
    def pending_panelist(self) -> str | None:
        allowed = self.allowed_next_panelists
        return allowed[0] if len(allowed) == 1 else None

    @property
    def may_complete(self) -> bool:
        return self.needs_question and self.turns[-1].panelist == self.panelist_order[-1]

    def answered_history(self) -> list[AnsweredQuestion]:
        return [
            AnsweredQuestion(
                turn.panelist, turn.question.question, turn.answer, turn.timed_out,
                turn.question.lead_in, tuple(turn.clarifications),
                turn.speaker_name, turn.question,
            )
            for turn in self.turns
            if turn.resolved
        ]

    def submit_answer(self, answer: str, *, speaker_name: str | None = None) -> None:
        if not self.awaiting_answer:
            raise ValueError("There is no question awaiting an answer.")
        answer = answer.strip()
        if not answer:
            raise ValueError("Write an answer before continuing.")
        if len(answer) > MAX_ANSWER_CHARS:
            raise ValueError(f"Keep your answer under {MAX_ANSWER_CHARS:,} characters.")
        self.turns[-1].answer = answer
        self.turns[-1].speaker_name = speaker_name
        self._finish_if_last()

    def time_out_current(self) -> None:
        if not self.awaiting_answer:
            raise ValueError("There is no question awaiting an answer.")
        self.turns[-1].timed_out = True
        self._finish_if_last()

    def _finish_if_last(self) -> None:
        last = self.panelist_order[-1]
        if self.turns[-1].panelist == last and sum(t.panelist == last for t in self.turns) == 2:
            self.finished = True

    def apply_move(self, move: PanelMove) -> None:
        if not self.needs_question:
            raise ValueError("There is no pending panel move.")
        if move.panelist is None and move.question is None:
            if not self.may_complete:
                raise ValueError("All four panelists must speak before completion.")
            self.finished = True
            return
        if move.panelist not in self.allowed_next_panelists or move.question is None:
            raise ValueError("The next panelist is not allowed.")
        self.turns.append(DefenseTurn(move.panelist, move.question))


def advance_defense(
    session: DefenseSession,
    project_files: list[ProjectFile],
    api_key: str | None,
    model: str = DEFAULT_MODEL,
    client=None,
) -> PanelMove:
    """Generate one allowed move; leave the saved answer untouched on failure."""
    if not session.needs_question:
        raise ValueError("There is no pending panel move.")
    move = generate_next_move(
        project_files,
        api_key,
        history=session.answered_history(),
        allowed_panelists=session.allowed_next_panelists,
        may_complete=session.may_complete,
        model=model,
        client=client,
        defense_type=session.defense_type, research_stage=session.research_stage,
    )
    session.apply_move(move)
    return move


def sync_project_session(state: MutableMapping, fingerprint: str | None) -> None:
    """Discard a defense when the accepted uploaded project changes."""
    if state.get("defense_project_fingerprint") != fingerprint:
        state.pop("defense_session", None)
        state["defense_project_fingerprint"] = fingerprint
