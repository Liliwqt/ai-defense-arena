import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Drawer } from "./Drawer";

describe("Drawer", () => {
  it("renders nothing when closed", () => {
    const { container } = render(
      <Drawer open={false} mode="controls" title="Controls" onClose={vi.fn()}>
        <p>content</p>
      </Drawer>,
    );
    expect(container.firstChild).toBeNull();
  });

  it("renders children when open", () => {
    render(
      <Drawer open={true} mode="controls" title="Controls" onClose={vi.fn()}>
        <p>drawer content</p>
      </Drawer>,
    );
    expect(screen.getByText("drawer content")).toBeTruthy();
  });

  it("calls onClose when Escape is pressed", async () => {
    const onClose = vi.fn();
    render(
      <Drawer open={true} mode="controls" title="Controls" onClose={onClose}>
        <button>focus me</button>
      </Drawer>,
    );
    await userEvent.keyboard("{Escape}");
    expect(onClose).toHaveBeenCalledOnce();
  });

  it("calls onClose when scrim is clicked", async () => {
    const onClose = vi.fn();
    render(
      <Drawer open={true} mode="controls" title="Controls" onClose={onClose}>
        <p>content</p>
      </Drawer>,
    );
    await userEvent.click(document.getElementById("drawer-scrim")!);
    expect(onClose).toHaveBeenCalledOnce();
  });

  it("focuses Close and returns focus to the opener when dismissed", () => {
    const opener = document.createElement("button");
    document.body.append(opener);
    opener.focus();
    const { rerender } = render(
      <Drawer open={true} mode="controls" title="Controls" onClose={vi.fn()}>
        <p>controls</p>
      </Drawer>,
    );
    expect(document.activeElement).toBe(screen.getByRole("button", { name: /close panel/i }));
    rerender(
      <Drawer open={false} mode="controls" title="Controls" onClose={vi.fn()}>
        <p>controls</p>
      </Drawer>,
    );
    expect(document.activeElement).toBe(opener);
    opener.remove();
  });

  it("shows the title in the heading", () => {
    render(
      <Drawer open={true} mode="transcript" title="Transcript" onClose={vi.fn()}>
        <p>t</p>
      </Drawer>,
    );
    expect(screen.getByRole("heading", { name: /transcript/i })).toBeTruthy();
  });
});
