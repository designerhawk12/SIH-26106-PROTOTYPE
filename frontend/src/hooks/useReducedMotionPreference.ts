import { useReducedMotion } from "framer-motion";

/** A single, SSR-safe motion preference used by custom visual effects. */
export function useReducedMotionPreference() {
  return useReducedMotion() ?? false;
}
