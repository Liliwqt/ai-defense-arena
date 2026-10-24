# Panelist activity specification: confirmed test boundaries

Status: confirmed by the user, 2026-10-24.
The historical draft filename is retained as the boundary-sketch record.
The published implementation specification is [spec.md](spec.md).

## Primary behavioral boundaries

1. Whole-App React and actual browser-visible behavior: selected Editor notes
   presentation, all task locations, visible highlighted safe context,
   disappearance on fast/normal completion, navigation/reconnect recovery,
   partial coaching, keyboard/accessibility, reduced motion and responsive views.
   Reuse existing whole-App stage/navigation/progressive-coaching tests and
   current waiting/status fixtures. Observe user-visible output rather than
   implementation-specific component trees or incidental CSS class names.
2. Existing authenticated FastAPI HTTP/WebSocket room flows: real host/guest
   membership and shared snapshots, current-operation identity/lifecycle,
   safe-context disclosure, state transitions, stale-result suppression,
   retries/cancellation/restart and preserved answer/timer/financial behavior.
   Use controlled clocks, synthetic sources/answers and mocked external AI,
   account/payment providers. Do not add a separate reasoning-stream test API.

## Supporting prior art and checks

- Current room-operation and recovery tests support edge cases not conveniently
  forced through the higher room boundary. Keep focused tests minimal and tied
  to observable behavior; do not mirror derivation helpers or animation markup.
- Existing typed Streamlit whole-flow/native-status checks verify matching task
  information, fallback and cleanup within its single-browser interface.
- Verify no added provider requests, model/reasoning changes, transcript export
  additions or activity-content analytics. Existing content-free timing records
  remain separate from ephemeral activity context.
- Full Python/React suites and production build are the agreed regression gate.
  Mocked two-client research/mixed scenarios cover both Standard and Free;
  production rollout, real-provider quality/latency and installed Android/iOS
  verification remain separate evidence.

## Prototype evidence boundary

The selected A design is captured on prototype/panelist-activity, source ef445a2,
decision f98d50d. Its local completion/recovery controls are synthetic and do not
replace real application lifecycle or authenticated multi-client tests.

No paid provider call is required for this presentation feature. No new database
or provider-facing endpoint is proposed for activity text.
