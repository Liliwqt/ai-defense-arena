"""Typed research exchanges using the shared validated provider contracts."""

from copy import deepcopy
from contextlib import contextmanager
from threading import Lock, Thread
from dataclasses import dataclass
from queue import Queue, Empty
from contextvars import copy_context
from time import monotonic, sleep

from backend.defense_progression import commit_progression, prepare_progression
from backend.defense_session import PlannedMove
from backend.openrouter_questions import COMBINED_PLANNING, COMBINED_PLANNING_GUIDANCE
from backend.provider_allowance import ProviderAllowance
from backend.processing_policy import ProcessingPolicy, ProcessingWindowExpired, decide_retry
from backend.resource_limits import limit
from backend import question_generator
from backend import defense_session
from backend.question_generator import (
    ClarificationExchange, CombinedSubmissionDraft, QuestionGenerationError,
)


def now_ms():
    return int(monotonic() * 1000)


@dataclass(frozen=True)
class ProcessingAttempt:
    deadline: int | None


class TypedDefenseFlow:
    def __init__(self, provider, session, files):
        self.provider, self.session, self.files = provider, session, tuple(files)
        self.policy = ProviderAllowance(provider.run_scope, provider.owner).policy()
        self.processing = (ProcessingPolicy.free() if self.policy.get('tier') == 'free' else
                           ProcessingPolicy.standard() if self.policy.get('planning_contract') == COMBINED_PLANNING
                           else ProcessingPolicy.legacy())
        self._lock = Lock()
        self.busy = False
        self.cancelled = False
        self._current = None
        self.status = None
        self.pending = None
        self.attempts = {}
        self._notify = lambda text: None

    @contextmanager
    def _operation(self, notify):
        if not self._lock.acquire(blocking=False):
            raise QuestionGenerationError('This defense operation is already in progress.')
        self.busy = True
        attempt = ProcessingAttempt(self.processing.deadline_ms(now_ms()))
        self._current = attempt
        self._automatic_retries = 0
        self._notify = notify
        try:
            self._check(attempt)
            yield attempt
        except Exception:
            self._check(attempt)
            raise
        finally:
            self.busy = False
            self._current = None
            self.status = None
            self._notify = lambda text: None
            self._lock.release()

    def _announce(self, text):
        self.status = text
        self._notify(text)

    def _call(self, kind, request, attempt):
        turn = self.session.turns[-1] if self.session.turns else None
        key = (kind, len(self.session.turns))
        cap = limit('AI_INTERPRETATION_ATTEMPTS', 6, 20) if kind == 'interpretation' else limit('AI_QUESTION_ATTEMPTS', 3, 10)
        stage = ('Reviewing your reply…' if turn and turn.probe else 'Reviewing your answer…') if kind == 'interpretation' else (
            'Answer saved. Preparing your next question…' if turn and turn.resolved and turn.answer else
            'Preparing your next question…' if turn else 'Preparing your first question…')
        retrying = False
        while True:
            self._check(attempt)
            used = self.attempts.get(key, 0)
            if used >= cap:
                raise QuestionGenerationError('This stage has used its retry allowance. Saved work is retained; end this practice or contact the operator.')
            self.attempts[key] = used + 1
            self._announce(('Trying again… ' if retrying else '') + stage)
            try:
                result = self._bounded_request(request, attempt)
                self._check(attempt)
                return result
            except Exception as error:
                self._check(attempt)
                retry = decide_retry(error, self.processing, now_ms(), attempt.deadline, cap-used-1)
                if (self._automatic_retries >= self.processing.automatic_retries
                        or (self.processing.version == 'legacy' and
                            (kind == 'interpretation' or not turn or not turn.resolved))
                        or not retry.allowed):
                    if retry.supplemental:
                        raise QuestionGenerationError(str(error)+' '+retry.supplemental) from error
                    raise
                self._automatic_retries += 1
                self._announce(f'Waiting to retry… Next attempt in {retry.delay_ms/1000:g}s.')
                sleep(retry.delay_ms / 1000)
                retrying = True

    def _bounded_request(self, request, attempt):
        if attempt.deadline is None:
            return request()
        # Provider threads may finish late and reconcile billing. They never
        # publish state, and retain this attempt's fence after manual recovery.
        result = Queue(maxsize=1)
        context = copy_context()
        def run():
            try:
                value = context.run(request)
            except BaseException as error:
                result.put((False, error))
            else:
                result.put((True, value))
        Thread(target=run, name='typed-defense-provider', daemon=True).start()
        while True:
            self._check(attempt)
            remaining = max(0, attempt.deadline-now_ms()) / 1000
            try:
                succeeded, value = result.get(timeout=min(0.05, remaining))
            except Empty:
                continue
            self._check(attempt)
            if not succeeded:
                raise value
            return value

    def _stopped(self, attempt):
        return (self.cancelled or self._current is not attempt or self.provider.session is not self.session
                or self.processing.expired(attempt.deadline, now_ms()))

    def _check(self, attempt):
        if self.processing.expired(attempt.deadline, now_ms()):
            raise ProcessingWindowExpired(self.processing.expiry_message())
        if self.cancelled or self._current is not attempt or self.provider.session is not self.session:
            raise QuestionGenerationError('This defense operation is no longer current.')

    def _client(self, attempt):
        self._check(attempt)
        return self.provider.client(self.session, self.files, stopped=lambda: self._stopped(attempt))

    def advance(self, *, notify=lambda text: None):
        with self._operation(notify) as attempt:
            self._advance(attempt)

    def _advance(self, attempt):
        request = prepare_progression(self.session)
        move = self._call('question', lambda: request.generate(list(self.files), None,
            client=self._client(attempt), next_move=defense_session.generate_next_move,
            research_move=defense_session.generate_research_move), attempt)
        candidate = request.apply(move)
        with self.provider.publishing(self.session, lambda: self._stopped(attempt)):
            self._check(attempt)
            commit_progression(self.session, candidate)
            self.pending = None

    def submit(self, text, *, notify=lambda text: None):
        with self._operation(notify) as attempt:
            return self._submit(text, attempt)

    def _submit(self, text, attempt):
        session = self.session
        if not session.awaiting_answer:
            raise ValueError('There is no question awaiting an answer.')
        text = text.strip()
        self.pending = text
        turn = session.turns[-1]
        candidate = deepcopy(session)
        prospective = candidate.turns[-1]
        combined = self.policy.get('planning_contract') == COMBINED_PLANNING
        if combined:
            if turn.probe:
                candidate.resolve_probe(text)
            else:
                prospective.answer = text.strip()
        context = (candidate if combined else session).context()
        context['current_topic'] = turn.topic_id
        def interpret():
            client = self._client(attempt)
            return question_generator.interpret_submission(
                list(self.files), None, panelist=turn.panelist, question=turn.question,
                submission=text, clarifications=tuple(turn.clarifications),
                history=session.answered_history(), defense_type=session.defense_type,
                research_stage=session.research_stage, research_context=context,
                client=client.interaction(turn.panelist, combined=combined),
                **({'probe': deepcopy(turn.probe), 'original_answer': turn.answer,
                    'original_speaker_name': turn.speaker_name} if turn.probe else {}),
                **({'text_format': CombinedSubmissionDraft, 'planning_context': context,
                    'planning_guidance': COMBINED_PLANNING_GUIDANCE} if combined else {}))
        decision = self._call('interpretation', interpret, attempt)
        self._check(attempt)
        planned = identity = None
        if decision.action == 'clarify':
            candidate = deepcopy(session)
            exchange = ClarificationExchange(text.strip(), decision.clarification)
            if turn.probe:
                if len(turn.clarifications) + len(turn.probe.clarifications) >= 2:
                    raise ValueError('Both clarifications are used. Submit a reply.')
                candidate.turns[-1].probe.clarifications.append(exchange)
            else:
                candidate.record_clarification(exchange)
            outcome = 'clarified'
        elif decision.action == 'probe':
            candidate = deepcopy(session)
            candidate.begin_probe(text, decision.probe)
            outcome = 'probed'
        else:
            if combined:
                if decision.plan is None:
                    raise QuestionGenerationError('The AI returned an incomplete research plan. Please retry.')
                planned = PlannedMove(decision.plan.panelist, decision.plan.topic_id,
                                      decision.plan.is_follow_up, decision.plan.assessment)
                candidate.validate_plan(planned)
                identity = self._client(attempt).plan_identity(history=candidate.answered_history(),
                    context=candidate.context(), defense_type=session.defense_type,
                    research_stage=session.research_stage)
            elif turn.probe:
                candidate.resolve_probe(text)
            else:
                candidate.submit_answer(text)
            outcome = 'answered'
        with self.provider.publishing(session, lambda: self._stopped(attempt)):
            self._check(attempt)
            if planned is not None:
                self.provider.question_recovery.seed(self.provider.preparation_scope, identity, planned)
            commit_progression(session, candidate)
            self.pending = None
        if outcome == 'answered' and not session.completed:
            self._advance(attempt)
        return outcome
