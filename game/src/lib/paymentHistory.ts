export interface TestPurchase {
  id: string;
  provider?: "payment_intent" | "checkout_session";
  simulated?: boolean;
  status: string;
  credits: number;
  awarded_credits?: number;
  amount?: number;
  currency?: string;
}

export interface DefenseRunReceipt {
  id: string;
  mode: "voucher" | "credits";
  cost: number;
  status: "reserved" | "charged" | "released";
  created_at: number;
  charged_at: number | null;
}

export function purchaseLabel(order: TestPurchase): string {
  const qr = order.provider === "payment_intent";
  const labels: Record<string, string> = { creating: qr ? "Generating QR" : "Creating checkout",
    creation_failed: qr ? "QR creation unverified" : "Checkout unverified", pending: "Awaiting payment verification",
    paid: order.simulated ? "Sandbox simulation applied" : "Payment recorded", failed: "Payment failed", expired: "QR expired", cancelled: "Cancelled" };
  const label = labels[order.status] ?? "Unknown purchase status";
  return `${label} · ${order.awarded_credits ?? 0} test credits added`;
}

export function runLabel(run: DefenseRunReceipt): string {
  if (run.mode === "voucher") return "Voucher run · no credits used";
  if (run.status === "released") return "Reservation released · no credits charged";
  return `${run.status === "reserved" ? "Reserved" : "Charged"} · ${run.cost} test credits`;
}

const refundReviewLabels: Record<string,string> = {
  unused_review: "Unused purchase · contact support for refund review",
  used_review: "Previously used credits · contact support for complaint review",
  held: "Credits held during refund review",
  refunded: "Refund processed by provider",
  unavailable: "Refund eligibility needs review",
};
export function refundReviewLabel(state?:string):string {
  return refundReviewLabels[state ?? ""] ?? "";
}
