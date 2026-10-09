# Same-question panelist probes: local review

This feature is local on `feature/question-first-room`; publication is not part
of this checkpoint. The [implementation plan](../.scratch/panelist-detail-probe/implementation-plan.md)
records the proposed defaults; the unfinished discovery interview is unchanged.

A material gap may receive one short AI-generated request for detail during the
existing submission-interpretation request. Adequate answers should advance.
The original answer and citation remain saved. A probe has a server-issued ID,
its own 30-second reply window and a separate attributed reply. It does not create
a new vote, question number, coverage topic or charge. Only the chosen defender
can reply; disconnect reassignment retains the deadline. A missed probe does not
turn the original answer into a timeout. Direct-answer recovery bypasses probing.

Open the synthetic local preview:
<http://127.0.0.1:8776/?preview=1&research=1&probe=1>.
Add `&long=1` to inspect overflow. Preview dialogue is illustrative fixture data,
never embedded into live question generation. The fixture timer expires visually
but cannot exercise server actions. Refresh to review the initial countdown.

- [Desktop mock](../screenshots/panelist-probe-mock-desktop.png)
- [Portrait mock](../screenshots/panelist-probe-mock-portrait.png)
- [Short landscape mock](../screenshots/panelist-probe-mock-landscape.png)

Offline verification uses mocked AI and a fake authoritative clock. Two-client
code runs at four/eight questions and research/mixed runs at four questions check
same-turn probes, clarification, expiry, retry, reconnect, coaching and budget
completion. Shared-turn tests cover final code completion, stale/late/replayed
submissions, replacement speaker attribution and explicit recovery. React checks
cover retained drafts, pending acknowledgment, countdown and separate export.
Streamlit AppTest covers shared records and failure recovery without a mock timer.

Final full working-tree gate passed **430 Python tests** (AI/Google/PayMongo
mocked), **239 React tests**, TypeScript checking and production build. The exact
committed release, excluding unrelated local changes, passed **402 Python tests**
(providers mocked), **233 React tests** and build. Source commits: `2a804ce` and
`b86f6ae`. Browser previews at1440×900,390×844 and844×390 had no horizontal page
overflow, internal question scrolling and a visible probe label. Keyboard Enter
opened Controls; Escape closed it and restored focus. The only observed console
resource error was favicon404.

## Standards

Independent review against `e876f57` found no hard violations. Two minor
suggestions—shared answer-language classification and reuse of SourceReference—
were implemented; follow-up review reports no remaining actionable findings.

## Spec

Initial review found the pending probe's original speaker missing from AI context
after reassignment. The correction includes both server-owned names and the
current answer/citation/probe in shared serialization. A graceful-disconnect
protocol test checks this, and snapshot-only recovery is tested after an actual
offline capacity rejection. Follow-up review reports no remaining Spec findings.

 A separate live synthetic conversation is
still needed to assess restraint, source fidelity, role voice and language
continuity. User visual review, hosted checks and physical devices are unverified.
No payment provider or account balance is changed by these mock checks.
