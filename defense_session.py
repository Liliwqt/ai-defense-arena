"""State transitions for a four-panel adaptive practice defense."""

from dataclasses import dataclass, field
from typing import MutableMapping

from project_files import ProjectFile
from question_generator import (
    AnsweredQuestion,
    CRITICAL_JUDGE,
    DEFAULT_MODEL,
    GroundedQuestion,
    PanelMove,
    PRODUCT_JUDGE,
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

    @property
    def resolved(self) -> bool:
        return self.answer is not None or self.timed_out


@dataclass
class DefenseSession:
    turns: list[DefenseTurn] = field(default_factory=list)
    finished: bool = False

    @classmethod
    def start(cls, first_question: GroundedQuestion) -> "DefenseSession":
        return cls([DefenseTurn(PANELIST_ORDER[0], first_question)])

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
        index = PANELIST_ORDER.index(current)
        count = sum(turn.panelist == current for turn in self.turns)
        allowed = (current,) if count == 1 else ()
        if index + 1 < len(PANELIST_ORDER):
            allowed += (PANELIST_ORDER[index + 1],)
        return allowed

    @property
    def pending_panelist(self) -> str | None:
        allowed = self.allowed_next_panelists
        return allowed[0] if len(allowed) == 1 else None

    @property
    def may_complete(self) -> bool:
        return self.needs_question and self.turns[-1].panelist == PANELIST_ORDER[-1]

    def answered_history(self) -> list[AnsweredQuestion]:
        return [
            AnsweredQuestion(turn.panelist, turn.question.question, turn.answer, turn.timed_out)
            for turn in self.turns
            if turn.resolved
        ]

    def submit_answer(self, answer: str) -> None:
        if not self.awaiting_answer:
            raise ValueError("There is no question awaiting an answer.")
        answer = answer.strip()
        if not answer:
            raise ValueError("Write an answer before continuing.")
        if len(answer) > MAX_ANSWER_CHARS:
            raise ValueError(f"Keep your answer under {MAX_ANSWER_CHARS:,} characters.")
        self.turns[-1].answer = answer
        self._finish_if_last()

    def time_out_current(self) -> None:
        if not self.awaiting_answer:
            raise ValueError("There is no question awaiting an answer.")
        self.turns[-1].timed_out = True
        self._finish_if_last()

    def _finish_if_last(self) -> None:
        last = PANELIST_ORDER[-1]
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
    )
    session.apply_move(move)
    return move


def sync_project_session(state: MutableMapping, fingerprint: str | None) -> None:
    """Discard a defense when the accepted uploaded project changes."""
    if state.get("defense_project_fingerprint") != fingerprint:
        state.pop("defense_session", None)
        state["defense_project_fingerprint"] = fingerprint
