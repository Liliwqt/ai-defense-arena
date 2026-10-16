import { useCallback, useEffect, useState } from "react";
import { accountConsumedHref, appScreenHref, resolveAppRoute, type AppScreen } from "../lib/appRoute";

export function useAppRoute() {
  const [route, setRoute] = useState(() => resolveAppRoute(window.location.search, window.location.hash));

  useEffect(() => {
    const sync = () => {
      const next = resolveAppRoute(window.location.search, window.location.hash);
      // Consume the one-time legacy account intent so later fragment navigation and
      // Back/Forward behave normally after the OAuth return. Other query entries
      // (preview, signin_error, plan) are preserved.
      if (next.screen === "account" && new URLSearchParams(window.location.search).get("account") === "1") {
        window.history.replaceState(null, "", accountConsumedHref(window.location.search, window.location.pathname));
      }
      setRoute(next);
    };
    window.addEventListener("popstate", sync);
    window.addEventListener("hashchange", sync);
    sync();
    return () => {
      window.removeEventListener("popstate", sync);
      window.removeEventListener("hashchange", sync);
    };
  }, []);

  const navigateHref = useCallback((href: string) => {
    window.history.pushState(null, "", href);
    setRoute(resolveAppRoute(window.location.search, window.location.hash));
  }, []);
  const navigate = useCallback((screen: AppScreen) => {
    navigateHref(appScreenHref(screen, window.location.search, window.location.pathname));
  }, [navigateHref]);

  return { ...route, navigate, navigateHref };
}
