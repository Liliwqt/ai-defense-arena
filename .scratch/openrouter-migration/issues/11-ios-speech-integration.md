# 11 — iOS speech integration and readiness evidence

**What to build:** The iOS app uses the proven speech path while retaining
trusted-main-frame microphone permission, interruption safety and typed fallback.

**Blocked by:** [09 — Voice probe replies, lifecycle and truthful coaching evidence](09-voice-probes-lifecycle-evidence.md).

**Status:** ready-for-agent

- [ ] Adapt only what the verified transport requires; preserve microphone purpose
  disclosure, trusted-origin/main-frame grant, single-use arm and permission races.
- [ ] Preserve teardown, inactive/background interruption handling and fresh explicit
  capture after recovery, without changing answer/probe/deadline/spending rules.
- [ ] Run available native/bridge checks; execute iOS policy tests/build on a suitable
  toolchain or record them pending. Source inspection is not a passing build.
- [ ] Collect or explicitly leave pending installed iOS capture, TCC/denial,
  interruption and reconnect/provider behavior evidence. No iOS voice readiness
  claim without its relevant gate; web typing remains usable.

## Comments

- Approved as drafted on 2026-10-19. Parent: [OpenRouter migration specification](../spec.md).
- Read the [approved dependency index](../README.md) for checkpoint boundaries and evidence gates. This ticket does not authorize a push, deployment or change to main.
