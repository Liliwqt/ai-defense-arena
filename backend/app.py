"""AI Defense Arena hackathon app."""

import hashlib
import json
import os
from typing import get_args

import streamlit as st
from openai import OpenAIError
from pydantic import ValidationError

from backend.defense_session import (
    MAX_ANSWER_CHARS,
    DefenseSession,
    ResearchDefenseSession,
    advance_defense,
    sync_project_session,
)
from backend.defense_progression import prepare_progression
from backend.project_files import (
    ALLOWED_EXTENSIONS,
    MAX_ARCHIVE_BYTES,
    MAX_FILES,
    MAX_TOTAL_BYTES,
    read_project_files,
)
from backend.research_files import RESEARCH_EXTENSIONS, combine_sources, read_research_files
from backend.research_plan import generate_research_plan, validate_question_budget, validate_profile_description, StudyApproach
from backend.question_generator import (
    DEFAULT_MODEL,
    QuestionGenerationError,
    ClarificationExchange,
    interpret_submission,
    describe_openai_error,
    generate_first_question,
    generate_coaching_report,
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


def prepare_research_scope(files, api_key, model, mode, research_stage):
    """Explicit preparation retains saved host descriptions even on failure."""
    st.session_state.pop("defense_session", None)
    st.session_state.pop("research_coaching", None)
    st.session_state.pop("defense_error", None)
    for key in ("research_plan_error", "research_budget_preview", "research_confirmed_budget"):
        st.session_state.pop(key, None)
    st.session_state["research_plan"] = None
    st.session_state["research_plan_approved"] = False
    st.session_state["research_profile_dirty"] = False
    try:
        with st.spinner("Mapping the uploaded research..."):
            plan = generate_research_plan(files, api_key, model, defense_type=mode, research_stage=research_stage,
                    profile_correction=st.session_state.get("research_profile_correction"))
    except (QuestionGenerationError, OpenAIError, ValidationError) as exc:
        st.session_state["research_plan_error"] = generation_error_message(exc, model, api_key)
    else:
        st.session_state["research_plan"] = plan
    st.rerun()


def research_profile_editor(plan, active, files, api_key, model, mode, research_stage):
    saved = st.session_state.get("research_profile_correction") or (plan.profile if plan else None)
    if saved is None:
        st.session_state["research_profile_dirty"] = False
        return
    identity = (plan.id if plan else None, json.dumps({"fields": saved.fields, "approaches": saved.approaches, "setting": saved.setting}))
    if st.session_state.get("research_profile_editor_key") != identity:
        st.session_state["research_profile_fields"] = "\n".join(saved.fields)
        st.session_state["research_profile_approaches"] = list(saved.approaches)
        st.session_state["research_profile_setting"] = saved.setting or ""
        st.session_state["research_profile_editor_key"] = identity
    st.markdown("#### Correct the practice profile")
    st.caption("Your descriptions guide practice; the uploaded paper remains the evidence. Applying changes requires a new map and fresh confirmation.")
    fields = st.text_area("Research fields (one per line)", key="research_profile_fields", max_chars=1024, disabled=active)
    approaches = st.multiselect("Study approaches", list(get_args(StudyApproach)),
                                key="research_profile_approaches", disabled=active)
    setting = st.text_input("Research setting (optional)", key="research_profile_setting", max_chars=300, disabled=active)
    dirty = fields != "\n".join(saved.fields) or set(approaches) != set(saved.approaches) or setting != (saved.setting or "")
    st.session_state["research_profile_dirty"] = dirty
    if dirty:
        st.warning("Unsaved profile changes. Apply them and remap before confirming or starting.")
    if st.button("Apply profile and remap", disabled=active or not dirty or not bool(api_key)):
        try:
            correction = validate_profile_description({"fields": [value.strip() for value in fields.splitlines() if value.strip()],
                        "approaches": approaches, "setting": setting.strip() or None})
        except ValueError as exc:
            st.error(str(exc))
        else:
            st.session_state["research_profile_correction"] = correction
            prepare_research_scope(files, api_key, model, mode, research_stage)


def research_scope_preview(files, api_key, model, mode, research_stage):
    """Single-browser research map, profile, budget, and coverage controls."""
    st.subheader("Research coverage plan")
    st.info("Prepare and confirm the research profile, topics and maximum questions before starting. The budget is not a price or credit quote.")
    saved_session = st.session_state.get("defense_session")
    active = saved_session is not None and not saved_session.completed
    plan = st.session_state.get("research_plan")
    error = st.session_state.get("research_plan_error")
    research_profile_editor(plan, active, files, api_key, model, mode, research_stage)
    dirty = st.session_state.get("research_profile_dirty", False)
    label = "Retry research map" if error else "Prepare map again" if plan else "Prepare defense"
    if st.button(label, disabled=active or dirty or not bool(api_key)):
        prepare_research_scope(files, api_key, model, mode, research_stage)
    if error := st.session_state.get("research_plan_error"):
        st.error(f"{error} Your uploads are retained; no question was generated by this request.")
    if plan is None:
        return
    if plan.profile is None:
        st.session_state["research_plan_approved"] = False
        st.warning("Prepare a new research map to review and confirm its research profile.")
        return
    profile = plan.profile
    st.markdown("### Research profile")
    st.caption("Profile confirmed by host" if st.session_state.get("research_plan_approved") and not dirty else "Suggested profile · awaiting host review")
    if profile.host_description:
        st.caption("Host description · requested practice lens, not paper evidence.")
    st.markdown(f"**Fields:** {', '.join(profile.fields)}")
    st.markdown(f"**Study approaches:** {', '.join(profile.approaches)}")
    if profile.setting:
        st.write(f"Setting: {profile.setting}")
    if profile.source_description:
        st.markdown("**Paper-based suggestion**")
        st.write(f"{', '.join(profile.source_description.fields)} · {', '.join(profile.source_description.approaches)}")
        if profile.source_description.setting:
            st.write(f"Source setting: {profile.source_description.setting}")
        st.markdown("**Paper-grounded explanation**")
    st.write(profile.explanation)
    for uncertainty in profile.uncertainties:
        st.warning(f"Profile uncertainty: {uncertainty}")
    with st.expander("Profile source references"):
        for ref in profile.references:
            st.caption(f"{ref.filename} · {ref.evidence_location} · extracted text")
            st.code(ref.evidence_text, language="text")
    st.caption("This profile guides practice. It does not certify the study or the panel's expertise.")
    st.caption(f"{len(plan.topics)} proposed topics · suggested maximum {plan.suggested_budget} questions")
    if plan.uncertainties:
        st.markdown("**Unclear or missing information**")
        for uncertainty in plan.uncertainties:
            st.write(uncertainty)
    for index, topic in enumerate(plan.topics, 1):
        name = "Critical Reviewer" if topic.panelist == "Critical Judge" else topic.panelist
        with st.expander(f"Topic {index}: {topic.title} · {name}"):
            st.write(topic.objective)
            for gap in topic.gaps:
                st.warning(f"Needs clarification: {gap}")
            for ref in topic.references:
                st.caption(f"{ref.filename} · {ref.evidence_location} · {'extracted text' if ref.evidence_kind.startswith('research') else 'source code'}")
                st.code(ref.evidence_text, language="text")
    budget = st.number_input("Question budget", min_value=4, max_value=100, step=1,
                             value=plan.suggested_budget, key="research_budget_preview", disabled=active or dirty)
    if budget < len(plan.topics):
        st.warning("This limit is smaller than the topic count. Some topics may remain unexplored.")
    if st.session_state.get("research_confirmed_budget") != budget:
        st.session_state["research_plan_approved"] = False
    reviewed = st.checkbox("I reviewed the research profile", key=f"profile_review_{plan.id}", disabled=active or dirty)
    acknowledged = not profile.needs_uncertainty_acknowledgment or st.checkbox(
        "I understand the profile has unclear information", key=f"profile_uncertainty_{plan.id}", disabled=active or dirty)
    if st.button("Confirm profile and budget", disabled=active or dirty or not reviewed or not acknowledged):
        st.session_state["research_confirmed_budget"] = validate_question_budget(budget)
        st.session_state["research_plan_approved"] = True
    if st.session_state.get("research_plan_approved") and not dirty:
        st.success(f"Maximum confirmed: {budget} questions.")
    st.caption("Source locations are validated; the map's interpretation needs your review. This budget is not a price or credit estimate.")


st.set_page_config(page_title="AI Defense Arena", page_icon="🎓")
st.title("AI Defense Arena")
st.caption("Upload a code project, a research paper, or both for a practice defense.")

st.subheader("1. Add defense materials")
defense_type = st.selectbox("Defense type", ["Code project", "Research paper", "Research + code"],
    index=1, key="practice_defense_type",
    format_func=lambda choice: "Code project · Experimental" if choice == "Code project" else choice)
mode = {"Code project": "code", "Research paper": "research", "Research + code": "mixed"}[defense_type]
if mode != "code":
    st.markdown("**Practice a clear explanation**")
    st.markdown("Answer directly → explain why → support with evidence → acknowledge a relevant limitation.")
    st.caption("For spoken practice, use the microphone in the multiplayer app when voice is available. This fallback uses typing.")
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
        if mode != "code":
            research_scope_preview(files, api_key, model, mode, research_stage)
        st.caption(
            f"Model: {model}. Each question sends all accepted project text "
            f"(up to {MAX_TOTAL_BYTES // 1_000} KB) and earlier answers to OpenAI."
        )

        session = st.session_state.get("defense_session")
        button_label = "Start new defense" if session else "Start defense"
        research_ready = mode == "code" or bool(st.session_state.get("research_plan_approved")
            and st.session_state.get("research_plan") and st.session_state["research_plan"].profile
            and not st.session_state.get("research_profile_dirty", False))
        if not research_ready:
            st.info("Prepare the research map and confirm its question budget before starting.")
        if st.button(button_label, disabled=not bool(api_key) or not research_ready):
            try:
                with st.spinner("Reviewing defense materials..."):
                    if mode == "code":
                        request = prepare_progression(None, defense_type=mode, research_stage=research_stage)
                        new_session = request.apply(request.generate(files, api_key, model, first_question=generate_first_question))
                    else:
                        new_session = ResearchDefenseSession.create(st.session_state["research_plan"],
                            st.session_state["research_confirmed_budget"], mode, research_stage)
                        st.session_state["defense_run_id"] = st.session_state.get("defense_run_id", 0) + 1
                        st.session_state.pop("research_coaching", None)
                        st.session_state["defense_session"] = new_session
                        advance_defense(new_session, files, api_key, model=model)
            except (QuestionGenerationError, OpenAIError, ValidationError) as error:
                st.session_state["defense_error"] = generation_error_message(error, model, api_key)
            else:
                session = new_session
                st.session_state.pop("research_coaching", None)
                st.session_state["defense_session"] = session
                if mode == "code":
                    st.session_state["defense_run_id"] = st.session_state.get("defense_run_id", 0) + 1
                st.session_state.pop("defense_error", None)
                st.rerun()

        # A failed research opener retains its empty prepared session so Retry
        # and End defense are available immediately, without recreating it.
        session = st.session_state.get("defense_session")
        if error_message := st.session_state.get("defense_error"):
            st.error(error_message)

        if session:
            answered_count = sum(turn.answer is not None for turn in session.turns)
            if isinstance(session, ResearchDefenseSession):
                addressed = sum(item["status"] == "addressed" for item in session.coverage.values())
                st.caption(f"Question {len(session.turns)} of {session.question_budget} · {addressed} of {len(session.coverage)} topics addressed")
                st.caption("Addressed means discussion coverage, not proof that the research is correct.")
                with st.expander("Topic coverage"):
                    for topic in session.plan.topics:
                        item = session.coverage[topic.id]
                        st.write(f"{topic.title}: {item['status']} · questions {', '.join(str(i + 1) for i in item['turns']) or 'none'}")
                        if item["reason"]:
                            st.caption(item["reason"])
                if not session.completed and st.button("End defense"):
                    session.end()
                    st.rerun()
            else:
                st.caption(f"Progress: {answered_count} answered · four panelists · up to eight questions")
            for number, turn in enumerate(session.turns, start=1):
                panelist_name = "Critical Reviewer" if mode != "code" and turn.panelist == "Critical Judge" else turn.panelist
                turn_label = " (follow-up)" if number > 1 and session.turns[number - 2].panelist == turn.panelist else ""
                st.markdown(
                    f"**{panelist_name} · Question {number}{turn_label}**"
                )
                if turn.question.lead_in:
                    st.caption(turn.question.lead_in)
                st.write(turn.question.question)
                st.caption(
                    f"Evidence: {turn.question.filename}, {turn.question.evidence_location or f'Line {turn.question.evidence_line}'}"
                )
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

            if session.completed:
                st.success(f"Defense complete. Review your {answered_count} answers above.")
                if isinstance(session, ResearchDefenseSession):
                    st.caption(f"Ending reason: {session.completion_reason}")
                    unresolved = [t.title for t in session.plan.topics if session.coverage[t.id]["status"] != "addressed"]
                    st.write("Unresolved topics: " + (", ".join(unresolved) if unresolved else "none"))
                report = st.session_state.get("research_coaching")
                if not session.answered_history():
                    st.info("The host ended before any answer or timeout was recorded. No discussion coverage was confirmed.")
                elif report is None and st.button("Generate coaching", disabled=not bool(api_key)):
                    try:
                        with st.spinner("Preparing coaching..."):
                            context = {"research_context": session.context()} if isinstance(session, ResearchDefenseSession) else {}
                            report = generate_coaching_report(files, session.answered_history(), api_key, model,
                                defense_type=mode, research_stage=research_stage, **context)
                    except (QuestionGenerationError, OpenAIError, ValidationError) as exc:
                        st.error(generation_error_message(exc, model, api_key))
                    else:
                        st.session_state["research_coaching"] = report
                        st.rerun()
                if report:
                    if report.closing:
                        last_reviewer = session.answered_history()[-1].panelist
                        if mode != "code" and last_reviewer == "Critical Judge":
                            last_reviewer = "Critical Reviewer"
                        st.caption(f"{last_reviewer} · Closing remarks")
                        st.write(report.closing)
                    st.write(report.summary)
                    for point in report.strengths + report.improvements:
                        st.write(f"Question {point['turn'] + 1}: {point['text']}")
                    st.write(report.next_step)
            elif session.needs_question:
                st.info("Your answer is saved. Retry generating the next question.")
                if st.button("Retry next question", disabled=not bool(api_key)):
                    generate_next_question(session, files, api_key, model)
                    st.rerun()
            elif session.awaiting_answer:
                run_id = st.session_state["defense_run_id"]
                turn_number = len(session.turns)
                probe = session.turns[-1].probe
                clarification_count = len(session.turns[-1].clarifications) + (len(probe.clarifications) if probe else 0)
                stage_key = probe.id if probe else "answer"
                recovery_key = f"probe_recovery_{run_id}_{stage_key}"
                if probe and st.session_state.get(recovery_key):
                    st.error(st.session_state[recovery_key])
                    if st.button("Continue with original answer"):
                        session.resolve_probe(status="ended_early")
                        st.session_state.pop(recovery_key, None)
                        if not session.completed:
                            generate_next_question(session, files, api_key, model)
                        st.rerun()
                with st.form(f"answer_form_{run_id}_{turn_number}_{clarification_count}_{stage_key}"):
                    answer = st.text_area(
                        "Your probe reply or clarification request" if probe else "Your answer or clarification request",
                        max_chars=MAX_ANSWER_CHARS,
                        key=f"answer_{run_id}_{turn_number}_{clarification_count}_{stage_key}",
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
                                    history=session.answered_history(),
                                    model=model, defense_type=mode, research_stage=research_stage,
                                    **({"research_context": {**session.context(), "current_topic": session.turns[-1].topic_id}}
                                       if isinstance(session, ResearchDefenseSession) else {}),
                                    **({"probe": probe, "original_answer": session.turns[-1].answer} if probe else {}),
                                )
                        except (QuestionGenerationError, OpenAIError, ValidationError) as error:
                            if probe:
                                st.session_state[recovery_key] = generation_error_message(error, model, api_key)
                            st.error(generation_error_message(error, model, api_key))
                            if probe:
                                st.rerun()
                        else:
                            if decision.action == "clarify":
                                try:
                                    if probe:
                                        if clarification_count >= 2:
                                            raise ValueError("Both clarifications are used. Submit a reply.")
                                        probe.clarifications.append(ClarificationExchange(answer.strip(), decision.clarification))
                                    else:
                                        session.record_clarification(ClarificationExchange(answer.strip(), decision.clarification))
                                except ValueError as error:
                                    st.error(str(error))
                                else:
                                    st.rerun()
                            elif decision.action == "probe":
                                session.begin_probe(answer, decision.probe)
                                st.rerun()
                            else:
                                if probe:
                                    session.resolve_probe(answer)
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
