/** Root-fragment app screens. Screen addresses are navigation intent, not permission. */
export type AppScreen = "home" | "signin" | "account" | "room";

export interface AppRoute {
  screen: AppScreen;
  invalid: boolean;
}

const SCREENS: Record<string, AppScreen> = {
  "/": "home",
  "/home": "home",
  "/signin": "signin",
  "/account": "account",
  "/room": "room",
};

export function resolveAppRoute(search: string, hash: string): AppRoute {
  const path = hash.replace(/^#/, "").split("?")[0];
  if (path) {
    const screen = SCREENS[path];
    return screen ? { screen, invalid: false } : { screen: "home", invalid: true };
  }
  const params = new URLSearchParams(search);
  if (params.get("preview") === "1") return { screen: "room", invalid: false };
  if (params.get("account") === "1") return { screen: "account", invalid: false };
  return { screen: "home", invalid: false };
}

/** Keep preview fixtures and other query entries; drop the consumed account link. */
export function appScreenHref(screen: AppScreen, search: string, pathname: string): string {
  const params = new URLSearchParams(search);
  params.delete("account");
  params.delete("signin_error");
  const query = params.toString();
  return `${pathname}${query ? `?${query}` : ""}#/${screen}`;
}
