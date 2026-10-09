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

Final suite counts and independent Standards/Spec review are recorded in the
handoff log after those checks finish. A separate live synthetic conversation is
still needed to assess restraint, source fidelity, role voice and language
continuity. User visual review, hosted checks and physical devices are unverified.
No payment provider or account balance is changed by these mock checks.
