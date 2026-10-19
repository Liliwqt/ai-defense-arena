# 10 — Android speech integration and readiness evidence

**What to build:** The Android app uses the proven speech path while retaining
trusted-origin microphone permission, safe foreground recovery and typed fallback.

**Blocked by:** [09 — Voice probe replies, lifecycle and truthful coaching evidence](09-voice-probes-lifecycle-evidence.md).

**Status:** ready-for-agent

- [ ] Adapt only what the verified transport requires; preserve exact-origin/main-page
  mic-only authorization, fresh explicit arming and stale permission protection.
- [ ] Verify background/interruption/document teardown and retry/reconnect do not
  resume capture or submit automatically; server scope/time/spend rules still apply.
- [ ] Run available policy/bridge tests and build the changed app where required.
  Record build metadata and distinguish tests/build from installed recording.
- [ ] Collect or explicitly leave pending real installed Android capture, denial,
  interruption and return-to-typing/provider behavior evidence. No Android voice
  readiness claim without its relevant gate; web typing remains usable.

## Comments

- Approved as drafted on 2026-10-19. Parent: [OpenRouter migration specification](../spec.md).
- Read the [approved dependency index](../README.md) for checkpoint boundaries and evidence gates. This ticket does not authorize a push, deployment or change to main.
