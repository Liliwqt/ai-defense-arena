"""Typed fallback presentation of the shared validated research coaching cards."""
import streamlit as st


def render_feedback(feedback, title):
    st.subheader(title)
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
