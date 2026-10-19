"""Private single-browser scopes for the shared funded research clients.

The fallback has no account login or credit transactions. Its opaque browser
identity owns provider allowances only; remapping the same material reopens the
same durable preparation scope. A new defense explicitly establishes a new run.
No credential is kept in Streamlit state.
"""

from dataclasses import dataclass
import secrets

from backend.openrouter_mapping import MappingClient
from backend.openrouter_questions import RunQuestionClient, establish_run_allowance
from backend.defense_session import ResearchDefenseSession
from backend.question_generator import QuestionGenerationError


@dataclass
class ResearchProvider:
    owner: str
    preparation_scope: str
    practice_tier: str = "standard"
    run_scope: str | None = None
    session: ResearchDefenseSession | None = None

    def mapping(self):
        return MappingClient(self.preparation_scope, self.owner, tier=self.practice_tier)

    def client(self, session, files, *, stopped=lambda: False):
        """Bind once before first dispatch; retries never establish another run."""
        if not isinstance(session, ResearchDefenseSession):
            raise QuestionGenerationError('OpenRouter practice requires a research or mixed defense.')
        if self.session is not session:
            scope = f'{self.owner}:run:{secrets.token_hex(24)}'
            establish_run_allowance(scope, self.owner, files, session.question_budget, tier=self.practice_tier)
            self.session, self.run_scope = session, scope
        return RunQuestionClient(self.run_scope, self.owner, session, files,
            stopped=lambda: self.session is not session or stopped())


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
            current.session = None
        current = ResearchProvider(owner, scope, practice_tier=tier)
        state['research_provider'] = current
    return current
