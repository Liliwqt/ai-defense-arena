"""AI Defense Arena hackathon app."""

import hashlib
import os

import streamlit as st
from openai import OpenAIError
from pydantic import ValidationError

from defense_session import (
    MAX_ANSWER_CHARS,
    DefenseSession,
    advance_defense,
    sync_project_session,
)
from project_files import (
    ALLOWED_EXTENSIONS,
    MAX_ARCHIVE_BYTES,
    MAX_FILES,
    MAX_TOTAL_BYTES,
    read_project_files,
)
from research_files import RESEARCH_EXTENSIONS, combine_sources, read_research_files
from question_generator import (
    DEFAULT_MODEL,
    QuestionGenerationError,
    ClarificationExchange,
    interpret_submission,
    describe_openai_error,
    generate_first_question,
)


def generation_error_message(error: Exception, model: str, api_key: str) -> str:
    if isinstance(error, QuestionGenerationError):
        return str(error)
    if isinstance(error, OpenAIError):
        return describe_openai_error(error, model, api_key)
    return "The AI returned an unexpected response. Please try again."


def generate_next_question(session, files, api_key, model):
    try:
        with st.spinner("Reviewing your answer and preparing the next question..."):
            advance_defense(session, files, api_key, model=model)
    except (QuestionGenerationError, OpenAIError, ValidationError) as error:
        st.session_state["defense_error"] = generation_error_message(error, model, api_key)
    else:
        st.session_state.pop("defense_error", None)


st.set_page_config(page_title="AI Defense Arena", page_icon="🎓")
st.title("AI Defense Arena")
st.caption("Upload a code project, a research paper, or both for a practice defense.")

st.subheader("1. Add defense materials")
defense_type = st.selectbox("Defense type", ["Code project", "Research paper", "Research + code"])
mode = {"Code project": "code", "Research paper": "research", "Research + code": "mixed"}[defense_type]
research_stage = "infer"
if mode != "code":
    research_stage = st.selectbox("Research stage", ["Let AI infer", "Proposal", "Completed study"])
    research_stage = {"Let AI infer": "infer", "Proposal": "proposal", "Completed study": "completed"}[research_stage]
uploads = st.file_uploader(
    "Project source files or ZIP",
    type=sorted(extension.lstrip(".") for extension in ALLOWED_EXTENSIONS) + ["zip"],
    accept_multiple_files=True,
    help=f"Up to {MAX_FILES} files, {MAX_TOTAL_BYTES // 1_000} KB extracted text combined.",
) if mode != "research" else []
papers = st.file_uploader(
    "Research documents (text-based PDF, DOCX, TXT, Markdown)",
    type=sorted(extension.lstrip(".") for extension in RESEARCH_EXTENSIONS),
    accept_multiple_files=True, disabled=mode == "code",
) if mode != "code" else []

