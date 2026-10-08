"""Synchronous timed-turn rules; room adapters own locks, tasks and publication."""

from dataclasses import dataclass, field
import secrets

from defense_session import DefenseSession, MAX_ANSWER_CHARS
from resource_limits import limit
from question_generator import ClarificationExchange, SubmissionDecision

VOTE_MS = 15_000
ANSWER_MS = 120_000


class DeadlineExpired(ValueError):
    """The room adapter must catch up the authoritative clock before replying."""


@dataclass(frozen=True)
class PendingSubmission:
    turn: int
    token: str
    name: str
    seat: int
    text: str
    remaining_ms: int


@dataclass(kw_only=True)
class TimedTurn:
    # Room inherits this state so existing snapshots and construction stay stable.
    phase: str = "lobby"
    error: str | None = None
    vote_deadline_ms: int | None = None
    answer_deadline_ms: int | None = None
    selected_seat: int | None = None
    votes: dict[str, int] = field(default_factory=dict)
    pending_submission: PendingSubmission | None = None
    interpretation_id: int = 0
    clock_id: int = 0
    answered_by: dict[int, str] = field(default_factory=dict)
    answered_by_seat: dict[int, int] = field(default_factory=dict)

    interpretation_attempts: int = 0
    pause_used_ms: int = 0
    pause_started_ms: int | None = None
    pause_deadline_ms: int | None = None

    def begin_vote(self, now: int) -> None:
        self.interpretation_attempts = 0
        self.pause_used_ms = 0
        self.pause_started_ms = None
        self.pause_deadline_ms = None
        self.phase = "voting"
        self.votes.clear()
        self.selected_seat = None
        self.answer_deadline_ms = None
        self.vote_deadline_ms = now + VOTE_MS
        self.clock_id += 1

    def cast_vote(self, token: str, seat: object, online: dict[str, int], now: int) -> None:
        if self.phase != "voting" or self.vote_deadline_ms is None:
            raise ValueError("Voting is not open.")
        if now >= self.vote_deadline_ms:
            raise DeadlineExpired("Voting time is over.")
        if isinstance(seat, bool) or not isinstance(seat, int) or seat not in online.values():
            raise ValueError("Choose an online defender.")
        self.votes[token] = seat

    def set_selected(self, seat: int | None, session: DefenseSession | None) -> None:
        self.selected_seat = seat
        if session is not None:
            session.assign_current_defender(seat)

    def reassign(self, online: dict[str, int], session: DefenseSession | None, choose=None) -> bool:
        if self.phase not in {"question", "interpreting", "interpretation_retry"} or self.selected_seat in online.values():
            return False
        seats = sorted(online.values())
        replacement = (choose or secrets.choice)(seats) if seats else None
        if replacement == self.selected_seat:
            return False
        self.set_selected(replacement, session)
        return True

    def expire(self, now: int, online: dict[str, int], session: DefenseSession,
               expected_id: int | None = None, choose=None) -> str | None:
        if expected_id is not None and self.clock_id != expected_id:
            return None
        if self.phase == "voting" and self.vote_deadline_ms is not None and now >= self.vote_deadline_ms:
            counts = {seat: 0 for seat in sorted(online.values())}
            for token, seat in self.votes.items():
                if token in online and seat in counts:
                    counts[seat] += 1
            highest = max(counts.values(), default=0)
            seats = [seat for seat, count in counts.items() if count == highest]
            self.set_selected((choose or secrets.choice)(seats) if seats else None, session)
            self.votes.clear()
            self.vote_deadline_ms = None
            self.phase = "question"
            self.answer_deadline_ms = now + ANSWER_MS
            self.clock_id += 1
            return "voting_closed"
        if self.phase in {'question', 'interpreting', 'interpretation_retry'} and self.answer_deadline_ms is not None and now >= self.answer_deadline_ms:
            self.discard_pending()
            session.time_out_current()
            self.resolve(session)
            return "timed_out"
        if self.phase in {'interpreting', 'interpretation_retry'} and self.pause_deadline_ms is not None and now >= self.pause_deadline_ms:
            self.pause_deadline_ms = None
            self.clock_id += 1
            self.reassign(online, session)
            return 'pause_ended'
        return None

    def clear_clock(self) -> None:
        self.clock_id += 1
        self.vote_deadline_ms = None
        self.answer_deadline_ms = None
        self.pause_started_ms = None
        self.pause_deadline_ms = None
        self.selected_seat = None
        self.votes.clear()

    def resolve(self, session: DefenseSession) -> None:
        self.clear_clock()
        self.phase = "complete" if session.completed else "generating"

    def validate_submit(self, seat: int, turn: object, answer: object,
                        session: DefenseSession | None, now: int, direct=False) -> None:
        phases = {'question', 'interpretation_retry', 'interpreting'} if direct else {'question'}
        if self.phase not in phases or session is None:
            raise ValueError("There is no question awaiting an answer.")
        if self.answer_deadline_ms is None or now >= self.answer_deadline_ms:
            raise DeadlineExpired("Answer time is over.")
        if self.selected_seat != seat:
            raise ValueError("Only the chosen defender can answer this question.")
        if isinstance(turn, bool) or not isinstance(turn, int) or turn != len(session.turns) - 1:
            raise ValueError("That question has already been answered.")
        if not isinstance(answer, str):
            raise ValueError("Write an answer before continuing.")
        if len(answer) > MAX_ANSWER_CHARS:
            raise ValueError(f"Keep your answer under {MAX_ANSWER_CHARS:,} characters.")
        if not answer.strip():
            raise ValueError("Write an answer or clarification request before continuing.")
        if not direct:
            if len(session.turns[-1].clarifications) >= 2:
                raise ValueError('Both clarifications are used. Choose Submit answer directly.')
            if self.interpretation_attempts >= limit('AI_INTERPRETATION_ATTEMPTS', 6, 20):
                raise ValueError('Interpretation allowance used. Choose Submit answer directly.')

    def submit_direct(self, token, name, seat, turn, answer, session, now):
        self.validate_submit(seat, turn, answer, session, now, direct=True)
        self.discard_pending()
        self.pending_submission = PendingSubmission(turn, token, name, seat, answer.strip(), 0)
        self.accept_pending(session)

    def submit(self, token: str, name: str, seat: int, turn: object, answer: object,
               session: DefenseSession | None, now: int) -> None:
        self.validate_submit(seat, turn, answer, session, now)
        self.interpretation_attempts += 1
        self.pause_started_ms = now
        pause_remaining = max(0, limit('AI_PAUSE_SECONDS', 240, 600) * 1000 - self.pause_used_ms)
        self.pause_deadline_ms = now + pause_remaining if pause_remaining else None
        remaining = max(0, self.answer_deadline_ms - now)
        self.pending_submission = PendingSubmission(turn, token, name, seat, answer.strip(),
                                                    max(0, self.answer_deadline_ms - now))
        self.clock_id += 1
        self.answer_deadline_ms = now + remaining + pause_remaining
        self.phase = "interpreting"
        self.error = None
        self.interpretation_id += 1

    def interpret(self, session: DefenseSession, decision: SubmissionDecision,
                  expected_id: int, pending: PendingSubmission, online: dict[str, int], now: int) -> str | None:
        if self.interpretation_id != expected_id or self.pending_submission is not pending:
            return None
        if decision.action == "clarify":
            try:
                session.record_clarification(ClarificationExchange(pending.text, decision.clarification))
                self.error = None
            except ValueError as error:
                self.error = str(error)
            elapsed = max(0, now - (self.pause_started_ms if self.pause_started_ms is not None else now))
            paused = min(elapsed, max(0, limit('AI_PAUSE_SECONDS', 240, 600)*1000 - self.pause_used_ms))
            self.pause_used_ms += paused
            self.pause_started_ms = None
            self.pause_deadline_ms = None
            self.pending_submission = None
            self.phase = "question"
            self.answer_deadline_ms = now + max(0, pending.remaining_ms - (elapsed - paused))
            self.clock_id += 1
            self.reassign(online, session)
            return "clarified"
        self.accept_pending(session)
        return "answered"

    def accept_pending(self, session: DefenseSession) -> None:
        pending = self.pending_submission
        assert pending is not None
        session.submit_answer(pending.text, speaker_name=pending.name)
        self.answered_by[pending.turn] = pending.name
        self.answered_by_seat[pending.turn] = pending.seat
        self.pending_submission = None
        self.error = None
        self.resolve(session)

    def discard_pending(self) -> None:
        self.interpretation_id += 1
        self.pending_submission = None
        self.pause_started_ms = None
        self.pause_deadline_ms = None

    def interpretation_failed(self, expected_id: int, pending: PendingSubmission, error: str) -> bool:
        if self.interpretation_id != expected_id or self.pending_submission is not pending:
            return False
        self.phase = "interpretation_retry"
        self.error = error
        return True

    def retry_interpretation(self, *, is_host: bool, seat: int) -> None:
        if self.phase != "interpretation_retry" or self.pending_submission is None:
            raise ValueError("There is no failed submission to retry.")
        if not (is_host or self.selected_seat == seat):
            raise ValueError("Only the host or chosen defender can retry.")
        if self.interpretation_attempts >= limit('AI_INTERPRETATION_ATTEMPTS', 6, 20):
            raise ValueError('Interpretation allowance used. Use the saved submission as an answer.')
        self.interpretation_attempts += 1
        self.phase = "interpreting"
        self.error = None
        self.interpretation_id += 1

    def accept_saved_answer(self, session: DefenseSession | None, token: str, seat: int) -> None:
        pending = self.pending_submission
        if self.phase != "interpretation_retry" or pending is None or session is None:
            raise ValueError("There is no failed submission to use as an answer.")
        if self.selected_seat != seat or token != pending.token:
            raise ValueError("Only the chosen defender can use their submission as an answer.")
        self.interpretation_id += 1
        self.accept_pending(session)
