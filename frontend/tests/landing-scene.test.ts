import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync } from "node:fs";
import { attachCursorLight } from "../src/components/landing/cursor-light.ts";
import {
  createVoxels,
  coast,
  clampPitch,
  clampVelocity,
  MAX_PITCH,
  MAX_VELOCITY,
  SCENE_RADIUS,
  CELL_SIZE,
  cameraDistance,
} from "../src/components/landing/voxel-data.ts";

test("voxel structure is deterministic, dense, and has every required region", () => {
  const cells = createVoxels();
  assert.deepEqual(cells, createVoxels());
  assert.ok(cells.length > 500 && cells.length < 1600);
  assert.deepEqual(
    new Set(cells.map((cell) => cell.region)),
    new Set(["graphite", "lime", "cyan", "magenta", "core"]),
  );
  assert.deepEqual(new Set(cells.map((cell) => cell.fill)), new Set(["solid", "glass", "wire"]));
  assert.equal(new Set(cells.map(({ x, y, z }) => `${x},${y},${z}`)).size, cells.length);
  for (const cell of cells)
    assert.ok(Math.hypot(cell.x, cell.y, cell.z) + (CELL_SIZE * Math.sqrt(3)) / 2 < SCENE_RADIUS);
});

test("inertia is bounded, decays to rest and is independent of frame rate", () => {
  assert.equal(clampVelocity(300), MAX_VELOCITY);
  assert.equal(clampVelocity(-300), -MAX_VELOCITY);
  assert.equal(clampPitch(20), MAX_PITCH);
  assert.equal(clampPitch(-20), -MAX_PITCH);
  assert.equal(coast(0, 1).delta, 0);
  assert.equal(coast(MAX_VELOCITY, 2).velocity, 0);
  const full = coast(1, 0.03);
  const half = coast(1, 0.015);
  const otherHalf = coast(half.velocity, 0.015);
  assert.ok(Math.abs(full.delta - half.delta - otherHalf.delta) < 1e-10);
  assert.ok(Math.abs(full.velocity - otherHalf.velocity) < 1e-10);
  assert.ok(full.delta < 0.03);
});

test("camera fits the entire rotational bounding sphere on phone and desktop", () => {
  for (const aspect of [0.55, 0.8, 1, 1.5, 2]) {
    const angle = Math.min(Math.PI / 10, Math.atan(Math.tan(Math.PI / 10) * aspect));
    assert.ok(cameraDistance(aspect) * Math.sin(angle) > SCENE_RADIUS);
  }
});

test("landing actions retain existing routes and four existing capabilities", () => {
  const source = readFileSync(new URL("../src/pages/LandingPage.tsx", import.meta.url), "utf8");
  assert.match(source, /to="\/analyze"/);
  assert.equal((source.match(/to="\/dashboard"/g) ?? []).length, 2);
  for (const title of [
    "Email Forensics",
    "AI Threat Intent",
    "Observed Infrastructure",
    "Evidence Integrity",
  ])
    assert.ok(source.includes(title));
});

function cursorHarness() {
  const media = Object.assign(new EventTarget(), { matches: true });
  const frames = new Map<number, FrameRequestCallback>();
  const style = new Map<string, string>();
  let sequence = 0;
  const viewport = Object.assign(new EventTarget(), {
    innerWidth: 1366,
    innerHeight: 768,
    matchMedia: () => media,
    requestAnimationFrame: (callback: FrameRequestCallback) => {
      frames.set(++sequence, callback);
      return sequence;
    },
    cancelAnimationFrame: (id: number) => frames.delete(id),
  });
  const page = Object.assign(new EventTarget(), {
    hidden: false,
    documentElement: new EventTarget(),
  });
  const cleanup = attachCursorLight(
    {
      style: {
        setProperty: (name: string, value: string) => style.set(name, value),
      } as unknown as CSSStyleDeclaration,
    },
    viewport as unknown as Window,
    page as unknown as Document,
  );
  const move = (x: number, y: number, pointerType = "mouse") => {
    const event = Object.assign(new Event("pointermove", { cancelable: true }), {
      clientX: x,
      clientY: y,
      pointerType,
    });
    viewport.dispatchEvent(event);
    assert.equal(event.defaultPrevented, false, "background must not consume scene pointer events");
  };
  const flush = () => {
    for (const callback of frames.values()) callback(0);
    frames.clear();
  };
  return { media, frames, style, viewport, page, cleanup, move, flush };
}

test("cursor light batches pointer events, covers viewport coordinates and stays passive", () => {
  const h = cursorHarness();
  h.move(12, 20);
  h.move(1300, 640);
  assert.equal(h.frames.size, 1);
  h.flush();
  assert.equal(h.style.get("--cursor-x"), "1300px");
  assert.equal(h.style.get("--cursor-y"), "640px");
  assert.equal(h.style.get("--cursor-active"), "1");
  h.cleanup();
});

test("cursor leave cancels pending updates; returning reactivates and cleanup removes listeners", () => {
  const h = cursorHarness();
  h.move(50, 50);
  h.page.documentElement.dispatchEvent(new Event("pointerleave"));
  h.flush();
  assert.equal(h.style.get("--cursor-active"), "0");
  h.move(70, 70);
  h.flush();
  assert.equal(h.style.get("--cursor-active"), "1");
  h.viewport.dispatchEvent(new Event("blur"));
  assert.equal(h.style.get("--cursor-active"), "0");
  h.move(90, 90);
  h.move(-10, 80); // Captured scene drags can continue past the viewport boundary.
  h.flush();
  assert.equal(h.style.get("--cursor-active"), "0");
  h.move(80, 80);
  h.cleanup();
  assert.equal(h.frames.size, 0);
  h.move(90, 90);
  assert.equal(h.frames.size, 0);
});

test("touch, reduced motion/coarse-pointer preference and hidden pages suppress cursor light", () => {
  const h = cursorHarness();
  h.move(10, 10, "touch");
  assert.equal(h.frames.size, 0);
  h.move(30, 30);
  h.media.matches = false;
  h.media.dispatchEvent(new Event("change"));
  h.flush();
  assert.equal(h.style.get("--cursor-active"), "0");
  h.move(50, 50);
  assert.equal(h.frames.size, 0);
  h.media.matches = true;
  h.move(50, 50);
  h.flush();
  h.page.hidden = true;
  h.page.dispatchEvent(new Event("visibilitychange"));
  assert.equal(h.style.get("--cursor-active"), "0");
  h.cleanup();
});
