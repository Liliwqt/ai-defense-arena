import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { PaymentTestPage, RECEIPT_KEY, ATTEMPT_KEY } from "./PaymentTestPage";
import { purchaseLabel } from "../lib/paymentHistory";

const topup = { id: "test_fixture", mode: "test", status: "pending", amount: 10000, currency: "PHP", credits: 100,
  qr_image_url: "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAAB", expires_at: 1800001800, created_at: 1800000000, paid_at: null, simulated: false };
const signedIn = { authenticated: true, google_enabled: true, user: { id: "account_alex", name: "Alex", email: "alex@example.test" }, csrf_token: "csrf-fixture", test_credits: 0, orders: [] };
const config = { mode: "test", enabled: true, packages: [{ id: "starter", amount: 10000, currency: "PHP", credits: 100 }] };
const json = (body: unknown, ok = true) => ({ ok, status: ok ? 200 : 400, json: async () => body });
const fetcherFor = (handler: (url: string, init?: RequestInit) => Promise<unknown> = async () => json({topup})) =>
  vi.fn(async (url: string, init?: RequestInit) => url === "/api/auth/me" ? json(signedIn) : url.endsWith("/config") ? json(config) : handler(url, init));
beforeEach(() => { sessionStorage.clear(); history.replaceState(null, "", "/?payments=test"); vi.spyOn(Date, "now").mockReturnValue(1800000000000); });
afterEach(() => { vi.useRealTimers(); vi.restoreAllMocks(); vi.unstubAllGlobals(); });
async function createQR() {
  await screen.findByRole("button", {name: "Generate test QR"});
  await waitFor(() => expect(screen.getByRole("button", {name: "Generate test QR"})).not.toBeDisabled());
  fireEvent.click(screen.getByRole("button", {name: "Generate test QR"}));
}

