/** Root-fragment app screens. Screen addresses are navigation intent, not permission. */
export type AppScreen = "home" | "signin" | "account" | "room";

export interface AppRoute {
  screen: AppScreen;
  invalid: boolean;
}

// A Map avoids inherited object keys (constructor, toString, __proto__) ever
// resolving to a non-screen value.
const SCREENS = new Map<string, AppScreen>([
  ["/", "home"],
  ["/home", "home"],
  ["/signin", "signin"],
  ["/account", "account"],
  ["/room", "room"],
]);

export function resolveAppRoute(search: string, hash: string): AppRoute {
  const params = new URLSearchParams(search);
  // The legacy account link is the OAuth return target; it keeps its destination
  // even if an unrelated fragment is present alongside it.
  if (params.get("account") === "1") return { screen: "account", invalid: false };
  const path = hash.replace(/^#/, "").split("?")[0];
  if (path) {
    const screen = SCREENS.get(path);
    return screen ? { screen, invalid: false } : { screen: "home", invalid: true };
  }
  if (params.get("preview") === "1") return { screen: "room", invalid: false };
  return { screen: "home", invalid: false };
}

/** Canonical URL after consuming the one-time legacy account intent. */
export function accountConsumedHref(search: string, pathname: string): string {
  const params = new URLSearchParams(search);
  params.delete("account");
  const query = params.toString();
  return `${pathname}${query ? `?${query}` : ""}#/account`;
}

/** Keep preview fixtures and other query entries; drop the consumed account link. */
export function appScreenHref(screen: AppScreen, search: string, pathname: string): string {
  const params = new URLSearchParams(search);
  params.delete("account");
  params.delete("signin_error");
  const query = params.toString();
  return `${pathname}${query ? `?${query}` : ""}#/${screen}`;
}
