# Compact mobile header: local review

Date: 2026-10-06. Branch: `feature/question-first-room`.
Baseline: user-confirmed starting commit `743d905`.

The existing website now uses a mobile header with Settings on the left, the
server-derived timer or factual phase status in the center, and Account on the
right. Room code, research coverage and Transcript remain available in Controls;
question progress stays on the question card. Desktop retains its navigation.
No room protocol, AI behavior, account/payment policy or native shell changed.

Review the loopback mock preview at <http://127.0.0.1:8816/?preview=1>.
It uses no AI calls; the ordinary app has the same layout after building React.

- [Portrait, long question and clarification](../screenshots/mobile-header-portrait.png)
- [Landscape, research question](../screenshots/mobile-header-landscape.png)
- [Simulated keyboard viewport](../screenshots/mobile-header-keyboard.png)
- [Desktop](../screenshots/mobile-header-desktop.png)
- [Controls and research coverage](../screenshots/mobile-header-controls.png)
- [Portrait source line](../screenshots/mobile-header-source-portrait.png)
- [Landscape extracted document citation](../screenshots/mobile-header-source-landscape.png)

## Evidence

- Red/green at the existing whole-room React boundary: Settings navigation was
  absent, opening/review status was absent, and drawer coverage count was absent
  before their respective implementation slices. The tests then passed.
- Working-tree offline gate: 219 Python tests (AI/Google/PayMongo mocked),
  184 React tests and production build pass. An isolated checkout of the selected
  staged files, excluding pre-existing Account/upload changes, passes 177 React
  tests and build. The seven-test difference belongs to that pending work. The restricted-sandbox Python
  TestClient stalled before its first result; stopped it and ran the same suite
  with local socket/thread access. That run completed in 13 seconds.
- Local real-browser mock previews at 320x568, 390x844, 667x375, 390x360 and
  1365x900: no horizontal page overflow; two 44x44 mobile icon targets; timer
  centered within 0.01 CSS pixel. Long code remains horizontally scrollable and
  research extracted text remains labeled; the question reading area scrolls
  internally. Research status, clarification history and question 11 of 24 remain
  accessible. Reading-area heights for the long fixture were approximately
  289/450/106/91/505 pixels respectively.
- Keyboard/browser checks: Settings to Transcript changes focus to Close;
  Escape restores Settings. Account opens; hidden desktop actions are omitted
  from mobile Tab order. Enlarged text at 125% has no horizontal page overflow.
- Fresh two-client local defense, all providers mocked: portrait host and
  landscape guest completed four questions with speaker votes, matching exact
  citations, shared answers/transcript/coaching, and guest reconnect during
  voting and after completion. Same-turn draft survived drawer navigation and
  simulated keyboard resize. Fixture clock advanced deadlines without changing
  production timing. Earlier helper attempts lacked the Origin header or used
  an incorrect vote label and were corrected only in the helper.

## Review and limits

Independent read-only reviews used the selected staged diff against the
user-confirmed latest starting commit, `743d905`. Both also checked the final
CSS correction preserving desktop labels at 1365x375. Mobile labels remain hidden.

### Standards

No documented-standard breaches found. One nonblocking **Duplicated Code**
judgment call: the addressed-topic count added to the research drawer repeats
HUD's simple count and presentation. A shared helper could keep both displays
consistent if the rules change. Retained the short expression for this checkpoint;
no current semantic divergence or correctness defect was found.

### Spec

No actionable implementation defects or scope creep found. Settings/status/Account
navigation, desktop controls, Transcript and coverage access, server countdown
and paused-time semantics, truthful review statuses and whole-room checks match
the specification. Artifacts and local preview are provided; user visual review
remains pending. No account/payment, backend, protocol, AI or native changes enter
the selected diff.

Review totals: Standards 0 hard breaches / 1 nonblocking smell; Spec 0 actionable
findings. User visual review remains pending. Implementation checks above do not establish deployment, paid AI calls,
installed-device or physical-keyboard evidence. The user subsequently requested
push/deploy; current rollout results are recorded separately in PROJECT_LOG.md. Main
remains frozen. Unrelated Account/upload edits and screenshot deletions are
excluded from the selected commit.

## Hosted rollout — 2026-10-06

User subsequently requested push and deployment. Source `b5502e3` and rollout
`23248cf` are published on the feature branch. The authenticated Render dashboard
identified Defense-Simulator, service `srv-dat25hm0tbcc739j4nfg`, connected to
`feature/question-first-room` and <https://defense-simulator.onrender.com>.
The similarly named older service is connected to frozen main and was not modified.

The automatic build succeeded but deployment failed immediately with “Cause of
failure could not be determined.” One Manual Deploy → Deploy latest commit retry
of the same release succeeded; Render shows `23248cf` Live in deployment
`dep-db29a37lot8c73ebsfgg`. Startup logs show one Uvicorn worker, successful
application startup and public service availability. No runtime, secret, build
command, instance size or branch setting was changed.

Hosted `/health` returns 200 with status ok. Served JS and CSS SHA-256 bytes match
the isolated tested source exactly:

| Asset | SHA-256 |
| --- | --- |
| index-Oq6ye7B_.js | d84802cd5ca1f8b1ba5d0badca5e978376b18709271e3b5069973ef3a60f1023 |
| index-CG8bX7IF.css | 7d4fbae8447e53a8466338eddc118237251e0bb2b68bbf075476d0d7dbe05362 |

Actual hosted browser checks use synthetic preview dialogue, with no AI/provider
calls: portrait390x844, landscape667x375 and desktop1365x900 have no horizontal
page overflow. Mobile icon targets remain44x44, with centered timer within0.01
CSS pixel. Research excerpts, question11of24, internal scrolling, Controls coverage,
Transcript, Account and Escape focus return work. Ordinary unauthenticated setup
and empty Transcript also work without page errors; `/api/auth/me` returns200
and Google configuration enabled. These checks establish served layout and API
availability, not a fresh authenticated live AI defense or physical device.

Hosted captures: [portrait](../screenshots/mobile-header-hosted-portrait.png),
[landscape](../screenshots/mobile-header-hosted-landscape.png),
[desktop](../screenshots/mobile-header-hosted-desktop.png).
Documentation receipt uses `[skip render]` to avoid another room-erasing deploy.
User visual review and native/provider/device prerequisites remain separate.
