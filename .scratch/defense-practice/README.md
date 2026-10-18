# Research defense practice — implementation tickets

Status: ready-for-agent

The user approved this ten-ticket breakdown as drafted on **2026-10-17**.
All ten separate local tickets are published below, with **58 acceptance
criteria covering all 108 specification stories**. Tickets 01–07 are implemented and
code-reviewed locally; ticket 08 is implemented and ready for human review; ticket
09 is implemented and locally verified pending review. User review, actual
speech/device validation and ticket 10 remain pending.

Parent: [research-defense practice specification](spec.md), preserved unchanged.
Design: selected prototype **B — Speaker desk** on prototype/research-practice,
source f0d74a7 and verdict a3046c4. See the [approved breakdown](ticket-breakdown-draft.md)
for slice demos, direct story mapping and intermediate runnable boundaries.

## Tickets and dependencies

| Ticket | Blocked by | Status | Criteria |
| --- | --- | --- | --- |
| [01 — Research-first practice with varied openings](issues/01-research-first-varied-openings.md) | None | ready-for-human | 6 |
| [02 — Host choice when an opening repeats](issues/02-repeated-opening-host-choice.md) | [01](issues/01-research-first-varied-openings.md) | ready-for-human | 5 |
| [03 — Live voice answers in Speaker desk](issues/03-live-voice-answers.md) | None | ready-for-human | 8 |
| [04 — Voice probe replies and recovery across screens](issues/04-voice-probes-and-recovery.md) | [03](issues/03-live-voice-answers.md) | ready-for-human | 6 |
| [05 — Grounded per-answer text coaching](issues/05-per-answer-text-coaching.md) | None | ready-for-human | 7 |
| [06 — Progressive coaching with safe completion and recovery](issues/06-progressive-coaching-recovery.md) | [05](issues/05-per-answer-text-coaching.md) | ready-for-human | 7 |
| [07 — Evidence-based voice delivery feedback](issues/07-voice-delivery-feedback.md) | [04](issues/04-voice-probes-and-recovery.md), [05](issues/05-per-answer-text-coaching.md) | ready-for-human | 6 |
| [08 — Android microphone practice](issues/08-android-microphone.md) | [04](issues/04-voice-probes-and-recovery.md) | ready-for-human | 4 |
| [09 — iOS microphone practice](issues/09-ios-microphone.md) | [04](issues/04-voice-probes-and-recovery.md) | ready-for-human | 4 |
| [10 — Complete defenses and local review handoff](issues/10-integrated-practice-review.md) | [02](issues/02-repeated-opening-host-choice.md), [06](issues/06-progressive-coaching-recovery.md), [07](issues/07-voice-delivery-feedback.md), [08](issues/08-android-microphone.md), [09](issues/09-ios-microphone.md) | ready-for-agent | 5 |

## Where to start

Tickets **01–07** are implemented and independently code-reviewed locally.
Checkpoints 1–3 are locally implemented and verified offline; actual speech/provider and user visual evidence remain pending.
User visual/live-quality review is pending. See [ticket 07 review and screenshots](reviews/07.md).
Research/mixed reports now use bounded progressive sections up to the supported
100-question budget, preserving ready work and financial recovery. Voice remains default-off pending actual provider checks.
Tickets **08 (Android)** and **09 (iOS)** are implemented and locally verified with
real-device and iOS-build evidence pending. Their 2026-10-19
[native review](reviews/native-check-2026-10-19.md) found two lifecycle/recovery
defects (iOS teardown blocked by its own navigation policy; Android Retry did not
restore capture recovery); both are fixed in the working tree, with the iOS
policy tests and all real-device/iOS-build evidence still pending.
Recommended next: **10 — Complete defenses and local review handoff**, whose
blockers 08 and 09 are implemented, once human review and the pending device
evidence allow.
A ready-for-agent status does not remove any listed blockers.

Independent features are not given artificial dependencies. Coordinate shared
source edits rather than assuming these tickets authorize parallel agents or
external-model sharing. No broad standalone prefactor is required; introduce
narrow additive contracts before migrating their callers in the first slice.

## Four runnable checkpoints

| Checkpoint | Tickets | Completed behavior |
| --- | --- | --- |
| 1 — Opening history | 01, 02 | Research-first setup, recent grounded openings and explicit host repetition choice. |
| 2 — Live web voice | 03, 04 | Speaker desk answers/probe replies, bounded relay, shared allowance and safe manual recovery. |
| 3 — Complete answer coaching | 05, 06, 07 | Grounded every-answer text/voice feedback, progressive Results and correct completion/recovery; typed Streamlit shared. |
| 4 — Native and integration | 08, 09, 10 | Android/iOS source/build integration and complete local handoff with real-provider/device gaps identified separately. |

Every slice includes its own relevant verification and leaves the app runnable.
Intermediate scope is explicit: 01 fails safely on repeated Q1 until 02; 03 keeps
probe input typed until 04; 05 supports complete short reports and rejects
incomplete output until 06 adds bounded long-report sections. Essential mic
permission, authorization, cap, deadline and lifecycle safety belongs to 03,
not a later hardening ticket. Final behavior remains the full specification.

## Coverage and verification boundaries

- **01** — specification stories 1–19, 21–24, 26, 106.
- **02** — specification stories 20–25.
- **03** — specification stories 27–34, 36–47, 49–52, 54–65, 103–105, 107.
- **04** — specification stories 35, 37, 48–54, 57, 61, 64, 79, 102–105.
- **05** — specification stories 5–6, 10, 69–85, 95, 97, 104–106.
- **06** — specification stories 75–98, 106, 108.
- **07** — specification stories 64–74, 79–85, 97, 107–108.
- **08** — specification stories 99, 101–105, 108.
- **09** — specification stories 100–105, 108.
- **10** — specification stories 108 and integrated acceptance of 1–107.

Local publication checks verify the ten files, exact approved acceptance
criteria, acyclic blocking edges, all 108 stories and working local links.
These are documentation checks, not runtime test results. Implementation uses
the user-confirmed room HTTP/WebSocket, whole-App/browser, fake-audio/clock and
real-local-database boundaries, plus native checks. Actual speech quality,
provider configuration/cost/retention, hosted transport and installed Android/iOS
capture remain separate evidence. Missing toolchains/devices cannot be marked
passed from source inspection.

Next workflow: **Implement ticket 10 — complete defenses and local review
handoff**, unless the user selects another unblocked ticket. Tickets 08 and 09
await human review and their pending real-device/iOS-build evidence. Ticket 05
was reviewed against actual starting commit 6581ffe; see its [local
review](reviews/05.md). Publishing these local tickets does not commit source,
start a mic, make paid calls, merge, push or deploy.
