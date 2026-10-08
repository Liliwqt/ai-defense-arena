import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { ManagerPage } from "./ManagerPage";

const owner = { authenticated: true, google_enabled: true, manager_enabled: true, user: { id: "owner", name: "Owner", email: "owner@example.test" }, csrf_token: "csrf" };
const person = { id: "user", name: "Alex", email: "alex@example.test", live_credits: 20, live_reserved_credits: 10, live_held_credits: 0, test_credits: 100, free_access: false, topup_invited: false };
function setup(account = owner, mutation?: (url: string, init: RequestInit) => Promise<unknown>) {
  const fetcher = vi.fn(async (url: string, init?: RequestInit) => {
    if (init?.method) {
      if (mutation) return mutation(url, init);
      return { ok: true, json: async () => ({}) };
    }
    return { ok: true, json: async () => url === "/api/auth/me" ? account : url.includes("/users?") ? { users: [person], total: 30 } : url.endsWith("/testers") ? { testers: [{ email: "tester@example.test", enabled: true }] } : { entries: [] } };
  });
  vi.stubGlobal("fetch", fetcher); return fetcher;
}
afterEach(() => { cleanup(); vi.unstubAllGlobals(); });
describe("Owner manager", () => {
  it("hides user data and sends no manager reads for nonowners", async () => {
    const fetcher = setup({ ...owner, manager_enabled: false }); render(<ManagerPage />);
    await screen.findByText(/available only to the configured owner/);
    expect(fetcher.mock.calls.some(([url]) => url.startsWith("/api/manager"))).toBe(false);
    expect(screen.queryByText("alex@example.test")).toBeNull();
  });
  it("shows balances, tester controls and paginated registered users", async () => {
    const fetcher = setup(); render(<ManagerPage />);
    await screen.findByText("alex@example.test");
    expect(screen.getByText("20 available · 10 reserved · 0 held")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Next users" }));
    await waitFor(() => expect(fetcher.mock.calls.some(([url]) => url.includes("offset=25"))).toBe(true));
  });
  it("adds and disables tester invitations using authenticated CSRF requests", async () => {
    const fetcher = setup(); render(<ManagerPage />); await screen.findByText("tester@example.test");
    fireEvent.change(screen.getByLabelText("Google email"), { target: { value: "new@example.test" } });
    fireEvent.click(screen.getByRole("button", { name: "Add tester" }));
    await screen.findByText("Tester invitation enabled.");
    expect(fetcher).toHaveBeenCalledWith("/api/manager/testers", expect.objectContaining({ method: "PUT", headers: expect.objectContaining({ "X-CSRF-Token": "csrf" }), body: JSON.stringify({ email: "new@example.test", enabled: true }) }));
    fireEvent.click(screen.getByRole("button", { name: "Disable top-ups for tester@example.test" }));
    await screen.findByText("Tester access updated.");
    expect(fetcher).toHaveBeenCalledWith("/api/manager/testers", expect.objectContaining({ body: JSON.stringify({ email: "tester@example.test", enabled: false }) }));
  });
  it("retains failed adjustment and retries with the same key without duplicate submissions", async () => {
    let finish!: () => void; const blocked = new Promise<void>(resolve => finish = resolve);
    let writes = 0;
    const fetcher = setup(owner, async () => {
      writes++; if (writes === 1) { await blocked; throw new Error("Network interrupted"); }
      return { ok: true, json: async () => ({ balance_after: 30 }) };
    });
    render(<ManagerPage />); await screen.findByText("alex@example.test");
    fireEvent.click(screen.getByRole("button", { name: "Edit credits for alex@example.test" }));
    expect(document.activeElement).toBe(screen.getByLabelText("Credits"));
    fireEvent.change(screen.getByLabelText("Reason"), { target: { value: "Tester grant" } });
    const form = screen.getByLabelText("Reason").closest("form")!;
    fireEvent.submit(form); fireEvent.submit(form);
    expect(writes).toBe(1);
    finish(); await screen.findByText("Network interrupted");
    expect((screen.getByLabelText("Reason") as HTMLTextAreaElement).value).toBe("Tester grant");
    fireEvent.click(screen.getByRole("button", { name: "Retry credit adjustment" }));
    await screen.findByText("Credit adjustment recorded.");
    const requests = fetcher.mock.calls.filter(([, init]) => init?.method === "POST");
    expect(requests).toHaveLength(2);
    expect(requests[0][1]!.headers).toEqual(requests[1][1]!.headers);
    expect(requests[0][1]!.body).toBe(JSON.stringify({ delta: 10, reason: "Tester grant" }));
  });
  it("returns Google sign-in to the manager screen", async () => {
    setup({ ...owner, authenticated: false }); render(<ManagerPage />);
    expect((await screen.findByRole("link", { name: "Sign in with Google" })).getAttribute("href")).toContain("return_to=%2F%3Fmanager%3D1");
  });
});
