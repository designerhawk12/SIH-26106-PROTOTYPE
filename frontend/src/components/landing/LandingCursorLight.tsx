import { useEffect, useRef } from "react";
import { attachCursorLight } from "./cursor-light";

export function LandingCursorLight() {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!ref.current) return;
    return attachCursorLight(ref.current);
  }, []);
  return <div ref={ref} className="landing-environment-light" aria-hidden="true" />;
}
