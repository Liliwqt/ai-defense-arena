"""Private single-browser scopes for the shared funded research clients.

The fallback has no account login or credit transactions. Its opaque browser
identity owns provider allowances only; remapping the same material reopens the
same durable preparation scope. A new defense explicitly establishes a new run.
No credential is kept in Streamlit state.
"""

from dataclasses import dataclass, field
import secrets
from threading import RLock
from contextlib import contextmanager

from backend.openrouter_mapping import MappingClient
from backend.openrouter_questions import RunQuestionClient, establish_run_allowance
from backend.defense_session import ResearchDefenseSession
from backend.question_generator import QuestionGenerationError
from backend.turn_recovery import QuestionPlanRecovery


@dataclass
class ResearchProvider:
    owner: str
    preparation_scope: str
    practice_tier: str = "standard"
    run_scope: str | None = None
    session: ResearchDefenseSession | None = None
    question_recovery: QuestionPlanRecovery = field(default_factory=QuestionPlanRecovery, repr=False)
    turns: object | None = field(default=None, repr=False)
    _binding_lock: object = field(default_factory=RLock, repr=False, compare=False)

    def mapping(self):
        return MappingClient(self.preparation_scope, self.owner, tier=self.practice_tier)

    def client(self, session, files, *, stopped=lambda: False):
        """Bind once before first dispatch; retries never establish another run."""
        if not isinstance(session, ResearchDefenseSession):
            raise QuestionGenerationError('OpenRouter practice requires a research or mixed defense.')
        with self._binding_lock:
            if stopped():
                raise QuestionGenerationError('This defense operation is no longer current.')
            if self.session is not session:
                self.question_recovery.invalidate()
                scope = f'{self.owner}:run:{secrets.token_hex(24)}'
                establish_run_allowance(scope, self.owner, files, session.question_budget, tier=self.practice_tier)
                self.session, self.run_scope = session, scope
            return RunQuestionClient(self.run_scope, self.owner, session, files,
                stopped=lambda: self.session is not session or stopped(),
                recovery=self.question_recovery.claim(self.preparation_scope))

    def flow(self, session, files):
        from backend.streamlit_turns import TypedDefenseFlow
        with self._binding_lock:
            if self.turns is None or self.turns.session is not session:
                self.client(session, files)
                self.turns = TypedDefenseFlow(self, session, files)
            return self.turns

    def cancel(self):
        with self._binding_lock:
            if self.turns is not None:
                self.turns.cancelled = True
            self.question_recovery.invalidate()

    @contextmanager
    def publishing(self, session, stopped):
        """Fence accepted state against a concurrent rerun changing the run."""
        with self._binding_lock:
            if self.session is not session or stopped():
                raise QuestionGenerationError('This defense operation is no longer current.')
            yield


def provider_for(state, fingerprint: str, *, tier="standard") -> ResearchProvider:
    from backend.practice_tiers import validate_tier
    validate_tier(tier)
    owner = state.get('research_provider_owner')
    if owner is None:
        owner = 'streamlit:' + secrets.token_hex(24)
        state['research_provider_owner'] = owner
    scope = f'{owner}:preparation:{fingerprint}' + (':free' if tier == 'free' else '')
    current = state.get('research_provider')
    if current is None or current.preparation_scope != scope or current.practice_tier != tier:
        if current is not None:
            current.cancel()
        current = ResearchProvider(owner, scope, practice_tier=tier)
        state['research_provider'] = current
    return current
