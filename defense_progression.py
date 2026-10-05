"""Shared preparation, dispatch and validation for both defense adapters.

Prepared requests own a detached session. Async callers may discard their result
without changing the room; the synchronous fallback applies a move to its saved
session only after generation succeeds.
"""

import copy
from dataclasses import dataclass, fields

from defense_session import DefenseSession, ResearchDefenseSession
from question_generator import DEFAULT_MODEL, generate_first_question, generate_next_move, generate_research_move


def apply_progression(session, result, *, defense_type="code", research_stage="infer") -> DefenseSession:
    if session is None:
        return DefenseSession.start(result, defense_type, research_stage)
    session.apply_move(result)
    return session


def commit_progression(current: DefenseSession | None, validated: DefenseSession) -> DefenseSession:
    """Publish a validated candidate while retaining an existing session's identity."""
    if current is None:
        return validated
    if type(current) is not type(validated):
        raise ValueError("The defense policy changed during generation.")
    for item in fields(current):
        setattr(current, item.name, getattr(validated, item.name))
    return current


@dataclass(frozen=True)
class PreparedProgression:
    session: DefenseSession | None
    defense_type: str
    research_stage: str

    def generate(self, files, api_key, model=DEFAULT_MODEL, client=None, *,
                 first_question=generate_first_question, next_move=generate_next_move,
                 research_move=generate_research_move):
        common = {"model": model, "defense_type": self.defense_type, "research_stage": self.research_stage}
        if client is not None:
            common["client"] = client
        if self.session is None:
            return first_question(files, api_key, **common)
        history = self.session.answered_history()
        if isinstance(self.session, ResearchDefenseSession):
            return research_move(files, api_key, history=history, context=self.session.context(), **common)
        return next_move(files, api_key, history=history,
                         allowed_panelists=self.session.allowed_next_panelists,
                         may_complete=self.session.may_complete, **common)

    def apply(self, result) -> DefenseSession:
        return apply_progression(self.session, result, defense_type=self.defense_type, research_stage=self.research_stage)


def prepare_progression(session: DefenseSession | None, *, defense_type="code", research_stage="infer") -> PreparedProgression:
    if session is not None:
        if not session.needs_question:
            raise ValueError("There is no pending panel move.")
        defense_type, research_stage = session.defense_type, session.research_stage
    return PreparedProgression(copy.deepcopy(session), defense_type, research_stage)
