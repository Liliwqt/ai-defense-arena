# Panelist detail probe: discovery

Started: 2026-10-09
Status: interview in progress. Scenarios confirmed by the user; design decisions
still open. Nothing implemented. No glossary term settled yet.

## The feature

A panelist can drill into a defender's answer when the answer is vague, ambiguous,
or unsupported, and the exchange is recorded on the turn. The panelist initiates it
unprompted. It does not become a new question.

This does not exist today. There is no panelist-initiated request of any kind in
`timed_turn.py`, `game_server.py`, or `game/src/`.

## What exists, and why it is not this

Three mechanisms are adjacent but none is this feature:

1. **Clarification** (`CONTEXT.md:24`) — *defender*-initiated, explains the same
   question. `interpret_submission` (`question_generator.py:225`) classifies a free-text
   submission as `answer` or `clarify`; there is no explicit button, the classifier
   infers intent. Same question, same citation, no new turn, no new vote. Capped at 2
   per turn by a bare literal in two places (`defense_session.py:133`,
   `timed_turn.py:145`). Each clarification also consumes one interpretation attempt
   (`timed_turn.py:159`), so the budgets are coupled.
2. **Follow-up** — *panelist*-initiated but costs a whole new Defense turn: new vote,
   new citation, new clocks, a slot from the budget. Permitted for code-only at
   `defense_session.py:81` (a panelist may speak twice) but not flagged `is_follow_up`
   in the snapshot. Research/mixed sets the flag properly (`defense_session.py:282`).
3. **Coverage assessment** — research/mixed only. The next-move request marks a resolved
   topic `discussed` / `needs clarification` / `addressed` (`defense_session.py:301`).
   It notices the gap and files it; nothing returns to the defender.

Current prompts actively suppress this behaviour:
- `question_generator.py:768-770` — "Accept a sufficient explanation; do not challenge
  it again just to fill a turn."
- `question_generator.py:681` — "Do not merely repeat your earlier question."

## Confirmed scenarios

Illustrative examples from the user, not decisions. One of three was removed after
review; two remain.

### B. Grounded confirmation

The user's original example, condensed from three probes to one.

```
Q4 · Technical Architect: How much does it cost?

Ana:  I've spent about hundreds.

Technical Architect:  Hundreds of money isn't an amount. Page 12, line 8
   lists 129,000 as the equipment allocation — so 129,000, not 129.
   Correct?

Ana:  Yes.
```

The panelist supplies the answer from the upload and asks for confirmation. Nothing is
clarified — the panelist already knew.

**Removed:** the original three-probe ladder (`Hundreds of what? Money? Rocks?
Things?` / `Money.` / `give me the specific amount` / `129`). Dropped by the user after
review: a real panelist demands the number once and moves on, and a ladder of
confirmations teaches the defender nothing while consuming the answer clock.

The defect the ladder exposed is kept, because scenario C catches it too: an answer can
be **true and useless** (`"hundreds"`). One restatement demand is enough.

### C. Unsupported claim resolved as a negative

```
Q7 · Security Reviewer: Your auth check runs before the rate limiter.
   Where exactly is the limiter enforced?

Ana:  Oh, we do have rate limiting. It's applied on every request so the
   API can't be overwhelmed.

Security Reviewer:  Rate limiting is applied on every request, but you
   cited line 41 — that's the input validator, not the limiter. The
   limiter is in config. So which is it: the validator, or a limiter
   that isn't in the file you pointed me at?

Ana:  ...I don't remember exactly. I think it might just be validation.

Security Reviewer:  Then the answer is that this project has no rate
   limiter. That's the finding.
```

The defender does not know. The panelist establishes it and the turn resolves with a
negative result rather than agreement. The user asked for this to be recorded "with
improvements" — see open question D2.

## What the surviving scenarios share

- Panelist initiates, unprompted.
- The defender's reply is short and counts as a real answer ("Yes", an admission).
- One probe per turn.
- It does not become a new question: no new vote, no new citation, no budget slot.
- The probing panelist does not continue the defense — the next panelist still owes
  their turn.
- All exchanges sit on the existing turn as request/reply pairs.

## Constraints any implementation must respect

- `ClarificationExchange` is `{request, reply}` (`question_generator.py:154`) and is
  published by `__dict__` (`game_server.py:144`), so a new field reaches every client
  with no protocol change.
- `QuestionCard.tsx:129-132` hardcodes "Defender asks:" / "{name} explains:".
  `TurnCard.tsx:20-23` and `buildDefenseSummary.ts:49-52` render the same pair.
