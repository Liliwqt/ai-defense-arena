/** Root-fragment app screens. Screen addresses are navigation intent, not permission. */
export type AppScreen = "home" | "signin" | "account" | "setup" | "prepare" | "room" | "controls" | "results" | "payments-live" | "payments-test" | "manager";

export interface AppRoute {
  screen: AppScreen;
  invalid: boolean;
  freshSetup?: boolean;
}

// A Map avoids inherited object keys (constructor, toString, __proto__) ever
// resolving to a non-screen value.
const SCREENS = new Map<string, AppScreen>([
  ["/", "signin"],
  ["/home", "home"],
  ["/signin", "signin"],
  ["/account", "account"],
  ["/setup", "setup"],
  ["/prepare", "prepare"],
  ["/room", "room"],
  ["/controls", "controls"],
  ["/results", "results"],
]);

export function resolveAppRoute(search: string, hash: string): AppRoute {
  const params = new URLSearchParams(search);
  // Keep the original document-entry precedence when more than one legacy flag exists.
  if (params.get("manager") === "1") return { screen: "manager", invalid: false };
  if (params.get("payments") === "test") return { screen: "payments-test", invalid: false };
  if (params.get("payments") === "live") return { screen: "payments-live", invalid: false };
  // The legacy account link is the OAuth return target; it keeps its destination
  // even if an unrelated fragment is present alongside it.
  if (params.get("account") === "1") return { screen: "account", invalid: false };
  const path = hash.replace(/^#/, "").split("?")[0];
  if (path) {
    const screen = SCREENS.get(path);
    return screen ? { screen, invalid: false, freshSetup: screen === "setup" && new URLSearchParams(hash.split("?")[1]).get("new") === "1" } : { screen: "home", invalid: true };
  }
  if (params.get("preview") === "1") return { screen: params.get("plan") === "1" ? "prepare" : "room", invalid: false };
  return { screen: "signin", invalid: false };
}

/** Canonical URL after consuming the one-time legacy account intent. */
export function accountConsumedHref(search: string, pathname: string): string {
  const params = new URLSearchParams(search);
  params.delete("account");
  const query = params.toString();
  return `${pathname}${query ? `?${query}` : ""}#/account`;
}

/** Keep preview fixtures and other query entries; drop the consumed account link. */
export function appScreenHref(screen: AppScreen, search: string, pathname: string, freshSetup = false): string {
  const params = new URLSearchParams(search);
  params.delete("account");
  params.delete("signin_error");
  params.delete("manager");
  params.delete("payments");
  params.delete("payment_return");
  if (screen === "manager") params.set("manager", "1");
  if (screen === "payments-live" || screen === "payments-test") params.set("payments", screen === "payments-live" ? "live" : "test");
  const query = params.toString();
  return `${pathname}${query ? `?${query}` : ""}#/${screen}${screen === "setup" && freshSetup ? "?new=1" : ""}`;
}

/** Only known app addresses are eligible for same-document navigation. */
export function internalAppHref(href: string): string | null {
  const url = new URL(href, window.location.href);
  if (url.origin !== window.location.origin || url.pathname !== "/") return null;
  const params = url.searchParams;
  if (params.get("manager") === "1" || ["live", "test"].includes(params.get("payments") ?? "") || params.get("account") === "1" ||
      SCREENS.has(url.hash.slice(1))) return `${url.pathname}${url.search}${url.hash}`;
  return !url.search && !url.hash ? "/#/home" : null;
}
