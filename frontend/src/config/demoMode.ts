/**
 * Presentation-only frontend gate.
 *
 * This is deliberately opt-in: every value except the exact string "true"
 * keeps the complete application enabled.
 */
export function resolveDemoMode(value: string | undefined): boolean {
  return value === "true";
}

export const DEMO_MODE = resolveDemoMode(import.meta.env?.VITE_DEMO_MODE);
