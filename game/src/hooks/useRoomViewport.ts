import { useEffect, useState } from "react";

// A keyboard can shrink the visible viewport without resizing the layout
// viewport. Resize the existing room; never remount its stateful composer.
export function useRoomViewport() {
  const read = () => ({ height: Math.round(window.visualViewport?.height ?? window.innerHeight), width: window.innerWidth });
  const [viewport, setViewport] = useState(read);
  useEffect(() => {
    const update = () => setViewport(read());
    window.addEventListener("resize", update);
    window.visualViewport?.addEventListener("resize", update);
    window.visualViewport?.addEventListener("scroll", update);
    // Catch a resize that happened between initial render and effect setup.
    update();
    return () => {
      window.removeEventListener("resize", update);
      window.visualViewport?.removeEventListener("resize", update);
      window.visualViewport?.removeEventListener("scroll", update);
    };
  }, []);
  return { ...viewport, compact: viewport.width <= 900 && viewport.height < 640 };
}
