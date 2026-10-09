# Panelist probes within the same question

Date: 2026-10-09
Status: implemented and code-reviewed locally; live conversation and user visual review remain pending. Not approved for publication.

## Purpose

Let the current panelist request one material missing detail in a defender's
answer without creating another defense question. Preserve the original answer
and record the probe and reply separately. An adequate answer should move on.

The existing discovery.md remains an unfinished interview, not an approved spec.
This plan proposes defaults for its open choices; it does not record them as
user-confirmed decisions or change that document.

## Proposed defaults

- Name the feature **panelist probe**, separate from defender-initiated
  clarification and a budget-consuming follow-up.
- Apply to code, research and mixed defenses, with each existing role's voice.
- Permit at most one optional probe per generated question. Most answers should
  need none. Trigger only for consequential ambiguity, a missing decision detail,
  or a source-supported discrepancy. Do not impose a probe to fill conversation.
- Keep the same question number, original question, original citation, topic and
  selected speaker. Do not start another vote or consume a question-budget slot.
- Give a published probe a separate **30-second reply window**, starting when the
  validated probe is published. The initial answer ends the normal answer stage;
  the original 120-second clock is not restarted. This is a proposed timing choice,
  not a rule already chosen in discovery.
- Record the exchange in transcript/export and give it to coaching and research
  assessment as attributed context. A missed probe is separate from an unanswered
  original question. Never overwrite the original answer.
- Choose the probe during the existing submission-interpretation AI request,
  before resolving the turn. This deliberately differs from discovery's
  next-move placement: current final-turn and research-budget stopping can bypass
  next-question generation. This placement supports probes on the final question
  without adding a separate probe-generation request.
- Preserve explicit direct-answer recovery: it finalizes the answer without
  another AI gate. Do not silently reintroduce interpretation for that action.

## Conversation and evidence rules

Ask one short, concrete question about the answer's material gap. Prefer asking
the defender to explain rather than supplying the answer and requesting agreement.
Short replies and admissions are valid responses; no minimum-length heuristic.
An explicit request to explain the probe remains a defender clarification.

Reuse shared role and language guidance. Keep language requests and attribution
consistent, distinguish a defender claim from what an uploaded source supports,
and treat uploaded text, names, replies and prior AI dialogue as untrusted data.
Private team chat remains excluded.

Do not infer project-wide absence from one file or an omission in the paper.
Frame uncertain conclusions narrowly. Probe references, when present, must name
accepted source IDs and locations, resolved by existing server-owned citation
validation. Supplemental references may appear beneath the probe without changing
the original question citation. A request to explain the defender's statement
need not invent a source citation.

## Implementation slices

### 1. Shared records and AI decision

In question_generator.py, extend the structured submission decision with a
validated probe alternative, including concise request text (proposed 300-character
maximum) and optional grounded references. Return only the fields appropriate to
answer, clarification or probe; reject unknown/contradictory combinations.
Server state, not model output, decides whether a probe remains eligible.

Add an optional probe record to DefenseTurn and AnsweredQuestion, preserving
backwards-compatible defaults. Record original speaker attribution and separate
probe reply attribution. Suggested record: server-issued id, request, references,
reply, reply speaker/seat, and pending/answered/expired/ended-early status.
Keep deadline values in authoritative timed state and snapshots.

Extend the shared transcript serializer so generation, clarification, coverage
assessment and coaching see the same original answer and attributed exchange.
Do not append the panelist's request or suggestion to the defender's answer.

### 2. Authoritative same-turn state

In defense_session.py and timed_turn.py, save the initial answer when a validated
probe is accepted, but defer turn resolution, next-question generation, automatic
completion and research assessment until the probe is answered or expires.
Add an explicit pending-probe phase and a separate server-owned probe deadline.

The flow is:

    vote (15s) -> original answer (120s) -> interpretation
      -> clarification: original question resumes, existing allowance applies
      -> answer: resolve the turn and generate the next move/coaching
      -> probe: save initial answer, show probe (30s)
          -> reply: record separately, resolve once
          -> expiry: mark probe expired, retain initial answer, resolve once

There is never a probe-of-a-probe. A defender asking to simplify a probe may use
the existing clarification mechanism while retaining the probe's intent and its
remaining reply time; explanations do not create another probe or reset the clock.
The existing cumulative AI pause and attempt budgets apply, without resetting them.

