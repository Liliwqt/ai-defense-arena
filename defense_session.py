"""State transitions for a four-answer practice defense."""

from dataclasses import dataclass, field
from typing import MutableMapping

from project_files import ProjectFile
from question_generator import (
    AnsweredQuestion,
    DEFAULT_MODEL,
    GroundedQuestion,
    SECURITY_REVIEWER,
    TECHNICAL_ARCHITECT,
    generate_panel_question,
)


PANELIST_ORDER = (
    TECHNICAL_ARCHITECT,
    SECURITY_REVIEWER,
    TECHNICAL_ARCHITECT,
    SECURITY_REVIEWER,
)
MAX_ANSWER_CHARS = 4_000


@dataclass
class DefenseTurn:
    panelist: str
    question: GroundedQuestion
    answer: str | None = None


@dataclass
class DefenseSession:
    turns: list[DefenseTurn] = field(default_factory=list)

    @classmethod
    def start(cls, first_question: GroundedQuestion) -> "DefenseSession":
        return cls([DefenseTurn(PANELIST_ORDER[0], first_question)])

    @property
    def completed(self) -> bool:
        return len(self.turns) == len(PANELIST_ORDER) and self.turns[-1].answer is not None

    @property
    def needs_question(self) -> bool:
        return (
            bool(self.turns)
            and len(self.turns) < len(PANELIST_ORDER)
            and self.turns[-1].answer is not None
        )

    @property
    def awaiting_answer(self) -> bool:
        return bool(self.turns) and self.turns[-1].answer is None

    @property
    def pending_panelist(self) -> str | None:
        if self.needs_question:
            return PANELIST_ORDER[len(self.turns)]
        return None

    def answered_history(self) -> list[AnsweredQuestion]:
        return [
            AnsweredQuestion(turn.panelist, turn.question.question, turn.answer)
            for turn in self.turns
            if turn.answer is not None
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

    def add_question(self, question: GroundedQuestion) -> None:
        panelist = self.pending_panelist
        if panelist is None:
            raise ValueError("There is no pending panel question.")
        self.turns.append(DefenseTurn(panelist, question))


def advance_defense(
    session: DefenseSession,
    project_files: list[ProjectFile],
    api_key: str | None,
    model: str = DEFAULT_MODEL,
    client=None,
) -> GroundedQuestion:
    """Generate exactly the pending turn; leave state untouched if the API fails."""
    panelist = session.pending_panelist
    if panelist is None:
        raise ValueError("There is no pending panel question.")
    question = generate_panel_question(
        project_files,
        api_key,
        panelist=panelist,
        history=session.answered_history(),
        follow_up=len(session.turns) >= 2,
        model=model,
        client=client,
    )
    session.add_question(question)
    return question


def sync_project_session(state: MutableMapping, fingerprint: str | None) -> None:
    """Discard a defense when the accepted uploaded project changes."""
    if state.get("defense_project_fingerprint") != fingerprint:
        state.pop("defense_session", None)
        state["defense_project_fingerprint"] = fingerprint
