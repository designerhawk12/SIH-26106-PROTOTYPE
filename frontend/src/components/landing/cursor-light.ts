/** Passive viewport tracking, adapted from the existing global pointer effect.
 * One scheduled CSS update per frame; never captures a pointer or updates React state.
 */
export function attachCursorLight(
  element: Pick<HTMLElement, "style">,
  viewport: Window = window,
  page: Document = document,
) {
  const enabled = viewport.matchMedia(
    "(min-width: 761px) and (hover: hover) and (pointer: fine) and (prefers-reduced-motion: no-preference)",
  );
  let frame: number | undefined;
  let x = 0;
  let y = 0;

  const hide = () => {
    if (frame !== undefined) viewport.cancelAnimationFrame(frame);
    frame = undefined;
    element.style.setProperty("--cursor-active", "0");
  };
  const commit = () => {
    frame = undefined;
    if (!enabled.matches || page.hidden) return;
    element.style.setProperty("--cursor-x", `${x}px`);
    element.style.setProperty("--cursor-y", `${y}px`);
    element.style.setProperty("--cursor-active", "1");
  };
  const move = (event: PointerEvent) => {
    if (
      !enabled.matches ||
      event.pointerType !== "mouse" ||
      event.clientX < 0 ||
      event.clientY < 0 ||
      event.clientX > viewport.innerWidth ||
      event.clientY > viewport.innerHeight
    ) {
      hide();
      return;
    }
    x = event.clientX;
    y = event.clientY;
    if (frame === undefined) frame = viewport.requestAnimationFrame(commit);
  };
  const capabilityChange = () => hide();
  const visibilityChange = () => {
    if (page.hidden) hide();
  };

  viewport.addEventListener("pointermove", move, { passive: true });
  viewport.addEventListener("blur", hide);
  page.documentElement.addEventListener("pointerleave", hide);
  page.addEventListener("visibilitychange", visibilityChange);
  enabled.addEventListener("change", capabilityChange);
  return () => {
    hide();
    viewport.removeEventListener("pointermove", move);
    viewport.removeEventListener("blur", hide);
    page.documentElement.removeEventListener("pointerleave", hide);
    page.removeEventListener("visibilitychange", visibilityChange);
    enabled.removeEventListener("change", capabilityChange);
  };
}
