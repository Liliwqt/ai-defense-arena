export interface TestPurchase {
  id: string;
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
  const labels: Record<string, string> = { creating: "Creating checkout", creation_failed: "Checkout unverified", pending: "Awaiting payment verification", paid: "Payment recorded" };
  const label = labels[order.status] ?? "Unknown purchase status";
  return `${label} · ${order.awarded_credits ?? 0} test credits added`;
}

export function runLabel(run: DefenseRunReceipt): string {
  if (run.mode === "voucher") return "Voucher run · no credits used";
  if (run.status === "released") return "Reservation released · no credits charged";
  return `${run.status === "reserved" ? "Reserved" : "Charged"} · ${run.cost} test credits`;
}
