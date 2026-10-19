"""Frozen research report membership and bounded section progress, without IO."""
from dataclasses import dataclass, field, replace
from collections.abc import Callable
import secrets
from backend.research_coaching import COACHING_BATCH_SIZE
from backend.project_files import ProjectFile
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from backend.question_generator import AnsweredQuestion, CoachingReport


@dataclass(frozen=True)
class CoachingInput:
    files: tuple[ProjectFile, ...]
    history: tuple["AnsweredQuestion", ...]
    research_context: dict | None
    defense_type: str
    research_stage: str
    overview_only: bool = False
    section_turns: tuple[int, ...] | None = None
    provider_scope: str | None = None
    provider_owner: str | None = None
    provider_stopped: Callable[[], bool] | None = None


@dataclass
class CoachingSection:
    id: str
    turns: tuple[int, ...] | None
    status: str = 'pending'
    attempts: int = 0
    error: str | None = None
    report: "CoachingReport | None" = None


@dataclass
class CoachingProgress:
    request: CoachingInput
    attempt_limit: int = 3
    id: str = field(default_factory=lambda: secrets.token_hex(12))
    sections: list[CoachingSection] = field(default_factory=list)
    completion_status: str = 'pending'
    completion_attempts: int = 0
    completion_error: str | None = None
    closing_started: bool = False
    cancelled: bool = False

    def __post_init__(self):
        count=len(self.request.history)
        if count>100:raise ValueError('Coaching membership exceeds the supported question budget.')
        self.sections=[CoachingSection('overview',None)] + [CoachingSection(f'answers-{start}',tuple(range(start,min(start+COACHING_BATCH_SIZE,count)))) for start in range(0,count,COACHING_BATCH_SIZE)]

    def begin(self, section):
        if self.cancelled or section.status != 'pending' or section.attempts >= self.attempt_limit:
            raise ValueError('This coaching section cannot be started.')
        section.status, section.error = 'generating', None
        section.attempts += 1

    def accept(self, section, report):
        from backend.research_coaching import validate_overview, validate_section
        if self.cancelled or section.status != 'generating':
            raise ValueError('This coaching section is no longer current.')
        if section.turns is None:validate_overview(report, self.request.history)
        else:validate_section(report, self.request.history, section.turns)
        section.report, section.status = report, 'ready'

    @property
    def overview(self):
        return self.sections[0]

    def assembled(self):
        if self.overview.status!='ready':return None
        cards=[card for section in self.sections[1:] if section.status=='ready' for card in section.report.answer_cards]
        return replace(self.overview.report,answer_cards=sorted(cards,key=lambda c:c['turn']))

    @property
    def complete_sections(self):
        return all(section.status=='ready' for section in self.sections)

    @property
    def can_retry(self):
        if self.cancelled:return False
        if self.overview.status=='failed' and self.overview.attempts>=self.attempt_limit:return False
        return (any(s.status=='failed' and s.attempts<self.attempt_limit for s in self.sections)
            or self.completion_status=='failed' and self.completion_attempts<self.attempt_limit)

    def retry(self):
        if not self.can_retry:raise ValueError('Coaching retry allowance used. Completed cards are retained; use available recovery controls.')
        for section in self.sections:
            if section.status=='failed' and section.attempts<self.attempt_limit:
                section.status,section.error='pending',None
        if self.completion_status=='failed' and self.completion_attempts<self.attempt_limit:
            self.completion_status,self.completion_error='pending',None

    def invalidate(self, outcome='cancelled'):
        self.cancelled=True
        self.completion_status=outcome
        for section in self.sections:
            if section.status in {'pending','generating'}:section.status='cancelled'

    def snapshot(self):
        return {'job_id':self.id,'overview_status':self.overview.status,
            'cards_ready':sum(len(s.turns) for s in self.sections[1:] if s.status=='ready'),
            'cards_required':len(self.request.history), 'completion_status':self.completion_status,
            'completion_error':self.completion_error,'can_retry':self.can_retry,
            'sections':[{'id':s.id,'turns':list(s.turns) if s.turns is not None else None,
                'status':s.status,'attempts_left':max(0,self.attempt_limit-s.attempts),'error':s.error} for s in self.sections]}
