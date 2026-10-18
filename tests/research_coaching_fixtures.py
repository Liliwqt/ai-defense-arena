"""Synthetic structured coaching responses; no model or network requests."""
from types import SimpleNamespace
from backend.question_generator import CoachingReport, ResearchCoachingDraft, generate_coaching_report
from backend.project_files import ProjectFile


def feedback(*, missed=False):
    return {'strengths':[] if missed else ['The answer states a limited claim.'],
            'improvements':['Explain the evidence behind that claim.'],
            'stronger_answer':None if missed else 'We will limit our claim to the campus pilot.',
            'wording_basis':'unanswered' if missed else 'supported',
            'practice_task':'Rehearse a direct claim followed by its source.', 'wording_examples':[]}


def cards_for(history):
    return [{'turn':i,'feedback':feedback(missed=item.answer is None),
             'probe_id':item.probe.id if item.probe else None,
             'probe_feedback':feedback() if item.probe and item.probe.reply is not None else None}
            for i,item in enumerate(history)]


def with_cards(draft, history, *, overview_only=False, section_turns=None):
    data = {key:getattr(draft,key) for key in ('summary','strengths','improvements','next_step')}
    data['closing']=getattr(draft,'closing','')
    from backend.question_generator import CoachingDraft
    raw_cards=cards_for(history)
    if section_turns is not None:raw_cards=[c for c in raw_cards if c["turn"] in section_turns]
    output=CoachingDraft(**data) if overview_only else ResearchCoachingDraft(**data,answer_cards=raw_cards)
    if not isinstance(draft,CoachingReport):return output
    client=SimpleNamespace(responses=SimpleNamespace(parse=lambda **kw:SimpleNamespace(output_parsed=output)))
    return generate_coaching_report([ProjectFile('fixture.md','Offline source.','research_text')],history,'offline-key',client=client,defense_type='research',overview_only=overview_only,section_turns=section_turns)


def scope_options(kwargs):
    return {key:kwargs[key] for key in ("overview_only","section_turns") if key in kwargs}