Add an authenticated selected-defender reply action with both turn number and
server-issued probe id. A duplicate/stale initial submit must not accidentally
become a probe reply just because it names the same turn. Accept the first valid
reply once; reject late, duplicate, stale and non-selected submissions.

If the speaker disconnects, use the existing reassignment policy without resetting
the probe clock. Reconnection restores the same probe id, saved answer and remaining
deadline, without new AI work. Timeouts, restart and host early ending invalidate
clock/generation ids so stale results cannot reopen or resolve a replaced turn.

### 3. Server integration and recovery

In game_server.py, apply a fully validated decision atomically under the room lock.
Broadcast the saved initial answer, pending probe and timing state together.
Do not apply a partial probe if reference or response validation fails.

Preserve pending text on interpretation failure. Host/chosen-defender retry uses
the existing bounded interpretation allowance. Existing explicit acceptance of
pending text as an answer bypasses probing and proceeds safely. Probe-reply failure
retains the draft and initial answer; recovery must offer finalization using the
original answer when provider capacity is exhausted.

When an original question times out without an answer, do not invent a reply or
issue an in-turn probe; existing next-question/timeout rules apply. If a published
probe expires, keep original timed_out false and annotate the missed probe.
Do not credit an unverified admission as proof of a vulnerability or study result.

Question/coverage budgets count only generated defense questions. Assess research
coverage once using both pieces of defender evidence after resolution; a probe
expiry is not itself evidence of adequate coverage. Final-question probes must
settle before coaching, without generating an extra defense question.
Billing rules remain unchanged: no extra charge/refund solely for a probe.

### 4. React and Streamlit presentation

Update game/src/types.ts, QuestionCard, RoomDock and countdown/status helpers.
Show the original question and exact citation, a quieter saved-answer block and
an explicitly labeled **Panelist asks for a detail** exchange. Use the existing
bottom composer for the chosen defender's reply, with a visible **Probe · 0:30**
countdown; other defenders see who is replying. Keep chat available.

Keep defender clarification labels distinct from panelist-initiated requests.
Update TurnCard and buildDefenseSummary so transcript/export include original
answer, probe, reply, authors and pending/expired/ended status in sequence.
Preserve drafts on failed sends and reconnect; clear only the acknowledged draft
at the correct original-answer/probe boundary. Preserve keyboard focus and readable
portrait/landscape question scrolling.

Mirror shared decisions, records and completion in app.py. Streamlit remains a
single-browser fallback with no multiplayer vote/seat/timer; do not add a pretend
30-second timer there.

### 5. Verification and handoff

First add offline tests for the new boundaries, then implement each behavior slice:

- Adequate answer -> advance; material gap -> one probe; clarification -> same
  intent; complete source-grounded answer -> no forced probe.
- Invalid action/fields/references rejected; short replies/admissions accepted;
  answer/citation/name/turn identity preserved; no nested probe; chat excluded.
- Chosen-speaker authority, first valid reply, original-submit replay, stale ids,
  late reply/deadline races, disconnect reassignment, reconnect and restart.
- Probe expiration/early ending preserves the initial answer; genuine original
  timeout remains distinct; retry/fallback cannot duplicate a turn or AI charge.
- Probe on final code turn and exhausted research question budget; coverage and
  coaching see original answer plus reply exactly once.
- React rendering/countdowns/draft retention, clarification direction,
  transcript/export and readable desktop, portrait and short landscape layouts.
- Streamlit normal/probe/clarification/retry/completion using shared records.

Run the full Python and React suites and production build with providers mocked.
Keep fake-clock message admission aligned with the simulated vote/reply deadlines.
Complete mocked two-client code and research defenses with adequate, vague and
contradictory answers, a missed probe, clarification, reconnect, retry and coaching.
Inspect separately a live synthetic conversation for appropriate restraint,
source fidelity, useful phrasing, role voice and language continuity; mocks cannot
prove those qualities. No payment/provider mutation is required for local mocks.

Present local preview/screenshots and record evidence separately in PROJECT_LOG.md.
Work on feature/question-first-room; preserve outstanding security/account/payment
work and unrelated deletions. Main and production remain unchanged. Publishing
or deployment requires a later request.

## Out of scope

Probe chains, new panelists, new question-budget or pricing rules, scoring, voice,
team-chat AI analysis, new stored defense history, external research claims and
guarantees that a probe proves the correctness of a project or paper.