if (mode == "code" and uploads) or (mode == "research" and papers) or (mode == "mixed" and uploads and papers):
    source_files, errors = read_project_files(uploads) if uploads else ([], [])
    research_files, research_errors = read_research_files(papers) if papers else ([], [])
    errors.extend(research_errors)
    files, combined_errors = combine_sources(source_files, research_files) if not errors else ([], [])
    errors.extend(combined_errors)
    for error in errors:
        st.warning(error)

    if files:
        st.success(f"Ready: {len(files)} accepted file(s).")
        st.caption("The panel receives all files listed below for every question.")
        st.subheader("Accepted files")
        for file in files:
            with st.expander(f"{file.name} · {file.detail}" if file.detail else file.name):
                st.code(file.content[:2_000], language="text")
                if len(file.content) > 2_000:
                    st.caption("Preview shows the first 2,000 characters; the full file is included.")

        fingerprint = hashlib.sha256(f"{mode}:{research_stage}".encode("utf-8"))
        for file in files:
            fingerprint.update(file.name.encode("utf-8"))
            fingerprint.update(b"\0")
            fingerprint.update(file.content.encode("utf-8"))
            fingerprint.update(b"\0")
        project_fingerprint = fingerprint.hexdigest()
        if st.session_state.get("defense_project_fingerprint") != project_fingerprint:
            st.session_state.pop("defense_error", None)
        sync_project_session(st.session_state, project_fingerprint)

        st.subheader("2. Practice defense")
        api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
        model = os.getenv("OPENAI_MODEL") or DEFAULT_MODEL
        if not api_key:
            st.warning("Set OPENAI_API_KEY in the shell, then restart the app to begin a defense.")
        st.caption(
            f"Model: {model}. Each question sends all accepted project text "
            f"(up to {MAX_TOTAL_BYTES // 1_000} KB) and earlier answers to OpenAI."
        )

        session = st.session_state.get("defense_session")
        button_label = "Start new defense" if session else "Start defense"
        if st.button(button_label, disabled=not bool(api_key)):
            try:
                with st.spinner("Reviewing defense materials..."):
                    first_question = generate_first_question(files, api_key, model=model, defense_type=mode, research_stage=research_stage)
            except (QuestionGenerationError, OpenAIError, ValidationError) as error:
                st.session_state["defense_error"] = generation_error_message(error, model, api_key)
            else:
                session = DefenseSession.start(first_question, mode, research_stage)
                st.session_state["defense_session"] = session
                st.session_state["defense_run_id"] = st.session_state.get("defense_run_id", 0) + 1
                st.session_state.pop("defense_error", None)
                st.rerun()

        if error_message := st.session_state.get("defense_error"):
            st.error(error_message)

        if session:
            answered_count = sum(turn.answer is not None for turn in session.turns)
            st.caption(f"Progress: {answered_count} answered · four panelists · up to eight questions")
            for number, turn in enumerate(session.turns, start=1):
                turn_label = " (follow-up)" if number > 1 and session.turns[number - 2].panelist == turn.panelist else ""
                st.markdown(
                    f"**{turn.panelist} · Question {number}{turn_label}**"
                )
                if turn.question.lead_in:
                    st.caption(turn.question.lead_in)
                st.write(turn.question.question)
                st.caption(
                    f"Evidence: {turn.question.filename}, {turn.question.evidence_location or f'Line {turn.question.evidence_line}'}"
                )
                st.code(turn.question.evidence_text, language="text")
                for exchange in turn.clarifications:
                    st.info(f"You asked: {exchange.request}\n\n{turn.panelist}: {exchange.reply}")
                if turn.answer is not None:
                    st.markdown("**Your answer**")
                    st.write(turn.answer)

            if session.completed:
                st.success(f"Defense complete. Review your {answered_count} answers above.")
            elif session.needs_question:
                st.info("Your answer is saved. Retry generating the next question.")
                if st.button("Retry next question", disabled=not bool(api_key)):
                    generate_next_question(session, files, api_key, model)
                    st.rerun()
            elif session.awaiting_answer:
                run_id = st.session_state["defense_run_id"]
                turn_number = len(session.turns)
                clarification_count = len(session.turns[-1].clarifications)
                with st.form(f"answer_form_{run_id}_{turn_number}_{clarification_count}"):
                    answer = st.text_area(
                        "Your answer or clarification request",
                        max_chars=MAX_ANSWER_CHARS,
                        key=f"answer_{run_id}_{turn_number}_{clarification_count}",
                    )
                    submitted = st.form_submit_button("Send to panelist")
                if submitted:
                    if not answer.strip():
                        st.error("Write an answer or clarification request before continuing.")
                    else:
                        try:
                            with st.spinner("Panelist is reading your submission..."):
                                decision = interpret_submission(
                                    files, api_key, panelist=session.turns[-1].panelist,
                                    question=session.turns[-1].question, submission=answer.strip(),
                                    clarifications=tuple(session.turns[-1].clarifications),
                                    model=model, defense_type=mode, research_stage=research_stage,
                                )
                        except (QuestionGenerationError, OpenAIError, ValidationError) as error:
                            st.error(generation_error_message(error, model, api_key))
                        else:
                            if decision.action == "clarify":
                                if clarification_count >= 2:
                                    st.error("This question has used both clarifications. Please submit an answer.")
                                else:
                                    session.turns[-1].clarifications.append(ClarificationExchange(answer.strip(), decision.clarification))
                                    st.rerun()
                            else:
                                session.submit_answer(answer)
                                if not session.completed:
                                    generate_next_question(session, files, api_key, model)
                                st.rerun()
    else:
        sync_project_session(st.session_state, None)
        st.session_state.pop("defense_error", None)
        st.info("Add the required project files and/or research documents to continue.")
else:
    sync_project_session(st.session_state, None)
    st.session_state.pop("defense_error", None)
