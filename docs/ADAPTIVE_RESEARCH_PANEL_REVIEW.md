# Adaptive research panel — ticket 01 local review

Implemented locally on `feature/question-first-room`; review baseline `c498598`.
Only ticket 01 is complete. Profile correction/remapping (02), shared subject-aware dialogue (03), and the complete checkpoint-2 review (04) remain pending.

## What changed

The existing paper-mapping request now also suggests multiple fields and study approaches, an optional setting, a short grounded explanation and uncertainties. Profile references are resolved from accepted paper text; code-only evidence cannot establish a research profile, even in mixed rooms. Streamed topic drafts remain unconfirmed until the complete output passes validation.

React and Streamlit show the profile and exact paper citations. The host explicitly reviews it and acknowledges uncertainty before confirming the current profile/map/budget. Guests can inspect the same confirmed state. Legacy maps without a profile cannot start or reserve a run. The research session captures the immutable plan/profile, which reconnect restores without classification. Code-only dialogue and payment/timer rules retain their existing behavior.

## Verification

- Working tree: 528 Python tests, AI/Google/PayMongo mocked; 273 React tests and production build passed. Separate pending reasoning/local-test work is included in that working-tree count.
- Selected ticket artifact: 520 Python tests (external providers mocked), 273 React tests and production build passed in an isolated extracted tree with its own frontend build. Its JS/CSS hashes match the working-tree build. This excludes the pending task-specific reasoning and quick-local-access implementation.
- Focused mocked tests cover invalid/missing/oversized profiles, paper-only profile references in mixed rooms, server-owned quotes, explicit confirmation, uncertain acknowledgment, host/guest authority, legacy-map rejection before reservation, frozen run context and reconnect. Streamlit AppTest covers ordinary and uncertain profiles plus existing long-defense/probe paths.
- Full offline protocol tests include code four/eight-turn and research/mixed twelve-question defenses, voting, clarification, timeout, saved-answer retry, reconnect, private PDF citations, transcript and coaching.
- Synthetic Chromium checks at desktop 1440×900, portrait 390×844 and landscape 844×390: readable profile, internal drawer scroll, no horizontal page overflow, 44-pixel checkbox labels and visible keyboard focus. Space, Tab and Enter confirmed the profile over the actual local WebSocket; Start enabled only after acknowledgment. These checks use a synthetic account, PDF and paced mapping, with no external AI/provider requests.
- Independent Standards and Spec reviews cleared ticket 01. One optional type-consistency suggestion was applied; stale Streamlit fixture labels were corrected and focused tests passed. Final review has zero remaining findings on either axis.

Live classification quality, actual Google/provider checks, installed Android/iOS verification and user visual review are separate pending evidence. This checkpoint does not publish or deploy.

## Preview

Open [the read-only profile preview](http://127.0.0.1:8844/?preview=1&plan=1).
For the interactive synthetic read/confirm path, open [the mapping fixture](http://127.0.0.1:8844/__fixture/login?case=mapping), choose Controls → Prepare defense, wait for the map, then review and acknowledge its profile before confirming. A synthetic opening question is not supplied by this fixture; use it for mapping/confirmation review only.

The preview is a separate loopback-only process with temporary storage and provider credentials removed. The user's normal server is unchanged.

- [Desktop suggested profile](../screenshots/adaptive-profile-desktop.png)
- [Portrait suggested profile](../screenshots/adaptive-profile-portrait.png)
- [Landscape confirmation controls](../screenshots/adaptive-profile-landscape.png)
- [Confirmed profile and exact PDF citation](../screenshots/adaptive-profile-confirmed.png)
