import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { PaymentTestPage, RECEIPT_KEY, ATTEMPT_KEY } from "./PaymentTestPage";

const order = { id: "test_fixture", mode: "test", status: "pending", amount: 10000, currency: "PHP", credits: 100, checkout_url: "https://checkout.paymongo.com/offline" };
const signedIn = { authenticated: true, google_enabled: true, user: { id: "account_alex", name: "Alex", email: "alex@example.test" }, csrf_token: "csrf-fixture", test_credits: 0, orders: [] };
const json = (body: unknown, ok = true) => ({ ok, json: async () => body });

beforeEach(() => { sessionStorage.clear(); history.replaceState(null, "", "/?payments=test"); });
afterEach(() => { vi.unstubAllGlobals(); });

describe("PaymentTestPage", () => {
  it("labels simulated payments and disables unconfigured checkout", async () => {
    vi.stubGlobal("fetch", vi.fn(async (url: string) => url.endsWith("/api/auth/me") ? json(signedIn) : json({ mode: "test", enabled: false })));
    render(<PaymentTestPage />);
    expect(screen.getByText("TEST MODE · SANDBOX CHECKOUT")).toBeTruthy();
    expect(screen.getByText(/Do not scan or pay the QR code with a real bank or wallet app/)).toBeTruthy();
    expect(screen.queryByText(/NO REAL MONEY/)).toBeNull();
    await screen.findByText("Test checkout is not configured yet.");
    expect((screen.getByRole("button", { name: "Create test checkout" }) as HTMLButtonElement).disabled).toBe(true);
  });

  it("creates a test checkout without persisting passcode or choosing amount", async () => {
    const fetcher = vi.fn(async (url: string) => url.endsWith("/api/auth/me") ? json(signedIn) : url.endsWith("config") ? json({ mode: "test", enabled: true }) : url.endsWith("checkout") ? json({ order, order_token: "fixture-token" }) : json({ order }));
    vi.stubGlobal("fetch", fetcher);
    render(<PaymentTestPage />);
    await screen.findByText("Test checkout is configured.");
    fireEvent.click(screen.getByRole("button", { name: "Create test checkout" }));
    const link = await screen.findByRole("link", { name: "Open test checkout" });
    expect(link.getAttribute("href")).toBe(order.checkout_url);
    expect(sessionStorage.getItem(RECEIPT_KEY)).toBe(JSON.stringify({ id: order.id }));
    expect(sessionStorage.getItem(RECEIPT_KEY)).not.toContain("private-passcode");
    const calls = fetcher.mock.calls as unknown as [string, RequestInit][];
    const creation = calls.find(([url]) => url.endsWith("checkout"))!;
    expect(JSON.parse(creation[1].body as string)).toEqual({});
    expect(creation[1].headers).toEqual({ "Content-Type": "application/json", "X-CSRF-Token": signedIn.csrf_token, "Idempotency-Key": sessionStorage.getItem(ATTEMPT_KEY) });
  });

  it("does not trust a successful checkout redirect as payment", async () => {
    history.replaceState(null, "", "/?payments=test&payment_return=success");
    sessionStorage.setItem(RECEIPT_KEY, JSON.stringify({ id: order.id, token: "fixture-token" }));
    vi.stubGlobal("fetch", vi.fn(async (url: string) => url.endsWith("/api/auth/me") ? json(signedIn) : url.endsWith("config") ? json({ mode: "test", enabled: true }) : json({ order })));
    render(<PaymentTestPage />);
    await screen.findByRole("link", { name: "Open test checkout" });
    expect(screen.queryByText("Test payment confirmed.")).toBeNull();
    expect(screen.getByText(/payment still needs server verification/i)).toBeTruthy();
  });

  it("restores a receipt using its bearer token and shows verified paid state", async () => {
    sessionStorage.setItem(RECEIPT_KEY, JSON.stringify({ id: order.id, token: "fixture-token" }));
    const fetcher = vi.fn(async (url: string) => url.endsWith("/api/auth/me") ? json(signedIn) : url.endsWith("config") ? json({ mode: "test", enabled: true }) : json({ order: { ...order, status: "paid" } }));
    vi.stubGlobal("fetch", fetcher);
    render(<PaymentTestPage />);
    await screen.findByText("Test payment confirmed.");
    const calls = fetcher.mock.calls as unknown as [string, RequestInit][];
    expect(calls.find(([url]) => url.includes("/orders/"))![1].headers).toEqual({ Authorization: "Bearer fixture-token" });
    expect(screen.queryByRole("link", { name: "Open test checkout" })).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Start another test" }));
    expect(sessionStorage.getItem(RECEIPT_KEY)).toBeNull();
  });

  it("shows safe failure and lets creation be retried", async () => {
    vi.stubGlobal("fetch", vi.fn(async (url: string) => url.endsWith("/api/auth/me") ? json(signedIn) : url.endsWith("config") ? json({ mode: "test", enabled: true }) : json({ detail: "Could not create test checkout." }, false)));
    render(<PaymentTestPage />);
    await screen.findByText("Test checkout is configured.");
    fireEvent.click(screen.getByRole("button", { name: "Create test checkout" }));
    expect(await screen.findByRole("alert")).toHaveProperty("textContent", "Could not create test checkout.");
    expect(sessionStorage.getItem(RECEIPT_KEY)).toBeNull();
    await waitFor(() => expect((screen.getByRole("button", { name: "Create test checkout" }) as HTMLButtonElement).disabled).toBe(false));
  });

  it("retains saved receipt when checking status fails", async () => {
    const receipt = JSON.stringify({ id: order.id, token: "fixture-token" });
    sessionStorage.setItem(RECEIPT_KEY, receipt);
    vi.stubGlobal("fetch", vi.fn(async (url: string) => url.endsWith("/api/auth/me") ? json(signedIn) : url.endsWith("config") ? json({ mode: "test", enabled: true }) : Promise.reject(new Error("Connection lost"))));
    render(<PaymentTestPage />);
    await screen.findByRole("alert");
    expect(sessionStorage.getItem(RECEIPT_KEY)).toBe(receipt);
    expect(screen.queryByText("Test payment confirmed.")).toBeNull();
  });

  it("refuses a live or malicious checkout response", async () => {
    vi.stubGlobal("fetch", vi.fn(async (url: string) => url.endsWith("/api/auth/me") ? json(signedIn) : url.endsWith("config") ? json({ mode: "test", enabled: true }) : json({ order: { ...order, mode: "live", checkout_url: "https://evil.example" }, order_token: "fixture-token" })));
    render(<PaymentTestPage />);
    await screen.findByText("Test checkout is configured.");
    fireEvent.click(screen.getByRole("button", { name: "Create test checkout" }));
    await screen.findByRole("alert");
    expect(screen.queryByRole("link", { name: "Open test checkout" })).toBeNull();
    expect(sessionStorage.getItem(RECEIPT_KEY)).toBeNull();
  });

  it("offers Google sign-in and prevents anonymous purchases", async () => {
    vi.stubGlobal("fetch", vi.fn(async (url: string) => url.endsWith("/api/auth/me")
      ? json({ authenticated: false, google_enabled: true }) : json({ mode: "test", enabled: true })));
    render(<PaymentTestPage />);
    expect((await screen.findByRole("link", { name: "Sign in with Google" })).getAttribute("href")).toBe("/api/auth/google/login?return_to=%2F%3Fpayments%3Dtest");
    expect((screen.getByRole("button", { name: "Create test checkout" }) as HTMLButtonElement).disabled).toBe(true);
    expect(screen.queryByRole("button", { name: "Refresh balance" })).toBeNull();
  });

  it("explains missing Google configuration without offering a broken login", async () => {
    vi.stubGlobal("fetch", vi.fn(async (url: string) => url.endsWith("/api/auth/me")
      ? json({ authenticated: false, google_enabled: false }) : json({ mode: "test", enabled: true })));
    render(<PaymentTestPage />);
    await screen.findByText(/Google sign-in needs server configuration/);
    expect(screen.queryByRole("link", { name: "Sign in with Google" })).toBeNull();
    expect((screen.getByRole("button", { name: "Create test checkout" }) as HTMLButtonElement).disabled).toBe(true);
  });

  it("refreshes balance and purchase history from the account endpoint", async () => {
    let credits = 0;
    vi.stubGlobal("fetch", vi.fn(async (url: string) => url.endsWith("/api/auth/me")
      ? json({ ...signedIn, test_credits: credits, orders: credits ? [{ id: "owned-order", status: "paid", credits, awarded_credits:credits }] : [] })
      : json({ mode: "test", enabled: true })));
    render(<PaymentTestPage />);
    await screen.findByText("No account purchases yet.");
    credits = 100;
    fireEvent.click(screen.getByRole("button", { name: "Refresh balance" }));
    await screen.findByText("owned-order");
    expect(screen.getByText("Payment recorded · 100 test credits added")).toBeTruthy();
    expect(screen.getByText("100", { selector: ".payment-balance b" })).toBeTruthy();
  });

  it("signs out with CSRF protection and clears the local receipt", async () => {
    sessionStorage.setItem(RECEIPT_KEY, JSON.stringify({ id: order.id, token: "fixture-token" }));
    const fetcher = vi.fn(async (url: string) => url.endsWith("/api/auth/me") ? json(signedIn)
      : url.endsWith("logout") ? json({ authenticated: false })
      : url.endsWith("config") ? json({ mode: "test", enabled: true }) : json({ order }));
    vi.stubGlobal("fetch", fetcher);
    render(<PaymentTestPage />);
    fireEvent.click(await screen.findByRole("button", { name: "Sign out" }));
    await screen.findByRole("link", { name: "Sign in with Google" });
    expect(sessionStorage.getItem(RECEIPT_KEY)).toBeNull();
    expect(screen.queryByRole("link", { name: "Open test checkout" })).toBeNull();
    const calls = fetcher.mock.calls as unknown as [string, RequestInit][];
    expect(calls.find(([url]) => url.endsWith("logout"))![1]).toEqual({ method: "POST", headers: { "X-CSRF-Token": signedIn.csrf_token } });
  });

  it("retains the account and receipt if logout fails", async () => {
    const receipt = JSON.stringify({ id: order.id, token: "fixture-token" });
    sessionStorage.setItem(RECEIPT_KEY, receipt);
    vi.stubGlobal("fetch", vi.fn(async (url: string) => url.endsWith("/api/auth/me") ? json(signedIn)
      : url.endsWith("logout") ? json({ detail: "Expired CSRF" }, false)
      : url.endsWith("config") ? json({ mode: "test", enabled: true }) : json({ order })));
    render(<PaymentTestPage />);
    fireEvent.click(await screen.findByRole("button", { name: "Sign out" }));
    await screen.findByText("Could not sign out. Please try again.");
    expect(sessionStorage.getItem(RECEIPT_KEY)).toBe(receipt);
    expect(screen.getByRole("button", { name: "Sign out" })).toBeTruthy();
  });

  it("labels earlier anonymous receipts without awarding account credits", async () => {
    sessionStorage.setItem(RECEIPT_KEY, JSON.stringify({ id: order.id, token: "fixture-token" }));
    vi.stubGlobal("fetch", vi.fn(async (url: string) => url.endsWith("/api/auth/me") ? json(signedIn)
      : url.endsWith("config") ? json({ mode: "test", enabled: true }) : json({ order: { ...order, status: "paid", credits: 0 } })));
    render(<PaymentTestPage />);
    await screen.findByText(/This earlier anonymous test receipt has no account credits/);
    expect(screen.getByText("0", { selector: ".payment-balance b" })).toBeTruthy();
  });

  it("stores only the order ID and checks a new receipt through the account session", async () => {
    sessionStorage.setItem(RECEIPT_KEY, JSON.stringify({ id: order.id }));
    const fetcher = vi.fn(async (url: string) => url.endsWith("/api/auth/me") ? json(signedIn) : url.endsWith("config") ? json({mode:"test",enabled:true}) : json({order}));
    vi.stubGlobal("fetch", fetcher);
    render(<PaymentTestPage />);
    await screen.findByRole("link", {name:"Open test checkout"});
    const calls = fetcher.mock.calls as unknown as [string, RequestInit][];
    expect(calls.find(([url]) => url.includes("/orders/"))![1]).toEqual({cache:"no-store"});
  });

  it("retains a request ID after a lost response and reuses it on retry", async () => {
    let attempts = 0;
    const fetcher = vi.fn(async (url: string) => url.endsWith("/api/auth/me") ? json(signedIn)
      : url.endsWith("config") ? json({mode:"test",enabled:true})
      : url.endsWith("checkout") && ++attempts === 1 ? Promise.reject(new Error("Response lost")) : json({order}));
    vi.stubGlobal("fetch", fetcher);
    render(<PaymentTestPage />);
    await screen.findByText("Test checkout is configured.");
    fireEvent.click(screen.getByRole("button", {name:"Create test checkout"}));
    await screen.findByText("Response lost");
    const requestId = sessionStorage.getItem(ATTEMPT_KEY);
    fireEvent.click(screen.getByRole("button", {name:"Create test checkout"}));
    await screen.findByRole("link", {name:"Open test checkout"});
    const calls = fetcher.mock.calls as unknown as [string, RequestInit][];
    for (const [,init] of calls.filter(([url]) => url.endsWith("checkout")))
      expect(init.headers).toMatchObject({"Idempotency-Key":requestId});
    expect(sessionStorage.getItem(RECEIPT_KEY)).not.toContain("token");
  });

  it("does not poll an account receipt while signed out", async () => {
    sessionStorage.setItem(RECEIPT_KEY, JSON.stringify({ id: order.id }));
    const fetcher = vi.fn(async (url: string) => url.endsWith("/api/auth/me") ? json({authenticated:false,google_enabled:true}) : json({mode:"test",enabled:true}));
    vi.stubGlobal("fetch", fetcher);
    render(<PaymentTestPage />);
    await screen.findByText("Sign in to check your saved purchase.");
    expect(fetcher.mock.calls.some(([url]) => url.includes("/orders/"))).toBe(false);
  });
});
