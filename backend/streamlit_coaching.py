"""Typed fallback presentation of the shared validated research coaching cards."""
import streamlit as st


def render_feedback(feedback, title):
    st.subheader(title)
    st.caption('AI practice suggestions · verify against your paper and intended meaning.')
    if feedback['strengths']:
        st.write('What worked')
        for text in feedback['strengths']:st.write(text)
    st.write('What to improve and why')
    for text in feedback['improvements']:st.write(text)
    if feedback['stronger_answer'] is not None:
        st.write('Conditional scaffold · confirm missing facts' if feedback['wording_basis']=='conditional' else 'Suggested wording')
        st.write(feedback['stronger_answer'])
        st.caption('Practice suggestion; verify the paper and your actual research decisions before using it.')
    if feedback['wording_examples']:
        st.write('Captured wording to practice: '+', '.join(feedback['wording_examples']))
    st.write('Practice task')
    st.write(feedback['practice_task'])


def render_research_coaching(cards):
    if not cards:return
    st.subheader('Practice each answer')
    selected=st.selectbox('Review a question',range(len(cards)),
        format_func=lambda i:f"Question {cards[i]['turn']+1} · {cards[i]['panelist']}")
    card=cards[selected]
    st.write(card['question'])
    with st.expander('Original answer and sources',expanded=True):
        st.caption(f"{card['speaker_name'] or 'Defender'} · Original answer")
        st.write(card['original_answer'] if card['original_answer'] is not None else 'No answer was recorded.')
        st.caption('Typed fallback · audio measurements unavailable.')
        repetitions = (card.get('delivery') or {}).get('observations', {}).get('repetition_examples', [])
        if repetitions:st.caption('Written-word observation · repeated wording: ' + ', '.join(repetitions))
        if card['citation']:
            st.caption(card['citation']['filename'])
            st.write(card['citation']['evidence_text'])
        probe=card['probe']
        if probe:
            st.write(f"Panelist asks: {probe['request']}")
            for exchange in probe['clarifications']:
                st.write(f"Defender asks: {exchange['request']}")
                st.write(f"Panelist explains: {exchange['reply']}")
            if probe['reply'] is not None:
                st.caption(f"{probe['speaker_name'] or 'Defender'} · Probe reply")
                st.write(probe['reply'])
            else:st.caption(f"Probe {probe['status']}; original answer retained.")
    with st.expander('Improvements and practice',expanded=True):
        render_feedback(card['feedback'],f"{card['speaker_name'] or 'Defender'} · Answer coaching")
        if card['probe_feedback'] is not None:
            render_feedback(card['probe_feedback'],f"{card['probe']['speaker_name'] or 'Defender'} · Reply coaching")



def progressive_research_report(files, history, context, mode, stage, api_key, model):
    """Single-browser bounded sections, using shared provider funding, not credits."""
    import copy
    from backend.coaching_progress import CoachingInput, CoachingProgress
    from backend.research_coaching import has_discussion
    job = st.session_state.get('research_coaching_job')
    if job is None:
        if has_discussion(history) and not st.button('Generate coaching', disabled=not bool(api_key)):
            return None
        from backend.streamlit_provider import provider_for
        try:
            practice = provider_for(st.session_state, st.session_state['defense_project_fingerprint'])
            practice.client(st.session_state['defense_session'], files)
            job = CoachingProgress(CoachingInput(tuple(files), tuple(copy.deepcopy(history)), copy.deepcopy(context), mode, stage,
                provider_scope=practice.run_scope, provider_owner=practice.owner))
        except Exception as error:
            from backend.question_generator import QuestionGenerationError
            st.error(str(error) if isinstance(error, QuestionGenerationError) else
                'The coaching allowance is unavailable. Ready answers are retained; retry when storage recovers.')
            return None
        st.session_state['research_coaching_job'] = job
    st.caption(f"{job.snapshot()['cards_ready']} of {len(job.request.history)} answers coached")
    failed = [section for section in job.sections if section.status == 'failed']
    if failed:
        st.error('Some coaching sections failed. Ready cards are retained.')
        for section in failed:
            st.caption(f"{section.id}: {section.error} · {max(0,job.attempt_limit-section.attempts)} attempts left")
        if job.can_retry and st.button('Retry failed coaching sections', disabled=not bool(api_key)):
            job.retry()
        elif not job.can_retry:
            st.info('Coaching retry allowance used. Keep the ready cards or start a new practice. This fallback does not process credit returns.')
    return job.assembled()


def advance_research_report(api_key, model):
    """Run after rendering ready work so the next slow request cannot hide it."""
    from backend.question_generator import generate_coaching_report, QuestionGenerationError, describe_openai_error
    from backend.research_coaching import validate_complete
    from backend.openrouter_questions import RunQuestionClient
    from openai import OpenAIError
    job = st.session_state.get('research_coaching_job')
    if job is None or job.cancelled:return
    section = next((item for item in job.sections if item.status == 'pending'), None)
    if section and (section.turns is None or job.overview.status == 'ready'):
        job.begin(section)
        request = job.request
        try:
            with st.spinner('Preparing the next coaching section…'):
                if not request.provider_scope or not request.provider_owner:
                    raise QuestionGenerationError('This retained report has no funded provider scope. Keep its ready cards or start a new practice.')
                client = RunQuestionClient(request.provider_scope, request.provider_owner, None, request.files,
                    stopped=lambda: job.cancelled or st.session_state.get('research_coaching_job') is not job).coaching()
                report = generate_coaching_report(list(request.files), list(request.history), api_key, model, client=client,
                    defense_type=request.defense_type, research_stage=request.research_stage,
                    research_context=request.research_context, overview_only=section.turns is None, section_turns=section.turns)
                job.accept(section, report)
        except Exception as error:
            section.status = 'failed'
            section.error = str(error) if isinstance(error,QuestionGenerationError) else describe_openai_error(error,model,api_key) if isinstance(error,OpenAIError) else 'The coaching section could not be prepared. Retry when the service recovers.'
        if job.complete_sections:
            validate_complete(job.assembled(), request.history, request.defense_type, batched=True)
            job.completion_status = 'ready'
        st.session_state['research_coaching'] = job.assembled()
        st.rerun()
