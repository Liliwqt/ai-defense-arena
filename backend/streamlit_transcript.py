"""Read-only transcript and report rendering for current and retained defenses."""

import streamlit as st

from backend.streamlit_coaching import render_research_coaching


def render_defense_transcript(session, mode):
    for number, turn in enumerate(session.turns, start=1):
        panelist_name = "Critical Reviewer" if mode != "code" and turn.panelist == "Critical Judge" else turn.panelist
        turn_label = " (follow-up)" if number > 1 and session.turns[number - 2].panelist == turn.panelist else ""
        st.markdown(f"**{panelist_name} · Question {number}{turn_label}**")
        if turn.question.lead_in:
            st.caption(turn.question.lead_in)
        st.write(turn.question.question)
        st.caption(f"Evidence: {turn.question.filename}, {turn.question.evidence_location or f'Line {turn.question.evidence_line}'}")
        st.code(turn.question.evidence_text, language="text")
        for exchange in turn.clarifications:
            st.info(f"You asked: {exchange.request}\n\n{panelist_name}: {exchange.reply}")
        if turn.ended_early:
            st.info("Ended early by host · no answer recorded.")
        elif turn.timed_out:
            st.info("Timed out · no answer recorded.")
        if turn.answer is not None:
            st.markdown("**Your answer**")
            st.write(turn.answer)
        if turn.probe:
            st.markdown("**Panelist asks for a detail**")
            st.write(turn.probe.request)
            for reference in turn.probe.references:
                st.caption(f"{reference.filename} · {reference.evidence_location}")
                st.code(reference.evidence_text)
            for exchange in turn.probe.clarifications:
                st.write(f"Defender asks: {exchange.request}")
                st.write(f"{turn.panelist} explains: {exchange.reply}")
            if turn.probe.reply is not None:
                st.write(f"Probe reply: {turn.probe.reply}")
            elif turn.probe.status != "pending":
                st.caption(f"Probe {turn.probe.status}; original answer retained.")


def render_coaching_summary(report, session, mode):
    history = session.answered_history()
    if report.closing and history:
        last_reviewer = history[-1].panelist
        if mode != "code" and last_reviewer == "Critical Judge":
            last_reviewer = "Critical Reviewer"
        st.caption(f"{last_reviewer} · Closing remarks")
        st.write(report.closing)
    st.write(report.summary)
    for point in report.strengths + report.improvements:
        st.write(f"Question {point['turn'] + 1}: {point['text']}")
    if mode != "code" and report.answer_cards is not None:
        render_research_coaching(report.answer_cards)
    st.write(report.next_step)
