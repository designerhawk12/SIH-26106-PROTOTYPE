import { motionValue } from "framer-motion";
import { useEffect } from "react";
import { useReducedMotionPreference } from "@/hooks/useReducedMotionPreference";

const normalizedX = motionValue(0);
const normalizedY = motionValue(0);
const clientX = motionValue(0);
const clientY = motionValue(0);
const pointerPresence = motionValue(0);

let activeConsumers = 0;
let stopTracking: (() => void) | undefined;

function resetPointer() {
  normalizedX.set(0);
  normalizedY.set(0);
  pointerPresence.set(0);
}

function startGlobalTracking() {
  const finePointer = window.matchMedia("(pointer: fine)");
  let frame: number | undefined;
  let latestEvent: PointerEvent | undefined;

  const commitPointer = () => {
    frame = undefined;
    if (!latestEvent || !finePointer.matches) return;
    const width = Math.max(window.innerWidth, 1);
    const height = Math.max(window.innerHeight, 1);
    clientX.set(latestEvent.clientX);
    clientY.set(latestEvent.clientY);
    normalizedX.set(Math.max(-1, Math.min(1, (latestEvent.clientX / width - 0.5) * 2)));
    normalizedY.set(Math.max(-1, Math.min(1, (latestEvent.clientY / height - 0.5) * 2)));
    pointerPresence.set(1);
  };

  const onPointerMove = (event: PointerEvent) => {
    if (!finePointer.matches || event.pointerType === "touch") return;
    latestEvent = event;
    if (frame === undefined) frame = window.requestAnimationFrame(commitPointer);
  };
  const onPointerLeave = () => resetPointer();
  const onPointerCapabilityChange = () => {
    if (!finePointer.matches) resetPointer();
  };

  window.addEventListener("pointermove", onPointerMove, { passive: true });
  window.addEventListener("blur", onPointerLeave);
  document.documentElement.addEventListener("pointerleave", onPointerLeave);
  finePointer.addEventListener("change", onPointerCapabilityChange);

  return () => {
    if (frame !== undefined) window.cancelAnimationFrame(frame);
    window.removeEventListener("pointermove", onPointerMove);
    window.removeEventListener("blur", onPointerLeave);
    document.documentElement.removeEventListener("pointerleave", onPointerLeave);
    finePointer.removeEventListener("change", onPointerCapabilityChange);
    resetPointer();
  };
}

/** Shared viewport-relative pointer motion with one global listener for all consumers. */
export function useGlobalPointerMotion() {
  const reduceMotion = useReducedMotionPreference();

  useEffect(() => {
    if (reduceMotion) {
      resetPointer();
      return;
    }

    activeConsumers += 1;
    if (activeConsumers === 1) stopTracking = startGlobalTracking();
    return () => {
      activeConsumers -= 1;
      if (activeConsumers === 0) {
        stopTracking?.();
        stopTracking = undefined;
      }
    };
  }, [reduceMotion]);

  return {
    clientX,
    clientY,
    normalizedX,
    normalizedY,
    pointerPresence,
    reduceMotion,
  };
}
