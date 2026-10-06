# Research-defense questioning and constructive suggestions

Research date: **2026-10-07**. Scope: university examiner guidance, compared with the current app prompts. This note records research and pre-implementation prompt behavior. The later local [constructive-panelist checkpoint](CONSTRUCTIVE_PANELIST_REVIEW.md) implements the selected guidance; live quality and user review remain pending.

## What the sources establish

These are institutional expectations for conducting defenses, not observational evidence that every panelist behaves this way. UK research-degree vivas, a UK undergraduate viva, Philippine graduate defenses, and a US education doctorate have different assessment rules. Their shared questioning principles can inform this simulator; their timings, panel composition, and award standards should not become universal app rules.

- **Prepare from the submitted work, then discuss it.** Westminster's August 2025 research-degree guidance recommends clear questions derived from the submission, asking rather than telling, clarifying confusion, and conducting a formal discussion. Its main guidance also allows questioning to respond to the candidate's answers. This supports grounded, responsive conversation. [Westminster, pp. 10 and 19, Appendix 2](https://www.westminster.ac.uk/sites/default/public-files/general-documents/Guidance-for-Examiners-of-Research-Degrees_0.pdf#page=19).

- **Challenge the reasoning constructively.** Southampton's February 2019 postgraduate examiner guidance contrasts a constructive comparison of the chosen method with an alternative against an accusatory claim that the alternative would have avoided difficulties. It recommends varying question types, allowing thinking time, and rephrasing a misunderstood question. Its poor-practice examples include hostile interrogation and repeatedly pursuing an examiner's favored topic. This supports methodological challenge without presuming the examiner's alternative is superior. [Southampton, pp. 5–6](https://cdn.southampton.ac.uk/assets/imported/transforms/content-block/UsefulDownloads_Download/D22673A2785F4491898FCEE0B1394F1D/Guidance%20for%20Examiners%20of%20PGR%20Awards.pdf#page=5).

- **Tailor questions and leave room to explain.** Harper Adams' undergraduate guidance recommends individual questions, logical progression, and coverage across the work. It asks examiners to explore methodological choices and alternatives without imposing personal preferences. Rephrase when a student struggles; move on if they cannot answer. Its suggested questions are adaptable discussion ideas, not a script, and undergraduate challenge should differ from doctoral challenge. [Harper Adams, pp. 7–11](https://cdn.harper-adams.ac.uk/document/page/155_Staff-Guidance-for-Conducting-an-Undergraduate-Viv.pdf#page=7).

- **Suggestions are explicitly part of a Philippine defense.** LPU-Batangas' 2023 graduate manual assigns examiners responsibility for constructive comments and suggestions. Proposal proceedings include objectives, methodology, comments, and follow-up questions. Final-defense responsibilities include checking whether results answer the approved objectives and whether conclusions and recommendations are appropriate. Suggestions therefore belong in defense practice, with attention to the study's stage. [LPU-Batangas, Proposal Defense Procedure and Responsibility of Panel of Examiners, PDF pp. 15 and 18](https://research.lpubatangas.edu.ph/wp-content/uploads/2023/06/Manual-for-Thesis-and-Dissertation-2023.pdf#page=18).

- **Ask first; offer an improvement when needed.** Georgia Southern's Educational Leadership dissertation guidance permits specific or general, retrospective or prospective questions, including open questions without a predetermined answer. It discourages long examiner lectures and telling students which method to use. Examiners should help students understand through relevant questioning; when that does not achieve understanding, they may suggest changes or improvements. This directly supports occasional suggestions rather than automatic replacement instructions. [Georgia Southern, “Questioning Process/Protocol”](https://ww2.georgiasouthern.edu/coe/edld/dissertation/defense-guidelines/).

## Current app compared with those findings

Source inspection of [question_generator.py](../question_generator.py) shows existing role focus/voice rules for methodological reasoning, ethics, impact, alternatives, and tradeoffs. `CONVERSATION_GUIDANCE` already requires one main question, meaningful reactions to actual answers, and a distinction between claims and demonstrated evidence. `_research_guidance` separates proposals from completed studies. `interpret_submission` explains the same question without supplying the team's answer. Coaching already includes turn-referenced improvements and a concrete next step.

However, question/move schemas have no dedicated suggestion field, and the questioning prompts have no explicit rule for when or how to offer a constructive methodological alternative. A model might mention one within its current prose; source inspection does not establish how frequently or well it does so. A new field is not automatically necessary.

## Proposed flow and prompt review criteria

The following is our design inference, not an institutional protocol or implemented change:

**Source observation → one question → listen → clarify, probe, or advance → occasional conditional suggestion.**

Ask why a choice serves the research objective before recommending a replacement. If an unresolved limitation warrants an alternative, identify the limitation, explain what the alternative could improve, and state its assumptions or costs. Give the team room to defend its choice. Follow-ups should resolve a meaningful gap; they should not be obligatory after every answer.

For proposals, examine planned feasibility and safeguards. For completed work, examine actual evidence and limitations; distinguish possible future improvements from findings already established. Do not infer figure contents unavailable through text extraction.

Original illustrative exchange, using a hypothetical proposal rather than an uploaded paper or source quotation:

> **Panelist:** Your proposal recruits classmates. How does that recruitment approach support your aim of understanding students across the university?
>
> **Team:** We can access our classmates, but they may not represent other departments.
>
> **Panelist:** You've identified a coverage limitation. If university-wide perspectives are essential, recruiting across departments could broaden the sample, subject to access and recruitment constraints. How would you decide whether that is feasible?
>
> **Team:** We would check access first, then either broaden recruitment or narrow our stated scope.

Review future prompts and sample transcripts for grounded premises, one main question, answer-responsive follow-ups, conditional alternatives with reasons and limits, study-stage accuracy, and respectful movement onward. Check that clarification still explains the question without giving the answer, and that coaching distinguishes examiner suggestions from team evidence. Offline mocked tests can check structure; live synthetic defenses and human review are needed to assess dialogue quality. Neither has been conducted for these proposals.
