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
    generate_research_move,
    ResearchMove,
    QuestionGenerationError,
)
from research_plan import ResearchPlan, validate_question_budget

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
    topic_id: str | None = None
    is_follow_up: bool = False
    ended_early: bool = False

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
        return not self.finished and bool(self.turns) and not self.turns[-1].resolved

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
                turn.topic_id, turn.is_follow_up,
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

    def assign_current_defender(self, seat: int | None) -> None:
        if self.awaiting_answer:
            self.turns[-1].assigned_seat = seat

    def record_clarification(self, exchange: ClarificationExchange) -> None:
        if not self.awaiting_answer:
            raise ValueError("There is no question awaiting an answer.")
        if len(self.turns[-1].clarifications) >= 2:
            raise ValueError("This question has used both clarifications. Please submit an answer.")
        self.turns[-1].clarifications.append(exchange)

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


@dataclass
class ResearchDefenseSession(DefenseSession):
    """Independent research policy; code-only ordering and caps stay unchanged."""

    plan: ResearchPlan | None = None
    question_budget: int = 4
    coverage: dict[str, dict] = field(default_factory=dict)
    completion_reason: str | None = None

    @classmethod
    def create(cls, plan: ResearchPlan, budget: int, defense_type: str, research_stage: str):
        if defense_type not in {"research", "mixed"} or not plan.topics:
            raise ValueError("A research defense requires a prepared research map.")
        return cls(defense_type=defense_type, research_stage=research_stage, plan=plan,
                   question_budget=validate_question_budget(budget),
                   coverage={topic.id: {"status": "pending", "turns": [], "reason": ""} for topic in plan.topics})

    @property
    def completed(self):
        return self.finished

    @property
    def needs_question(self):
        return not self.finished and (not self.turns or self.turns[-1].resolved)

    def _finish_if_last(self):
        # The final assessment shares the next-move call; it may not add a
        # question once the budget is exhausted.
        pass

    @property
    def pending_panelist(self):
        roles = self.allowed_next_panelists
        return roles[0] if len(roles) == 1 else None

    @property
    def allowed_next_panelists(self):
        return tuple(dict.fromkeys(option["panelist"] for option in self.question_options()))

    @property
    def may_complete(self):
        return len(self.turns) >= self.question_budget or all(
            role in {t.panelist for t in self.turns} for role in RESEARCH_PANELISTS)

    def question_options(self, coverage: dict | None = None):
        if not self.needs_question or len(self.turns) >= self.question_budget:
            return []
        coverage = coverage if coverage is not None else self.coverage
        assert self.plan is not None
        spoken = {turn.panelist for turn in self.turns}
        missing = [role for role in RESEARCH_PANELISTS if role not in spoken]
        untouched = [topic for topic in self.plan.topics if not any(t.topic_id == topic.id for t in self.turns)]
        unresolved = [topic for topic in self.plan.topics if coverage[topic.id]["status"] != "addressed"]
        # During opening rounds any topic can be examined through the next
        # reviewer's lens, even if the short paper has no topic assigned to it.
        topics = untouched or unresolved or (list(self.plan.topics) if missing else [])
        if missing:
            assigned = [topic for topic in self.plan.topics if topic.panelist == missing[0]]
            if assigned:
                topics = [topic for topic in untouched if topic in assigned] or [topic for topic in unresolved if topic in assigned] or assigned
        options = [{"panelist": missing[0] if missing else topic.panelist,
                    "topic_id": topic.id, "is_follow_up": False} for topic in topics]
        previous = self.turns[-1] if self.turns else None
        if (previous and not previous.is_follow_up
                and len(self.turns) + len(missing) < self.question_budget
                and coverage[previous.topic_id]["status"] != "addressed"):
            options.append({"panelist": previous.panelist, "topic_id": previous.topic_id, "is_follow_up": True})
        return options

    def context(self):
        assert self.plan is not None
        possible_coverage = {key: dict(value) for key, value in self.coverage.items()}
        if self.turns and self.turns[-1].resolved:
            # The latest assessment can reopen an earlier addressed topic.
            # Give the model candidate options; apply_move filters them against
            # the actual proposed assessment before accepting anything.
            possible_coverage[self.turns[-1].topic_id]["status"] = "needs clarification"
        return {"plan": self.plan.snapshot(), "coverage": self.coverage,
                "question_budget": self.question_budget, "generated_questions": len(self.turns),
                "question_options": self.question_options(possible_coverage), "completion_reason": self.completion_reason,
                "reviewers_spoken": list(dict.fromkeys(turn.panelist for turn in self.turns)),
                "opening_note": "Openers use their assigned topics when available; if the map has none for a reviewer, examine an existing topic through that reviewer's specialty.",
                "budget_exhausted": len(self.turns) >= self.question_budget,
                "previous_turn": len(self.turns) - 1 if self.turns else None,
                "previous_topic": self.turns[-1].topic_id if self.turns else None,
                "coverage_note": "Addressed describes discussion coverage, not proof that the research is correct."}

    def apply_move(self, move: ResearchMove):
        if not self.needs_question:
            raise ValueError("There is no pending research move.")
        if not isinstance(move, ResearchMove):
            raise QuestionGenerationError("The AI returned an invalid research move. Please retry.")
        coverage = {key: {**value, "turns": list(value["turns"])} for key, value in self.coverage.items()}
        assessment = move.assessment
        if self.turns:
            previous = self.turns[-1]
            if (assessment is None or type(assessment.turn) is not int
                    or assessment.turn != len(self.turns) - 1 or assessment.topic_id != previous.topic_id
                    or assessment.status not in {"discussed", "needs clarification", "addressed"}
                    or not assessment.reason.strip() or len(assessment.reason) > 600
                    or (previous.timed_out and assessment.status != "needs clarification")):
                raise QuestionGenerationError("The AI returned an invalid coverage assessment. Please retry.")
            item = coverage[assessment.topic_id]
            item["status"], item["reason"] = assessment.status, assessment.reason.strip()
            if assessment.turn not in item["turns"]:
                item["turns"].append(assessment.turn)
        elif assessment is not None:
            raise QuestionGenerationError("The opening move cannot assess an answer. Please retry.")
        all_spoken = set(RESEARCH_PANELISTS).issubset({t.panelist for t in self.turns})
        covered = all(value["status"] == "addressed" for value in coverage.values())
        exhausted = len(self.turns) >= self.question_budget
        should_finish = exhausted or (covered and all_spoken)
        if move.panelist is None and move.question is None:
            if not should_finish or move.topic_id is not None or move.is_follow_up:
                raise QuestionGenerationError("The AI ended the research defense too early. Please retry.")
        else:
            option = {"panelist": move.panelist, "topic_id": move.topic_id, "is_follow_up": move.is_follow_up}
            if should_finish or move.question is None or option not in self.question_options(coverage):
                raise QuestionGenerationError("The AI chose an invalid research topic or reviewer. Please retry.")
            if any(t.question.question.strip().casefold() == move.question.question.strip().casefold() for t in self.turns):
                raise QuestionGenerationError("The AI repeated an earlier question. Please retry.")
        # Every validation above succeeds before any coverage or turn changes.
        self.coverage = coverage
        if should_finish:
            self.finished = True
            self.completion_reason = "budget exhausted" if exhausted else "coverage addressed"
        else:
            self.turns.append(DefenseTurn(move.panelist, move.question,
                                          topic_id=move.topic_id, is_follow_up=move.is_follow_up))
            if self.coverage[move.topic_id]["status"] == "pending":
                self.coverage[move.topic_id]["status"] = "discussed"

    def end(self):
        if self.finished:
            raise ValueError("The defense is already complete.")
        if self.awaiting_answer:
            self.turns[-1].ended_early = True
        self.finished = True
        self.completion_reason = "ended by host"
        # A resolved but unassessed answer remains discussed, never silently
        # addressed. Its factual supporting turn survives manual ending.
        if self.turns and self.turns[-1].resolved:
            turn = self.turns[-1]
            item = self.coverage[turn.topic_id]
            if len(self.turns) - 1 not in item["turns"]:
                item["turns"].append(len(self.turns) - 1)
            if turn.timed_out:
                item["status"] = "needs clarification"


def advance_defense(
    session: DefenseSession,
    project_files: list[ProjectFile],
    api_key: str | None,
    model: str = DEFAULT_MODEL,
    client=None,
) -> PanelMove:
    """Generate one allowed move; leave the saved answer untouched on failure."""
    # Local import avoids a cycle between the policy types and orchestration.
    from defense_progression import prepare_progression, commit_progression
    request = prepare_progression(session)
    move = request.generate(project_files, api_key, model, client,
                            next_move=generate_next_move, research_move=generate_research_move)
    commit_progression(session, request.apply(move))
    return move


def sync_project_session(state: MutableMapping, fingerprint: str | None) -> None:
    """Discard a defense when the accepted uploaded project changes."""
    if state.get("defense_project_fingerprint") != fingerprint:
        state.pop("defense_session", None)
        for key in ("research_plan", "research_plan_error", "research_budget_preview", "research_plan_approved", "research_confirmed_budget", "research_coaching"):
            state.pop(key, None)
        state["defense_project_fingerprint"] = fingerprint
