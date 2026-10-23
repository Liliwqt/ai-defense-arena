# Critical rejection diagnostic preparation — 2026-10-23

Local source work only. **No new inference authorized or executed.**
[Protocol](../../../docs/CRITICAL_REVIEW_DIAGNOSTICS.md),
[exact proposed plan](08-critical-replay-plan.json),
[public provider research](../../../docs/DEEPSEEK_PROVIDER_CAPACITY.md).

## Scope and diagnosis

The historical Critical response is unavailable; its root cause remains unknown.
A deterministic HTTP-mocked test proved the reporting gap: a schema-valid rejected
answer with conflicting clarification text reached the original validator but
exported `unclassified`, not a specific known reason. It failed in0.588s before
the change; corresponding unchanged-class, pending-input and no-content-leak
checks now pass. This proves instrumentation, not the historical provider cause.

Static allowlisted codes identify existing submission, plan and bounded-lookup
rejection guards. Existing predicates, exception types/messages, accepted state,
retry policy, model/reasoning settings and financial effects remain unchanged.
Unknown or non-string diagnostic attributes remain unclassified. No provider
output, submitted answers or hidden reasoning are added to logs.

The two-request GLM/low/6144 diagnostic reconstructs the seven-question synthetic
English state with six prior role-script answers and the pending seventh.
Citations are resolved from original accepted source, including research kind,
location and surrounding text. The new fixed synthetic map ID makes this a
reconstruction rather than retained original wire bytes. It does not call earlier
stages, write a next question, expand lookup, retry, generate coaching or publish
room state. Replies pass original submission and prospective-plan validation.

Conservative bounds: **US$0.0506934**; proposed fresh cap: **US$0.06**.
Earlier completed campaign approvals/ledgers remain untouched. Frozen launcher
checks18source hashes/exact plan before key read and rejects old output. It pins
subprocess database settings to the new isolated ledger; CLI refuses any mismatch
before credential loading, directory creation or dispatch. Late receipts therefore
keep that ledger after timeout/context restoration. Unknown receipts can still
retain holds if the process exits; no remote-cancellation guarantee is made.

## Standards

Independent review against approved ticket08baseline `8465a88`, with the new
runtime delta isolated through prework snapshots/scoped patch: **0 hard
violations;1optional duplicated-code smell**. The new Critical timed-probe/stream/
CLI orchestration resembles the earlier Impact harness and could be consolidated
if maintained. No unrelated abstraction was introduced for that optional concern.

The reviewer also identified a timeout ledger-restoration concern. The
pre-pinned subprocess settings plus execute guard above resolve it for the
prepared execution path; independent Standards recheck confirmed this. No backend
payment/account-store interface or timing limit was changed to fix it.

## Spec

Independent review and final citation/ledger recheck: **0 confirmed findings**.
Historical cause, live quality/capacity and full-defense readiness remain open.
No production provider route or reasoning setting is promoted. Public endpoint
metadata suggests `inference-net/fp8` as a same-model candidate; no live inference
establishes its capacity or private admission. BYOK/account settings were not read
or changed, and no silent fallback was introduced.

## Verification

- Nine focused new tests: **passed in1.446s**, provider HTTP mocked. Covers
  semantic/plan/lookup diagnostics, valid actions, pending rejected inputs,
  safe-code allowlist, no earlier-stage replay, citation context and DB guard.
- Whole mocked CLI: two requests, two valid clarification actions, retained
  research citation context, pinned ledger settings, US$0.06 admission cap,
  correct supplied funding and unreviewed gate; dummy key, no inference.
- React: **414 passed**; production build passed on the unchanged frontend.
  Initial symlinked isolation was rejected by Vite's worker-path guard; copied
  dependencies within the checkpoint and reran successfully, no source workaround.
- Final exact isolated Python: **880 passed in184.875s**, external providers
  mocked. Initial879passed202.098s before the additional citation regression;
  rerun justified by the reconstruction-fidelity change.
- Base `4a6be54` plus15exact scoped files and3own-runtime-patch files excludes
  foreign pending reasoning/budget edits.18frozen hashes, root/public/frozen plan,
  launcher compile/JSON/scoped whitespace checks pass. No provider output exists.

No new hosted, installed-device, user visual/native-language or provider evidence;
no financial DB mutation outside temporary benchmark/test ledgers, push or deploy.
Ticket08 stayspartial4/7 with original provider gates unresolved. This review
records agent code review, not human approval or a completed live checkpoint.
