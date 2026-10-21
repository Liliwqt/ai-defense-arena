import { describe, expect, it } from "vitest";
import { deriveRoomPresentation } from "./roomPresentation";
import { previewState } from "../previewState";
import type { RoomState } from "../types";

const operation = {
  id: "question:4", kind: "question" as const, stage: "generating",
  started_at_ms: 9000, attempt: 1, retrying: false,
};
const resolvedTurn = { ...previewState.turns[0], answer: "We will run a pilot.", resolved: true };
const accepted: RoomState = { ...previewState, phase: "generating", operation,
  turns: [resolvedTurn], server_now_ms: 61000 };

describe("deriveWaiting", () => {
  it("prefers the authoritative operation and keeps the original start on reconnect", () => {
    expect(deriveRoomPresentation(accepted).waiting).toMatchObject({
      active: true, retryWait: false, startedAtMs: 9000,
      label: "Thinking… Preparing your question…", detail: "The accepted answer is saved.",
    });
    const reconnected = deriveRoomPresentation({ ...accepted, server_now_ms: 121000 });
    expect(reconnected.waiting?.startedAtMs).toBe(9000);
  });

  it("names a transient retry instead of rotating stages", () => {
    const view = deriveRoomPresentation({ ...accepted,
      operation: { ...operation, attempt: 2, retrying: true } });
    expect(view.waiting).toMatchObject({
      active: true, label: "Trying again… Preparing your question…",
    });
  });

  it("keeps the admitted retry label during the retried interpretation attempt", () => {
    const interpretation = { ...previewState, phase: "interpreting" as const,
      operation: { id: "interpretation:4", kind: "interpretation" as const,
        stage: "reviewing_answer", started_at_ms: 9000, attempt: 2, retrying: true } };
    expect(deriveRoomPresentation(interpretation).waiting?.label)
      .toBe("Trying again… Evaluating your answer…");
  });

  it("freezes the active indicator during automatic retry backoff", () => {
    const view = deriveRoomPresentation({ ...accepted,
      operation: { ...operation, stage: "retry_wait", attempt: 2, retrying: true,
        retry_at_ms: 12_000 } });
    expect(view.waiting).toMatchObject({
      active: false, retryWait: true, label: "Waiting to retry…",
      startedAtMs: null, retryAtMs: 12_000, detail: "The accepted answer is saved.",
    });
  });

  it("distinguishes a retained submission from an accepted answer", () => {
    const state: RoomState = { ...previewState, phase: "interpreting",
      my_pending_submission: "Keep this saved answer.", server_now_ms: 5000 };
    expect(deriveRoomPresentation(state).waiting).toMatchObject({
      active: true, label: "Evaluating your answer…",
      detail: "Submission saved, not yet accepted.",
    });
  });

  it("identifies probe review and the known mapping validation stage", () => {
    const probeTurn = { ...previewState.turns[0],
      probe: { id: "p1", request: "Which list?", status: "pending" as const,
        references: [], reply: null, clarifications: [] } };
    const probe = deriveRoomPresentation({ ...previewState, phase: "interpreting", turns: [probeTurn] });
    expect(probe.waiting?.label).toBe("Reviewing your probe reply…");
    const mapping = deriveRoomPresentation({ ...previewState, phase: "lobby",
      research_planning_status: "planning",
      research_plan_progress: { stage: "validating", topics: [] } });
    expect(mapping.waiting?.label).toBe("Checking source references…");
  });

  it("shows coaching preparation only while coaching is generating", () => {
    expect(deriveRoomPresentation({ ...previewState, phase: "complete",
      feedback_status: "generating" }).waiting?.label).toBe("Preparing your coaching report…");
    expect(deriveRoomPresentation({ ...previewState, phase: "complete",
      feedback_status: "ready" }).waiting).toBeNull();
  });

  it("uses known coaching stages without inventing a sequence", () => {
    const coaching = { ...previewState, phase: "complete" as const, feedback_status: "generating" as const,
      operation: { id: "coaching:2", kind: "coaching" as const, stage: "answers",
        started_at_ms: 1000, attempt: 1, retrying: false } };
    expect(deriveRoomPresentation(coaching).waiting?.label).toBe("Preparing your answer coaching…");
    expect(deriveRoomPresentation({ ...coaching, operation: { ...coaching.operation,
      stage: "saving_completion" } }).waiting?.label).toBe("Saving your coaching…");
    expect(deriveRoomPresentation({ ...coaching, operation: { ...coaching.operation,
      retrying: true } }).waiting?.label).toBe("Trying again… Preparing your answer coaching…");
  });

  it("stops active animation for recovery waits and removes it once no longer waiting", () => {
    const retry = deriveRoomPresentation({ ...previewState, phase: "retry",
      error: "Provider failed", turns: [resolvedTurn] });
    expect(retry.waiting).toMatchObject({
      active: false, retryWait: true, label: "Waiting to retry…", startedAtMs: null,
    });
    const exhausted = deriveRoomPresentation({ ...previewState, phase: "retry",
      question_attempts_left: 0, turns: [resolvedTurn] });
    expect(exhausted.waiting).toMatchObject({ active: false, label: "Recovery needed" });
    expect(deriveRoomPresentation({ ...previewState, phase: "question" }).waiting).toBeNull();
  });

  it("does not expose a stale operation when the server phase has moved on", () => {
    const state: RoomState = { ...previewState, phase: "retry", operation: null,
      turns: [resolvedTurn], question_attempts_left: 2 };
    expect(deriveRoomPresentation(state).waiting).toMatchObject({
      active: false, retryWait: true,
    });
  });
});