describe("QR-first sandbox top-up", () => {
  it("creates a QR using only a server package id, session CSRF and a retained request key", async () => {
    const fetcher = fetcherFor(); vi.stubGlobal("fetch", fetcher);
    render(<PaymentTestPage />); await createQR();
    expect((await screen.findByRole("img", {name: "Sandbox QR Ph code"})).getAttribute("src")).toBe(topup.qr_image_url);
    expect(screen.getByText("30:00", {selector: "time"})).toBeTruthy();
    const creation = fetcher.mock.calls.find(([url]) => url === "/api/payments/test/topups")!;
    expect(JSON.parse(creation[1]!.body as string)).toEqual({package_id: "starter"});
    expect(creation[1]!.headers).toMatchObject({"X-CSRF-Token": signedIn.csrf_token, "Idempotency-Key": sessionStorage.getItem(ATTEMPT_KEY)});
    expect(sessionStorage.getItem(RECEIPT_KEY)).toBe(JSON.stringify({id: topup.id, account_id: signedIn.user.id}));
    expect(screen.queryByRole("link", {name: "Open test checkout"})).toBeNull();
    expect(fetcher.mock.calls.some(([url]) => url.endsWith("/checkout"))).toBe(false);
  });
  it("regenerates a cancelled QR with a new request key while retaining the old receipt in history", async () => {
    let creations = 0;
    const fetcher = fetcherFor(async (url, init) => json({topup: url.endsWith("/topups") && init?.method === "POST"
      ? {...topup, id: ++creations === 1 ? topup.id : "test_second"} : {...topup, id: creations === 1 ? topup.id : "test_second"}}));
    vi.stubGlobal("fetch", fetcher); render(<PaymentTestPage />); await createQR();
    await screen.findByRole("img", {name: "Sandbox QR Ph code"});
    const firstKey = sessionStorage.getItem(ATTEMPT_KEY);
    fireEvent.click(screen.getByRole("button", {name: "Cancel top-up"}));
    expect(screen.getByText("Top-up cancelled on this device.")).toBeTruthy();
    expect(screen.queryByRole("img", {name: "Sandbox QR Ph code"})).toBeNull();
    expect(screen.getByText(/not cancelled at PayMongo/)).toBeTruthy();
    fireEvent.click(screen.getByRole("button", {name: "Regenerate test QR"}));
    await screen.findByText("Test top-up: test_second");
    expect(sessionStorage.getItem(ATTEMPT_KEY)).not.toBe(firstKey);
    expect(fetcher.mock.calls.filter(([url, init]) => url === "/api/payments/test/topups" && init?.method === "POST")).toHaveLength(2);
  });

  it("labels QR lifecycle and simulated credit awards in purchase history", () => {
    const base = {id: "qr", provider: "payment_intent" as const, credits: 100};
    expect(purchaseLabel({...base, status: "creating"})).toBe("Generating QR · 0 test credits added");
    expect(purchaseLabel({...base, status: "creation_failed"})).toBe("QR creation unverified · 0 test credits added");
    expect(purchaseLabel({...base, status: "pending"})).toBe("Awaiting payment verification · 0 test credits added");
    expect(purchaseLabel({...base, status: "failed"})).toBe("Payment failed · 0 test credits added");
    expect(purchaseLabel({...base, status: "expired"})).toBe("QR expired · 0 test credits added");
    expect(purchaseLabel({...base, status: "cancelled"})).toBe("Cancelled · 0 test credits added");
    expect(purchaseLabel({...base, status: "paid", simulated: true, awarded_credits: 100})).toBe("Sandbox simulation applied · 100 test credits added");
    expect(purchaseLabel({id: "old", credits: 100, status: "creating"})).toBe("Creating checkout · 0 test credits added");
  });

  it("counts down from server expiry, hides expired QR and never posts expiry as a payment", async () => {
    vi.useFakeTimers({toFake: ["setInterval", "clearInterval"]});
    const fetcher = fetcherFor(); vi.stubGlobal("fetch", fetcher); render(<PaymentTestPage />); await createQR();
    await screen.findByRole("img", {name: "Sandbox QR Ph code"});
    vi.mocked(Date.now).mockReturnValue(1800001799000);
    await act(async () => { await vi.advanceTimersByTimeAsync(1000); });
    expect(screen.getByText("00:01", {selector: "time"})).toBeTruthy();
    vi.mocked(Date.now).mockReturnValue(1800001800000);
    await act(async () => { await vi.advanceTimersByTimeAsync(1000); });
    expect(screen.getByText("Test QR expired.")).toBeTruthy();
    expect(screen.queryByRole("img")).toBeNull();
    expect(screen.queryByRole("button", {name: "Simulate paid top-up"})).toBeNull();
    expect(screen.getByText("0", {selector: ".payment-balance b"})).toBeTruthy();
    expect(fetcher.mock.calls.filter(([, init]) => init?.method === "POST")).toHaveLength(1);
  });

  it("restores owned receipts and refreshes paid balance and history automatically on WebView resume", async () => {
    sessionStorage.setItem(RECEIPT_KEY, JSON.stringify({id: topup.id, account_id: signedIn.user.id}));
    let paid = false;
    vi.stubGlobal("fetch", vi.fn(async (url: string, _init?: RequestInit) => url === "/api/auth/me" ? json({...signedIn, test_credits: paid ? 100 : 0,
      orders: paid ? [{id: topup.id, provider: "payment_intent", status: "paid", credits: 100, awarded_credits: 100}] : []})
      : url.endsWith("/config") ? json(config) : json({topup: {...topup, status: paid ? "paid" : "pending"}})));
    render(<PaymentTestPage />); await screen.findByRole("img", {name: "Sandbox QR Ph code"});
    paid = true; await act(async () => { fireEvent(window, new Event("defense-native-resume")); });
    await screen.findByText("Test payment confirmed.");
    expect(await screen.findByText("100", {selector: ".payment-balance b"})).toBeTruthy();
    expect(screen.getByText("Payment recorded · 100 test credits added")).toBeTruthy();
    expect(screen.queryByRole("img")).toBeNull();
  });

  it("polls for verified payment without requiring a redirect or manual reload", async () => {
    sessionStorage.setItem(RECEIPT_KEY, JSON.stringify({id: topup.id, account_id: signedIn.user.id}));
    let paid = false;
    vi.stubGlobal("fetch", vi.fn(async (url: string, _init?: RequestInit) => url === "/api/auth/me" ? json({...signedIn, test_credits: paid ? 100 : 0})
      : url.endsWith("/config") ? json(config) : json({topup: {...topup, status: paid ? "paid" : "pending"}})));
    vi.useFakeTimers({toFake: ["setInterval", "clearInterval"]});
    render(<PaymentTestPage />); await screen.findByRole("img"); paid = true;
    await act(async () => { await vi.advanceTimersByTimeAsync(5000); });
    expect(screen.getByText("Test payment confirmed.")).toBeTruthy();
    expect(screen.getByText("100", {selector: ".payment-balance b"})).toBeTruthy();
  });

  it("simulates with CSRF, distinguishes fixture evidence and refreshes the account", async () => {
    let paid = false; let release!: () => void;
    const pending = new Promise<void>(resolve => {release = resolve;});
    const fetcher = vi.fn(async (url: string, _init?: RequestInit) => url === "/api/auth/me"
      ? json({...signedIn, test_credits: paid ? 100 : 0}) : url.endsWith("/config") ? json(config)
      : url.endsWith("/simulate") ? (await pending, paid = true, json({topup: {...topup, status: "paid", simulated: true}})) : json({topup: {...topup, status: paid ? "paid" : "pending", simulated: paid}}));
    vi.stubGlobal("fetch", fetcher); render(<PaymentTestPage />); await createQR(); await screen.findByRole("img");
    fireEvent.click(screen.getByRole("button", {name: "Simulate paid top-up"}));
    expect(screen.getByRole("button", {name: "Simulate paid top-up"})).toBeDisabled();
    fireEvent.click(screen.getByRole("button", {name: "Simulate paid top-up"}));
    await act(async () => { release(); });
    await screen.findByText("Sandbox simulation applied.");
    expect(screen.getByText(/No provider payment was processed/)).toBeTruthy();
    expect(screen.getByText("100", {selector: ".payment-balance b"})).toBeTruthy();
    const simulations = fetcher.mock.calls.filter(([url]) => url.endsWith("/simulate"));
    expect(simulations).toHaveLength(1);
    expect(simulations[0][1]).toEqual({method: "POST", headers: {"Content-Type": "application/json", "X-CSRF-Token": signedIn.csrf_token}, body: "{}"});
  });

  it("retains the QR and enables retry when sandbox simulation fails", async () => {
    vi.stubGlobal("fetch", fetcherFor(async url => url.endsWith("/simulate") ? json({detail: "Test mode is disabled."}, false) : json({topup})));
    render(<PaymentTestPage />); await createQR(); await screen.findByRole("img");
    fireEvent.click(screen.getByRole("button", {name: "Simulate paid top-up"}));
    await screen.findByText("Test mode is disabled.");
    expect(screen.getByRole("img")).toBeTruthy();
    expect(screen.getByRole("button", {name: "Simulate paid top-up"})).not.toBeDisabled();
    expect(screen.queryByText("Sandbox simulation applied.")).toBeNull();
  });

  it.each(["failed", "expired", "creation_failed"])("shows %s without inventing an award and permits regeneration", async status => {
    sessionStorage.setItem(RECEIPT_KEY, JSON.stringify({id: topup.id, account_id: signedIn.user.id}));
    vi.stubGlobal("fetch", fetcherFor(async () => json({topup: {...topup, status}})));
    render(<PaymentTestPage />);
    await screen.findByRole("button", {name: "Regenerate test QR"});
    expect(screen.queryByRole("img")).toBeNull();
    expect(screen.getByText("0", {selector: ".payment-balance b"})).toBeTruthy();
    expect(screen.queryByRole("button", {name: "Simulate paid top-up"})).toBeNull();
  });

  it("keeps cancelled receipts hidden across reload while monitoring a late verified payment", async () => {
    sessionStorage.setItem(RECEIPT_KEY, JSON.stringify({id: topup.id, account_id: signedIn.user.id, hidden: true}));
    let paid = false;
    vi.stubGlobal("fetch", fetcherFor(async () => json({topup: {...topup, status: paid ? "paid" : "pending"}})));
    render(<PaymentTestPage />); await screen.findByText("Top-up cancelled on this device.");
    expect(screen.queryByRole("img")).toBeNull();
    paid = true; await act(async () => { fireEvent(window, new Event("defense-native-resume")); });
    await screen.findByText("Test payment confirmed.");
  });

  it("shows generating state and blocks repeated creation while awaiting a response", async () => {
    let release!: () => void; const pending = new Promise<void>(resolve => {release = resolve;});
    const fetcher = fetcherFor(async () => {await pending; return json({topup});});
    vi.stubGlobal("fetch", fetcher); render(<PaymentTestPage />); await createQR();
    expect(screen.getByRole("button", {name: "Generating test QR…"})).toBeDisabled();
    fireEvent.submit(screen.getByLabelText("Test-credit package").closest("form")!);
    expect(fetcher.mock.calls.filter(([url]) => url.endsWith("/topups"))).toHaveLength(1);
    await act(async () => {release();}); await screen.findByRole("img");
  });

  it("retains and reuses a request id after a lost creation response", async () => {
    let requests = 0;
    const fetcher = fetcherFor(async url => url.endsWith("/topups") && ++requests === 1
      ? Promise.reject(new Error("Response lost")) : json({topup}));
    vi.stubGlobal("fetch", fetcher); render(<PaymentTestPage />); await createQR();
    await screen.findByText("Response lost"); const id = sessionStorage.getItem(ATTEMPT_KEY);
    expect(screen.getByLabelText("Test-credit package")).toBeDisabled();
    await createQR(); await screen.findByRole("img");
    for (const [, init] of fetcher.mock.calls.filter(([url]) => url.endsWith("/topups")))
      expect(init!.headers).toMatchObject({"Idempotency-Key": id});
  });

  it("retains an owned receipt and reports a polling error without confirming payment", async () => {
    const saved = JSON.stringify({id: topup.id, account_id: signedIn.user.id}); sessionStorage.setItem(RECEIPT_KEY, saved);
    vi.stubGlobal("fetch", fetcherFor(async () => Promise.reject(new Error("Offline"))));
    render(<PaymentTestPage />); await screen.findByRole("alert");
    expect(sessionStorage.getItem(RECEIPT_KEY)).toBe(saved);
    expect(screen.queryByText("Test payment confirmed.")).toBeNull();
  });

  it.each([false, true])("requires sign-in and handles google_enabled=%s", async google_enabled => {
    const fetcher = vi.fn(async (url: string, _init?: RequestInit) => url === "/api/auth/me" ? json({authenticated: false, google_enabled}) : json(config));
    vi.stubGlobal("fetch", fetcher); render(<PaymentTestPage />);
    await screen.findByText("Sign in to own your test credits");
    expect(screen.getByRole("button", {name: "Generate test QR"})).toBeDisabled();
    if (google_enabled) expect(screen.getByRole("link", {name: "Sign in with Google"}).getAttribute("href")).toBe("/api/auth/google/login?return_to=%2F%3Fpayments%3Dtest");
    else expect(screen.getByText(/Google sign-in needs server configuration/)).toBeTruthy();
    expect(fetcher.mock.calls.some(([url]) => url.includes("/topups/"))).toBe(false);
  });

  it("disables unconfigured payments and preserves the test QR warning", async () => {
    vi.stubGlobal("fetch", vi.fn(async (url: string, _init?: RequestInit) => url === "/api/auth/me" ? json(signedIn) : json({...config, enabled: false})));
    render(<PaymentTestPage />); await screen.findByText("Test top-up is not configured yet.");
    expect(screen.getByRole("button", {name: "Generate test QR"})).toBeDisabled();
    expect(screen.getByText(/Do not scan or pay the QR code with a real bank or wallet app/)).toBeTruthy();
  });

  it.each([{mode: "live"}, {qr_image_url: "https://evil.example/qr.png"}, {qr_image_url: "data:image/svg+xml;base64,AAAA"}, {amount: 1}, {status: "unknown"}, {expires_at: "soon"}])("rejects invalid top-up evidence %j", async patch => {
    vi.stubGlobal("fetch", fetcherFor(async () => json({topup: {...topup, ...patch}})));
    render(<PaymentTestPage />); await createQR(); await screen.findByRole("alert");
    expect(screen.queryByRole("img")).toBeNull();
    expect(sessionStorage.getItem(RECEIPT_KEY)).toBeNull();
  });

  it("does not mistake a redirect or legacy checkout receipt for QR payment", async () => {
    history.replaceState(null, "", "/?payments=test&payment_return=success");
    sessionStorage.setItem("arena-test-payment", JSON.stringify({id: "old", token: "legacy-fixture"}));
    const fetcher = fetcherFor(); vi.stubGlobal("fetch", fetcher); render(<PaymentTestPage />);
    await screen.findByText(/A checkout redirect does not confirm payment/);
    expect(screen.queryByText("Test payment confirmed.")).toBeNull();
    expect(fetcher.mock.calls.some(([url]) => url.includes("/orders/"))).toBe(false);
    expect(sessionStorage.getItem("arena-test-payment")).toContain("old");
  });

  it("does not poll or show another account’s saved QR", async () => {
    sessionStorage.setItem(RECEIPT_KEY, JSON.stringify({id: topup.id, account_id: "another-account"}));
    const fetcher = fetcherFor(); vi.stubGlobal("fetch", fetcher); render(<PaymentTestPage />);
    await screen.findByText(/Sign in to the account that created this top-up/);
    expect(fetcher.mock.calls.some(([url]) => url.includes("/topups/"))).toBe(false);
    expect(screen.queryByRole("img")).toBeNull();
  });

  it("opens an existing QR from server-owned account history without creating one", async () => {
    const fetcher = vi.fn(async (url: string, _init?: RequestInit) => url === "/api/auth/me" ? json({...signedIn,
      orders: [{id: topup.id, provider: "payment_intent", status: "pending", credits: 100}]})
      : url.endsWith("/config") ? json(config) : json({topup}));
    vi.stubGlobal("fetch", fetcher); render(<PaymentTestPage />);
    fireEvent.click(await screen.findByRole("button", {name: "View top-up test_fixture"}));
    await screen.findByRole("img");
    expect(fetcher.mock.calls.some(([url]) => url === "/api/payments/test/topups")).toBe(false);
  });

  it("signs out with CSRF and clears the current QR and retry key", async () => {
    const fetcher = fetcherFor(async url => url.endsWith("/logout") ? json({authenticated: false}) : json({topup}));
    vi.stubGlobal("fetch", fetcher); render(<PaymentTestPage />); await createQR(); await screen.findByRole("img");
    fireEvent.click(screen.getByRole("button", {name: "Sign out"}));
    await screen.findByRole("link", {name: "Sign in with Google"});
    expect(screen.queryByRole("img")).toBeNull(); expect(sessionStorage.getItem(RECEIPT_KEY)).toBeNull();
    expect(sessionStorage.getItem(ATTEMPT_KEY)).toBeNull();
    expect(fetcher.mock.calls.find(([url]) => url.endsWith("/logout"))![1]).toEqual({method: "POST", headers: {"X-CSRF-Token": signedIn.csrf_token}});
  });

  it("retains the QR if sign-out fails", async () => {
    vi.stubGlobal("fetch", fetcherFor(async url => url.endsWith("/logout") ? json({detail: "Expired CSRF"}, false) : json({topup})));
    render(<PaymentTestPage />); await createQR(); await screen.findByRole("img");
    fireEvent.click(screen.getByRole("button", {name: "Sign out"}));
    await screen.findByText("Could not sign out. Please try again.");
    expect(screen.getByRole("img")).toBeTruthy(); expect(sessionStorage.getItem(RECEIPT_KEY)).toContain(topup.id);
  });

  it("ignores an outstanding status read after sign-out", async () => {
    sessionStorage.setItem(RECEIPT_KEY, JSON.stringify({id: topup.id, account_id: signedIn.user.id}));
    let release!: () => void; const pending = new Promise<void>(resolve => {release = resolve;});
    vi.stubGlobal("fetch", fetcherFor(async url => url.endsWith("/logout") ? json({authenticated: false})
      : (await pending, json({topup: {...topup, status: "paid"}}))));
    render(<PaymentTestPage />); await screen.findByText("Loading your saved test top-up…");
    fireEvent.click(screen.getByRole("button", {name: "Sign out"})); await screen.findByRole("link", {name: "Sign in with Google"});
    await act(async () => {release();});
    expect(screen.queryByText("Test payment confirmed.")).toBeNull();
    expect(sessionStorage.getItem(RECEIPT_KEY)).toBeNull();
  });

  it("does not let an account refresh in flight restore a signed-out account", async () => {
    let reads = 0; let release!: () => void; const pending = new Promise<void>(resolve => {release = resolve;});
    const fetcher = vi.fn(async (url: string, _init?: RequestInit) => url === "/api/auth/me" ? (++reads === 1 ? json(signedIn) : (await pending, json(signedIn)))
      : url.endsWith("/config") ? json(config) : json({authenticated: false}));
    vi.stubGlobal("fetch", fetcher); render(<PaymentTestPage />); await screen.findByRole("button", {name: "Sign out"});
    fireEvent.click(screen.getByRole("button", {name: "Sign out"}));
    fireEvent(window, new Event("defense-native-resume"));
    await screen.findByRole("link", {name: "Sign in with Google"});
    await act(async () => {release();});
    expect(screen.getByRole("link", {name: "Sign in with Google"})).toBeTruthy();
    expect(screen.queryByRole("button", {name: "Sign out"})).toBeNull();
  });

  it("keeps a confirmed receipt and explains when automatic balance refresh fails", async () => {
    sessionStorage.setItem(RECEIPT_KEY, JSON.stringify({id: topup.id, account_id: signedIn.user.id}));
    let reads = 0;
    vi.stubGlobal("fetch", vi.fn(async (url: string, _init?: RequestInit) => url === "/api/auth/me" ? (++reads === 1 ? json(signedIn) : Promise.reject(new Error("Offline")))
      : url.endsWith("/config") ? json(config) : json({topup: {...topup, status: "paid"}})));
    render(<PaymentTestPage />); await screen.findByText("Test payment confirmed.");
    await screen.findByText("Payment is recorded, but the balance could not refresh. Try Refresh balance.");
    expect(sessionStorage.getItem(RECEIPT_KEY)).toContain(topup.id);
  });

  it("generates a QR immediately when the host explicitly chooses a package", async () => {
    const fetcher = fetcherFor(); vi.stubGlobal("fetch", fetcher); render(<PaymentTestPage />);
    await screen.findByText("Test top-up is configured.");
    expect(screen.getByLabelText("Test-credit package")).toHaveValue("");
    fireEvent.change(screen.getByLabelText("Test-credit package"), {target: {value: "starter"}});
    await screen.findByRole("img", {name: "Sandbox QR Ph code"});
    expect(JSON.parse(fetcher.mock.calls.find(([url]) => url.endsWith("/topups"))![1]!.body as string)).toEqual({package_id: "starter"});
  });

  it("replaces simulated evidence with later server-verified provider evidence on resume", async () => {
    sessionStorage.setItem(RECEIPT_KEY, JSON.stringify({id: topup.id, account_id: signedIn.user.id}));
    let simulated = true;
    vi.stubGlobal("fetch", fetcherFor(async () => json({topup: {...topup, status: "paid", simulated}})));
    render(<PaymentTestPage />); await screen.findByText("Sandbox simulation applied.");
    simulated = false;
    await act(async () => { fireEvent(window, new Event("defense-native-resume")); });
    await screen.findByText("Test payment confirmed.");
    expect(screen.queryByText("Sandbox simulation applied.")).toBeNull();
    expect(screen.getByText(/The server verified the payment notification/)).toBeTruthy();
  });

});
