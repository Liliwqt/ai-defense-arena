# 09 — Voice probe replies, lifecycle and truthful coaching evidence

**What to build:** Same-question voice replies and interrupted capture recover
safely across screens/reconnect, and accepted speech contributes only reliable,
attributable evidence to coaching.

**Blocked by:** [08 — Authorized OpenRouter voice answers in Speaker desk](08-authorized-web-voice-answers.md).

**Status:** ready-for-agent

- [ ] Extend the verified route to answer-probe replies without a new question number
  or altered reply deadline; original and reply speakers/provenance stay distinct.
- [ ] Stop capture on obsolete selection/turn/probe/run, navigation, disconnect and
  lifecycle events; delayed or duplicate chunks cannot populate later work.
- [ ] Preserve valid finalized-unsent draft recovery without replaying Send; reject
  forged text/provenance and never treat an unsent transcript as an answer.
- [ ] Preserve shared time/dollar usage through reconnect, cap/error typing recovery
  and temporary audio disposal. Adapt delivery facts honestly to provider support:
  no invented rates, pauses, confidence, filler counts or accent judgments.
- [ ] Verify two-client deadline/reconnect/retry/end/restart cases, Results/export
  attribution and responsive keyboard behavior with synthetic audio/providers.

## Comments

- Approved as drafted on 2026-10-19. Parent: [OpenRouter migration specification](../spec.md).
- Read the [approved dependency index](../README.md) for checkpoint boundaries and evidence gates. This ticket does not authorize a push, deployment or change to main.