- `question`, `interpreting`, `interpretation_retry` share one `answer_deadline_ms`
  and are one expiry group (`timed_turn.py:102-106`). `clock_id` is the authoritative
  cancellation token; a transition that does not bump it lets a stale deadline fire.
- `pause_deadline_ms` / `pause_used_ms` are a separate clock, consulted only during
  interpretation (`timed_turn.py:107-111`).
- `reassign` moves the answering defender on disconnect (`timed_turn.py:74-82`).

## Design tree

Root decisions, independent, form the frontier:

1. **D1 Term and record.** Fold into Clarification (user's stated answer: "folded"), or
   split into a separate concept. Scenario C makes this harder: a negative finding is not
   a clarification in any ordinary sense.
   - Downstream: glossary entry, exchange direction field, rendering, cap.
2. **D2 Where scenario C records.** Transcript only, coaching report only, or both — and
   if both, kept distinguishable.
   - Downstream: `generate_coaching_report`, export, transcript rendering.
3. **D3 Cost and bound.** See "How many probes" below — the question asked was whether a
   panelist probes until it has enough. Answer: no, and it should not.
   - Downstream: clock handling, cap value, budget interaction.
4. **D4 Who answers.** Chosen defender only, or any online defender.
   - Downstream: seat enforcement, reassignment.
5. **D5 Scope.** Code-only first, or all defense types.
   - Downstream: coverage vocabulary, test surface.
6. **D6 Restraint.** What stops a probe firing on every imperfect answer and turning
   practice into interrogation. Both current prompts ("accept a sufficient explanation"
   at `question_generator.py:768-770`, "do not merely repeat your earlier question" at
   `:681`) exist to prevent filler; the new trigger must narrow them rather than
   reverse them.
   - Downstream: the probe's eligibility condition, and whether "good answer, say
   nothing" is rewarded.

Already settled by the user: initiation is automatic, emitted with the next move; the
three-probe ladder is out of scope.

## How many probes: the cap is a backstop, not the mechanism

The user asked whether the panelist probes until it has "proved" the point. Recorded
answer: **no, and it should not.** Two things were bundled in that question and they
separate cleanly.

- **Does the panelist decide when it has enough?** Must be yes. There is no proof state
  to check against — a panelist never proves anything, they judge they have enough.
- **Does that repeat until satisfied?** That is the three-probe ladder with the cap
  removed, which was already rejected. It also inverts D6: a panelist that always probes
  until satisfied is a panelist that always probes.

**Recommendation: one probe per turn, and the panelist's own judgement decides whether
that turn needed one at all.** Most turns get none. The cap only catches a model that
misfires repeatedly; it is not what normally ends a probe. The panelist ends it.

**A second bound already exists and is not a cap:** the 120-second answer clock. In
scenario B that window holds Ana's answer, the panelist's probe, and "Yes." It is tight.
Whatever the cap, the clock bounds it too — an argument for being conservative, not
generous. Neither scenario shows the clock being spent; a probe that starts near expiry
would inherit almost none of it.

## D3 options, recorded

| Option | Cost to the defender | New machinery | Note |
| --- | --- | --- | --- |
| **Free, one probe per turn** (recommended) | none | `clock_id` and the shared expiry group | Turn does not resolve until the probe is answered |
| Costs a whole turn | a full re-vote for one word, plus a budget slot | almost none | Uses the existing code-only follow-up slot (`defense_session.py:81`), self-limiting to four extra turns |

The second is not hypothetical — code-only defenses already permit each panelist to speak
twice, so "probe by taking your second turn" is available today. It was rejected on weight:
re-voting Ana for "Yes" is the kind of friction that makes a practice tool feel punitive.
This is a recommendation, not a decision — D3 remains open.

## Rejected

- **The three-probe ladder** (original scenario A). Removed by the user. A real panelist
  restates once and moves on; a chain of confirmations spends the answer clock to extract
  a number and teaches nothing.
- **Probing until satisfied.** See "How many probes" above.
- **One probe per question as the cap.** Superseded — with the ladder gone, the cap
  bounds a defense, not a chain. Now recommended as the D3 value, still unconfirmed.

## Open at close of session

D1-D6 are unanswered. `CONTEXT.md` is untouched and no glossary term exists for this
feature; D1 must settle first. Handing over to another session: the scenarios,
constraints and D3 options above are the agreed part, the design tree is the open part.