# Constructive panelist suggestions: discovery

Started: 2026-10-07
Status: superseded by [specification synthesis](spec.md) at the user's request; the three interview choices were not answered.

## Input

The user wants panelists to examine the research and sometimes suggest an alternative, such as using one approach instead of another. University guidance and its limitations are recorded in [PANELIST_QUESTIONING_RESEARCH.md](../../docs/PANELIST_QUESTIONING_RESEARCH.md). This discovery decides the desired behavior; it does not implement it.

## Design tree and current frontier

1. Suggestion policy: selective unsolicited advice, advice only on request, or coaching only.
   - Downstream: triggers, frequency, unresolved issues, handling sufficient answers, and end-of-defense advice.
2. Scope: research and mixed defenses, or all defense types.
   - Downstream: role-specific advice and study-stage handling.
3. Evidence boundary: whether alternatives not named in uploaded material may be proposed.
   - Downstream: attribution, uncertainty, unsupported claims, and any external-source requirement.

The three root decisions are independent and form round 1. Downstream decisions will be asked after their prerequisites are settled.

## Settled decisions

The user confirmed the existing mocked generator/two-client room tests, React display tests, and a separate live conversation review as the test boundaries on 2026-10-07.

The user invoked To Spec before answering the three feature choices. The spec uses the recommended defaults as assumptions; do not treat those defaults as completed interview answers.

## Implementation facts

Read-only source inspection established:

- Existing question and move schemas provide a lead-in but no separate suggestion field. The lead-in is bounded to two sentences and 300 characters.
- Lead-ins already flow through defense history, WebSocket snapshots/reconnect, the question card, transcript, summary export, and Streamlit.
- Clarification explains the same question and forbids supplying the team's answer. It does not consume another defense turn.
- Completion has no closing panelist dialogue field; final advice fits the existing coaching report.
- Advice in the existing lead-in adds no separate turn, model request, vote, or answer deadline. Assessment must still use the team's actual answer rather than panelist advice.

The spec therefore reuses these existing boundaries and changes guidance for research/mixed modes rather than introducing a suggestion subsystem.

## Completion gate

The initial interview called for shared-understanding confirmation before implementation. The later To Spec request superseded that unfinished interview and authorized documentation synthesis; it did not supply the unanswered choices or authorize implementation/deployment. Keep feature work local on `feature/question-first-room`; the spec is published to the local Markdown tracker only.
