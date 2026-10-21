import { act, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { WaitingIndicator } from "./WaitingIndicator";

describe("WaitingIndicator", () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  it("announces one polite factual label and hides decorative motion and ticks", () => {
    const { container } = render(<WaitingIndicator label="Thinking… Preparing your question…"
      detail="The accepted answer is saved." active startedAtMs={1000} serverNowMs={5000} />);
    const status = screen.getByRole("status");
    expect(status).toHaveAttribute("aria-live", "polite");
    expect(status).toHaveAttribute("aria-busy", "true");
    expect(status).toHaveClass("waiting-status", "is-active");
    expect(within(status).getByText("Thinking… Preparing your question…")).toBeTruthy();
    expect(within(status).getByText("The accepted answer is saved.")).toBeTruthy();
    expect(container.querySelector(".waiting-dots")).toHaveAttribute("aria-hidden", "true");
    expect(container.querySelector(".waiting-elapsed")).toHaveAttribute("aria-hidden", "true");
    expect(status.textContent).toContain("4s");
  });

  it("uses an existing server anchor across a reconnect instead of restarting at zero", () => {
    render(<WaitingIndicator label="Mapping your paper…" startedAtMs={1000} serverNowMs={61000} />);
    expect(screen.getByRole("status").textContent).toContain("1m 00s");
  });

  it("ticks locally from the server anchor without dispatching anything", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date(10_000));
    render(<WaitingIndicator label="Evaluating your answer…" startedAtMs={6000} serverNowMs={9000} />);
    expect(screen.getByRole("status").textContent).toContain("3s");
    act(() => vi.advanceTimersByTime(2000));
    expect(screen.getByRole("status").textContent).toContain("5s");
  });

  it("counts down a known retry without announcing every tick", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date(10_000));
    render(<WaitingIndicator label="Waiting to retry…" active={false} startedAtMs={null}
      retryAtMs={13_000} serverNowMs={9_000} />);
    const status = screen.getByRole("status");
    const retry = status.querySelector(".waiting-retry");
    expect(retry).toHaveAttribute("aria-hidden", "true");
    expect(retry?.textContent).toBe("Retrying in 4s");
    expect(screen.getByText("Waiting to retry…")).toBeTruthy();
    act(() => vi.advanceTimersByTime(2000));
    expect(status.querySelector(".waiting-retry")?.textContent).toBe("Retrying in 2s");
  });

  it("stops motion and busy state while waiting for a retry decision", () => {
    vi.useFakeTimers();
    render(<WaitingIndicator label="Waiting to retry…" active={false} startedAtMs={null} />);
    const status = screen.getByRole("status");
    expect(status).toHaveClass("is-static");
    expect(status).not.toHaveAttribute("aria-busy");
    vi.advanceTimersByTime(5000);
    expect(status.querySelector(".waiting-elapsed")).toBeNull();
  });
});
