"""Synchronous timed-turn rules; room adapters own locks, tasks and publication."""

from dataclasses import dataclass, field
import secrets

from defense_session import DefenseSession, MAX_ANSWER_CHARS
from resource_limits import limit
from question_generator import ClarificationExchange, SubmissionDecision

VOTE_MS = 15_000
ANSWER_MS = 120_000
PROBE_MS = 30_000


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
    probe_id: str | None = None


@dataclass(kw_only=True)
class TimedTurn:
    # Room inherits this state so existing snapshots and construction stay stable.
    phase: str = "lobby"
    error: str | None = None
    vote_deadline_ms: int | None = None
    answer_deadline_ms: int | None = None
    probe_deadline_ms: int | None = None
    probe_recovery_available: bool = False
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
        self.probe_recovery_available = False
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
        if self.phase not in {"question", "probe", "interpreting", "interpretation_retry"} or self.selected_seat in online.values():
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
        if self.phase in {'question', 'probe', 'interpreting', 'interpretation_retry'} and self.answer_deadline_ms is not None and now >= self.answer_deadline_ms:
            self.discard_pending()
            is_probe = session.turns[-1].probe is not None and session.turns[-1].probe.status == "pending"
            if is_probe:
                session.resolve_probe(status="expired")
            else:
                session.time_out_current()
            self.resolve(session)
            return "probe_expired" if is_probe else "timed_out"
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
        self.probe_deadline_ms = None
        self.pause_started_ms = None
        self.pause_deadline_ms = None
        self.selected_seat = None
        self.votes.clear()

    def resolve(self, session: DefenseSession) -> None:
        self.clear_clock()
        self.phase = "complete" if session.completed else "generating"

    def validate_submit(self, seat: int, turn: object, answer: object,
                        session: DefenseSession | None, now: int, direct=False, probe_id=None) -> None:
        phases = ({'probe', 'interpretation_retry', 'interpreting'} if direct else {'probe'}) if probe_id is not None else ({'question', 'interpretation_retry', 'interpreting'} if direct else {'question'})
        if self.phase not in phases or session is None:
            raise ValueError("There is no question awaiting an answer.")
        if self.answer_deadline_ms is None or now >= self.answer_deadline_ms:
            raise DeadlineExpired("Answer time is over.")
        if self.selected_seat != seat:
            raise ValueError("Only the chosen defender can answer this question.")
        if isinstance(turn, bool) or not isinstance(turn, int) or turn != len(session.turns) - 1:
            raise ValueError("That question has already been answered.")
        probe = session.turns[-1].probe
        if probe_id is not None:
            if not probe or probe.status != "pending" or probe.id != probe_id:
                raise ValueError("That panelist probe is no longer awaiting a reply.")
        elif probe is not None:
            raise ValueError("Reply to the panelist probe using its current identifier.")
        if not isinstance(answer, str):
            raise ValueError("Write an answer before continuing.")
        if len(answer) > MAX_ANSWER_CHARS:
            raise ValueError(f"Keep your answer under {MAX_ANSWER_CHARS:,} characters.")
        if not answer.strip():
            raise ValueError("Write an answer or clarification request before continuing.")
        if not direct:
            if len(session.turns[-1].clarifications) + (len(probe.clarifications) if probe else 0) >= 2:
                raise ValueError('Both clarifications are used. Choose Submit answer directly.')
            if self.interpretation_attempts >= limit('AI_INTERPRETATION_ATTEMPTS', 6, 20):
                raise ValueError('Interpretation allowance used. Choose Submit answer directly.')

    def submit_direct(self, token, name, seat, turn, answer, session, now):
        self.validate_submit(seat, turn, answer, session, now, direct=True)
        self.discard_pending()
        self.pending_submission = PendingSubmission(turn, token, name, seat, answer.strip(), 0)
        self.accept_pending(session)

    def submit(self, token: str, name: str, seat: int, turn: object, answer: object,
               session: DefenseSession | None, now: int, *, probe_id=None) -> None:
        self.validate_submit(seat, turn, answer, session, now, probe_id=probe_id)
        self.interpretation_attempts += 1
        self.pause_started_ms = now
        pause_remaining = max(0, limit('AI_PAUSE_SECONDS', 240, 600) * 1000 - self.pause_used_ms)
        self.pause_deadline_ms = now + pause_remaining if pause_remaining else None
        remaining = max(0, self.answer_deadline_ms - now)
        self.pending_submission = PendingSubmission(turn, token, name, seat, answer.strip(),
                                                    max(0, self.answer_deadline_ms - now), probe_id)
        self.clock_id += 1
        self.answer_deadline_ms = now + remaining + pause_remaining
        self.phase = "interpreting"
        self.error = None
        self.interpretation_id += 1

    def submit_probe_reply(self, token, name, seat, turn, probe_id, reply, session, now, *, direct=False):
        if not isinstance(probe_id, str) or not probe_id:
            raise ValueError("A current panelist probe identifier is required.")
        self.validate_submit(seat, turn, reply, session, now, direct=direct, probe_id=probe_id)
        if direct:
            self.discard_pending()
            self.pending_submission = PendingSubmission(turn, token, name, seat, reply.strip(), 0, probe_id)
            self.accept_pending(session)
        else:
            self.submit(token, name, seat, turn, reply, session, now, probe_id=probe_id)

    def finish_probe(self, seat, turn, probe_id, session, now):
        if not isinstance(probe_id, str) or not probe_id:
            raise ValueError("A current panelist probe identifier is required.")
        self.validate_submit(seat, turn, "Continue with original answer.", session, now, direct=True, probe_id=probe_id)
        self.discard_pending()
        session.resolve_probe(status="ended_early")
        self.resolve(session)

    def interpret(self, session: DefenseSession, decision: SubmissionDecision,
                  expected_id: int, pending: PendingSubmission, online: dict[str, int], now: int) -> str | None:
        if self.interpretation_id != expected_id or self.pending_submission is not pending:
            return None
        if decision.action == "probe":
            if pending.probe_id is not None or decision.probe is None:
                raise ValueError("A panelist cannot probe a probe reply.")
            session.begin_probe(pending.text, decision.probe, speaker_name=pending.name)
            elapsed = max(0, now - (self.pause_started_ms if self.pause_started_ms is not None else now))
            self.pause_used_ms += min(elapsed, max(0, limit('AI_PAUSE_SECONDS', 240, 600)*1000 - self.pause_used_ms))
            self.answered_by[pending.turn] = pending.name
            self.answered_by_seat[pending.turn] = pending.seat
            self.discard_pending()
            self.phase, self.error = "probe", None
            self.answer_deadline_ms = self.probe_deadline_ms = now + PROBE_MS
            self.clock_id += 1
            self.reassign(online, session)
            return "probed"
        if decision.action == "clarify":
            try:
                exchange = ClarificationExchange(pending.text, decision.clarification)
                if pending.probe_id:
                    session.turns[-1].probe.clarifications.append(exchange)
                else:
                    session.record_clarification(exchange)
                self.error = None
            except ValueError as error:
                self.error = str(error)
            elapsed = max(0, now - (self.pause_started_ms if self.pause_started_ms is not None else now))
            paused = min(elapsed, max(0, limit('AI_PAUSE_SECONDS', 240, 600)*1000 - self.pause_used_ms))
            self.pause_used_ms += paused
            self.pause_started_ms = None
            self.pause_deadline_ms = None
            self.pending_submission = None
            self.phase = "probe" if pending.probe_id else "question"
            self.answer_deadline_ms = now + max(0, pending.remaining_ms - (elapsed - paused))
            if pending.probe_id:
                self.probe_deadline_ms = self.answer_deadline_ms
            self.clock_id += 1
            self.reassign(online, session)
            return "clarified"
        self.accept_pending(session)
        return "answered"

    def accept_pending(self, session: DefenseSession) -> None:
        pending = self.pending_submission
        assert pending is not None
        if pending.probe_id:
            if session.turns[-1].probe.id != pending.probe_id:
                raise ValueError("That probe reply is stale.")
            session.resolve_probe(pending.text, speaker_name=pending.name, seat=pending.seat)
        else:
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
