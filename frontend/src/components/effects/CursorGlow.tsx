import { motion, useSpring, useTransform } from "framer-motion";
import { useGlobalPointerMotion } from "@/hooks/useGlobalPointerMotion";

const GLOW_RADIUS = 300;

/** One soft, non-interactive atmospheric glow shared with global pointer motion. */
export function CursorGlow() {
  const { clientX, clientY, pointerPresence, reduceMotion } = useGlobalPointerMotion();
  const smoothX = useSpring(clientX, { stiffness: 90, damping: 24, mass: 0.7 });
  const smoothY = useSpring(clientY, { stiffness: 90, damping: 24, mass: 0.7 });
  const opacity = useSpring(pointerPresence, { stiffness: 80, damping: 22, mass: 0.8 });
  const x = useTransform(smoothX, (value) => value - GLOW_RADIUS);
  const y = useTransform(smoothY, (value) => value - GLOW_RADIUS);

  return (
    <motion.div
      aria-hidden
      className="landing-cursor-glow pointer-events-none fixed left-0 top-0 z-0"
      style={{ x, y, opacity: reduceMotion ? 0 : opacity }}
    />
  );
}
