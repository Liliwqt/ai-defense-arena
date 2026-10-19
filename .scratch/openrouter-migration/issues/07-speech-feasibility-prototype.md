# 07 — OpenRouter-only live-caption feasibility prototype

**What to build:** A reviewable speech experiment shows whether an OpenRouter
route can provide the agreed incremental captions and finalizing Send behavior
without exposing a key or enabling an unproven pilot.

**Blocked by:** [06 — Complete text checkpoint and measured local handoff](06-text-checkpoint-handoff.md).

**Status:** ready-for-agent

- [ ] Compare a verified chunk/transport approach against the current authenticated
  mic/read-only-draft/manual-Send contract; no final speech model is assumed.
- [ ] Demonstrate bounded buffers, temporary audio disposal, ordered/deduplicated
  results, cancellation, last-segment finalization and failure/typing outcomes.
- [ ] Record actual first/intermediate/finalization latency, English recognition,
  account/endpoint support, usage/cost and retention. Tagalog/Bisaya claims require
  separate evidence; synthetic events alone cannot pass actual speech quality.
- [ ] Review provider limits and a speech share of the defense ceiling that protects
  coaching and the existing shared ten-minute cap.
- [ ] Present the local prototype and a clear gate outcome. A failed or unreviewed
  outcome keeps voice off and blocks 08 onward; do not substitute file-at-Send,
  restore direct OpenAI or mark speech replacement complete.

## Comments

- Approved as drafted on 2026-10-19. Parent: [OpenRouter migration specification](../spec.md).
- Read the [approved dependency index](../README.md) for checkpoint boundaries and evidence gates. This ticket does not authorize a push, deployment or change to main.
