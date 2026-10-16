import { useCallback, useEffect, useState } from "react";
import { appScreenHref, resolveAppRoute, type AppScreen } from "../lib/appRoute";

export function useAppRoute() {
  const [route, setRoute] = useState(() => resolveAppRoute(window.location.search, window.location.hash));

  useEffect(() => {
    const sync = () => setRoute(resolveAppRoute(window.location.search, window.location.hash));
    window.addEventListener("popstate", sync);
    window.addEventListener("hashchange", sync);
    return () => {
      window.removeEventListener("popstate", sync);
      window.removeEventListener("hashchange", sync);
    };
  }, []);

  const navigate = useCallback((screen: AppScreen) => {
    window.history.pushState(null, "", appScreenHref(screen, window.location.search, window.location.pathname));
    setRoute(resolveAppRoute(window.location.search, window.location.hash));
  }, []);

  return { ...route, navigate };
}
