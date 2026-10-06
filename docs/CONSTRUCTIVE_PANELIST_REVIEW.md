# Constructive panelist advice: local review

Date: 2026-10-07. Branch: `feature/question-first-room`. Specification: [constructive suggestions](../.scratch/constructive-panelists/spec.md).

## Behavior

Research and mixed reviewers receive shared guidance to examine the actual answer before occasionally offering one conditional improvement. Advice and reaction share the existing zero-to-two-sentence, 300-character lead-in. The question and exact citation remain separate. Advice may identify an alternative absent from uploads, but must not claim it is in the paper, effective by virtue of the citation, or something the team already demonstrated. Reviewers should respect objectives, practical constraints and study stage, accept sufficient explanations, and avoid repetitive recommendations.

Opening questions retain empty introductions. After a timeout there is no answer to advise on; acknowledge it neutrally. Clarification continues to explain the current question without supplying the team's answer. Coaching can offer conditional improvements tied to actual answers or unresolved issues, and must not turn panelist advice into a team strength. These semantic requirements are prompt guidance; bounds, citations and move validation remain enforced by the existing server. No new fields, actions, AI calls or timing changes were added. Code-only prompts remain unchanged.

## Evidence

- Offline: `.venv/bin/python -m unittest discover -v` passed **228 tests** with AI, Google and payment providers mocked. TestClient requires execution outside this session's sandbox; a minimal empty FastAPI TestClient stalled inside it and passed outside it.
- Selected frontend: a separate snapshot of `0d47be9` plus only this checkpoint's two React test changes passed **179 tests**, TypeScript checking and the production build. It excludes unrelated account/upload edits. No production React file changed.
- Offline frontend: `(cd game && npm test && npm run build)` passed **186 React tests**, TypeScript checking and the Vite production build. Counts include pre-existing uncommitted account/upload tests; those changes are excluded from this checkpoint's commit.
- Focused regressions exercise research/mixed request context, opening/timeout guidance, rejected overlong/multi-sentence introductions and invalid citations, atomic retry with retained answers, coaching attribution, whole-room rendering and summary export. Existing two-WebSocket-client twelve-turn research/mixed checks now carry suggestion-bearing dialogue and confirm persistence alongside actual answers.
- Streamlit, mocked: `.venv/bin/python -m unittest test_research_coverage.CoverageStreamlitTests -v` passed after the review added explicit rendered-caption assertions through the twelve-turn fallback. Advice remained separate from accepted answers; no live AI was called.
- Browser, mocked: the built React app served through FastAPI completed a **four-question research defense** and a **twelve-question mixed defense** in two independent browser contexts. Checked create/join, synchronized questions, clarification without turn advancement, voting/selected-speaker submission, exact paper/code citations, a timeout and immediate follow-up, generation failure/retry, reload/reconnect, transcript and coaching. The local-only harness advances the server clock for vote/answer expiry and uses synthetic accounts and documents; it makes no provider calls and is not shipped.
- Browser layout: long bounded advice at **1366×768**, **390×844**, and **844×390** remained reachable through the question card's internal scroll with no page-level horizontal overflow. Header, both seat strips and bottom dock remain visible. Transcript drawer Escape/focus behavior was exercised. These are browser viewports, not physical device/WebView checks.

## Review captures

- [Desktop dialogue](../screenshots/constructive-advice-mock-desktop.png)
- [Portrait dialogue](../screenshots/constructive-advice-mock-portrait.png)
- [Landscape dialogue](../screenshots/constructive-advice-mock-landscape.png)
- [Four-question transcript/coaching](../screenshots/constructive-advice-mock-coaching.png)
- [Twelve-question mixed transcript/coaching](../screenshots/constructive-advice-mock-mixed-complete.png)

All pictured advice is a mock response used to test rendering, not live AI output or a script embedded in the panelist prompts. On a short landscape screen, scroll the middle card to reach the question and document excerpt below the long lead-in.

The session's local mock server is at **http://127.0.0.1:8870/**. While it remains running, join room **6HGBYXCCUW** with a display name and open Transcript to inspect the completed mixed defense. Rooms disappear on restart. The harness lives in `/tmp/constructive-review-server.py`, binds only loopback, and is not an application authentication bypass in the repository.

## Pending review

No OpenAI key was available to this implementation process. Live synthetic proposal, completed-study and mixed conversations still need inspection with sufficient, vague, contradictory, constrained and Taglish answers. Check specific reactions, defensible alternatives, stage accuracy, non-repetitive advice, acceptance of reasonable refusal, and advice not being credited to the team. Mock success cannot establish these qualities. User visual/conversation approval, hosted verification and physical second-device/WebView checks are not claimed. Nothing was pushed or deployed; frozen `main` and the live service remain unchanged.


## Standards

Independent read-only review against starting HEAD `0d47be9` found no documented-standard violations or reportable baseline smells. Shared guidance stays in the existing generator boundary and evidence clearly distinguishes mocked checks from pending live/user review. **0 findings; no worst issue.**

## Spec

Independent read-only review found no implementation mismatch or unrequested scope. It identified the unrecorded Streamlit rendering check, now resolved by the passing mocked AppTest above. One verification requirement remains pending: live synthetic proposal, completed-study and mixed conversations with sufficient, vague, contradictory, constrained and Taglish answers. No configured key was available here. **0 code findings; 1 pending verification requirement, live dialogue quality.**
