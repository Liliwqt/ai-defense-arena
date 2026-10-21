# Ticket 01 local interface evidence

Date: 2026-10-21. Code review: [verified fixes](01-fixes.md).

Completed the two remaining implementation checks using an isolated loopback
FastAPI fixture and the actual production React build, plus a real local
Streamlit server. Papers and provider responses were synthetic; provider HTTP
was mocked and databases were disposable SQLite. No paid requests or hosted
checks were made. Fixture sources, screenshots and spinner-check output remain
under `.local/turn01-interface/`.

- Mapping/preparing, draft topics and source-validation waiting appeared in the
  actual preparation page. A refresh retained operation identity/start time.
  Animated dots used `waiting-dot`; reduced motion used `none`.
- Two separate browser contexts joined a real room over HTTP/WebSocket. Opening
  generation survived socket reconnect and Controls/room navigation without
  resetting its start. Desktop 1440×960, portrait 390×844 and landscape 844×390
  captures showed readable waiting/actions without horizontal page overflow.
- Clarification, answer interpretation, same-question probe reply, failed reply
  interpretation and failed next-question generation were driven through real
  controls. Pending text was labelled not yet accepted; accepted original/reply
  text survived failures. Failure stopped active animation. Keyboard retry worked;
  the guest was not offered host-only question retry.
- A four-question research run reached progressive Results. Overview and ready
  cards remained available while another section failed. Failed-only keyboard
  retry preserved the chosen card and originals, reached 4/4 cards, settled once
  and cleared waiting animation. Refresh restored Results.
- Free mixed-mode preparation/start was checked with an Android WebView user
  agent in Chromium, touch/mobile viewport and reduced motion. Mapping failure
  presented recovery without active animation. End/restart during blocked question
  generation discarded stale work and did not publish an obsolete question.
  An early fixture accidentally reported a nonzero Free cost; the real app
  correctly blocked it. Only the fake receipt was corrected to zero.
- Streamlit's actual native spinners appeared for mapping, first/next question,
  evaluation and coaching sections; they disappeared after results. Four typed
  answers and coaching completed; a second early-ended practice exercised coaching
  on a narrow portrait page. Three focused AppTest failure/recovery checks passed
  with spinner contexts instrumented: all contexts exited, including failed
  interactions/coaching and unavailable preparation storage.

Representative captures: [landscape waiting](/home/jhonryl-pamaybay/IBM-BOB/.local/turn01-interface/evidence/question-landscape.png),
[Free mixed WebView-shaped waiting](/home/jhonryl-pamaybay/IBM-BOB/.local/turn01-interface/evidence/free-mixed-webview-waiting.png),
[portrait coaching](/home/jhonryl-pamaybay/IBM-BOB/.local/turn01-interface/evidence/coaching-ready-portrait.png),
[Streamlit section spinner](/home/jhonryl-pamaybay/IBM-BOB/.local/turn01-interface/evidence/streamlit-coaching-portrait.png).

The prior 757 Python / 409 React / build gates remain the source verification;
this continuation changed only local fixtures and handoff documents. No runtime
defect or production change was required. Both remaining local interface/lifecycle
criteria are now checked (9/9). Ticket 01 remains ready-for-human, not visually
approved by the user. The user explicitly authorized proceeding to ticket 02.

Chromium with a WebView user agent is shared-web evidence, **not an installed
Android/iOS check**. Actual provider speed/quality/cost, hosted transport,
installed-device behavior and human visual sign-off remain separate.
