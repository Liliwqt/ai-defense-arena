# 09 — Integrated defenses and local review handoff

**What to build:** a reviewer can inspect the complete runnable improvement and see
exactly which correctness, latency, quality and deployment claims are supported.

**Blocked by:** 07 — Typed Streamlit optimized-flow parity;
08 — Measured reviewer settings and provider gate.

**Status:** ready-for-human

Source: [confirmed specification](../spec.md). Breakdown approved on 2026-10-21.

- [x] Complete mocked two-client eight/twelve-question research/mixed defenses with
  all reviewer turns, clarification/probes, direct/saved recovery, openings,
  timeouts, retry/lookup, reconnect, ending/restart and progressive completion.
- [x] Prove call-count and deadline behavior, invalid-plan/citation refusal, changed
  context invalidation, legacy/result compatibility, no answer loss/time refund
  and no duplicate charge/history/return/settlement.
- [ ] Run full Python/React suites and production build plus the real local
  PostgreSQL allowance/once-only gate; providers remain mocked in offline checks.
- [x] Inspect desktop/portrait/landscape browser behavior with keyboard/reduced-motion
  states, truthful waiting/elapsed text, retained cards and reachable recovery.
  Record screenshots/interaction evidence and present a local preview.
- [x] Confirm shared Free recovery/status without a paid route/quota reset or claim
  that its provider capacity improved. Mapping/coaching deadlines, code-only
  disablement and voice-off boundaries stay intact.
- [x] Include 08's actual comparison evidence and unresolved limits. Keep correctness,
  model speed/quality/cost, hosted transport and installed-device evidence distinct;
  do not mark human review complete before it actually happens.
- [x] Remove only obsolete paths made redundant by migration, retaining required
  legacy compatibility. Review the integrated change against the source spec.
- [x] Finish checkpoint 2 only to the evidenced extent: no live-ready declaration
  without the required provider gate; no automatic publication/deployment.

## Comments

2026-10-24 — Implemented and verified locally from `6eb547c`; see [review 09](../reviews/09.md). Added `tests/test_integrated_turn_paths.py` covering answer timeout, direct/saved recovery, host ending/restart and Free completion, and corrected the synthetic router to derive a timed-out turn's assessment as `needs clarification` (the server rejects any other status). Offline gate: 920 Python (providers mocked, 1 unrelated pre-existing failure in another session's allowance test), 4/4 new integrated defenses, 57/57 router-dependent suites, 436 React/build. Synthetic Chromium desktop/portrait/landscape shows the activity block in every state with no overflow and correct live-region semantics. Ticket 08's provider gate remains failed/incomplete and is carried forward, not repaired. User visual acceptance, hosted and installed-device evidence remain pending. No paid inference, push or deployment.

2026-10-24 final recheck — The user accepted the revised mapping layout. Reopened the combined suite/PostgreSQL checkbox: the historical real-local16-check PostgreSQL receipt predates this checkpoint; this environment currently has no PostgreSQL toolchain, so no fresh gate is claimed. New full scoped Python/React/build results and independent final review are pending. Ticket08 provider gate remains open.

2026-10-24 final results — Full scoped915Python/providers mocked,437React/build pass; wider working tree920Python passes. Independent final source review has0hard/0runtime findings and1optional duplication suggestion. The combined database checkbox remains open because no fresh PostgreSQL run is available. Ticket08 provider gate remains4/7; no live-ready declaration.
