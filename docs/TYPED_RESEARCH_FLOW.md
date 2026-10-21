# Typed research fallback

The Streamlit fallback uses the same funded OpenRouter clients as the multiplayer
app. New Standard research/mixed answers combine interpretation, coverage and
next-reviewer selection in the outgoing reviewer's request. A validated next
reviewer writes the question. Ordinary transitions therefore use two requests;
explicit source lookup and eligible retry can add requests. Openings and other
uninterpreted outcomes retain separate planning.

`backend/streamlit_turns.py` owns one typed operation. It validates a detached
prospective session before accepting an answer or probe reply, and seeds the
shared question-plan recovery with the accepted logical input. A writer failure
leaves the accepted answer and validated plan intact. **Retry question writing**
uses that plan without interpreting the answer or planning it again. If answer
interpretation fails, the draft remains explicitly **not yet accepted**; **Retry
saved submission** retries its text. Editing and sending a revised draft remains
possible under the same attempt limits.

Clarifications keep their original question and citation. Probe replies keep the
original answer as well as the reply. Context, language and exact citations use
the shared generation contracts. New Standard policies use the focused evidence
and explicit bounded lookup described in [Focused evidence](FOCUSED_EVIDENCE.md).
Every citation still validates against the complete accepted upload.

## Waiting and recovery

One Standard interactive operation has a 45-second processing window across
interpretation, broader lookup, planning/writing and automatic retry. A late
result cannot become a new question. An accepted answer remains saved if the
later stage reaches the limit. The interface stops waiting at that deadline even
if a provider connection is still blocked. Such provider work retains its old
attempt fence, so it cannot join a later manual retry or publish a late question;
its billing remains conservatively held or reconciled by the existing transport.
Manual recovery starts a fresh processing attempt
without renewing its durable spending allowance or resetting stage attempts.

The shared processing policy permits one eligible automatic transient retry
across the operation. A 429 needs a supplied short Retry-After that fits the
remaining window. Missing/long delays, exhausted daily/funding limits, invalid
decisions and configuration failures retain work for manual recovery. A second
stage does not get another independent automatic retry.

Native Streamlit waiting indicators show elapsed time and factual labels such
as **Reviewing your answer**, **Reviewing your reply**, **Answer saved. Preparing
your next question**, **Waiting to retry** and **Trying again**. These labels do
not expose private model reasoning or invent percentage progress. A rerun does
not resume an interrupted operation or replay a send automatically. A busy flow
rejects duplicate operations. Ending, remapping or changing accepted materials
invalidates pending work; publication is fenced against a newer run.

## Policy and interface boundaries

Models, reasoning, output/context limits and provider spending stay attached to
the original run. Selected models are retried without an automatic model switch.
Question attempts cannot spend protected coaching funds. Ending a defense and
generating or retrying coaching uses the original allowance, including its Free
tier. Ready coaching sections remain visible and only failed sections retry.

Free retains its separate planning/model/capacity policy and request quotas; it
shares safe recovery and factual waiting. Saved legacy policies keep their
separate-planning/full-source behavior. Code-only starts and voice remain disabled
by the existing release gates. Retained historical code results stay readable.

The fallback remains accountless and untimed for answers. It does not introduce
host-account credit charges, multiplayer votes/timers, or access to an account's
private opening history. The authenticated app's opening history and once-only
credit settlement are unchanged. A fresh browser session is not persistent
Streamlit session recovery.

Verification uses whole-App Streamlit tests with synthetic provider HTTP and
temporary SQLite, plus the same flows against real local PostgreSQL. This proves
routing, retention, validation and spending behavior; actual provider schema
support, conversational quality, latency and cost remain separate ticket 08
evidence. Human review, hosted operation and installed-device checks remain
separate from these offline tests.
