/** Decorative topology only: never represents live case or threat data. */
export type Region = "graphite" | "lime" | "cyan" | "magenta" | "core";
export interface Voxel {
  x: number;
  y: number;
  z: number;
  region: Region;
  fill: "solid" | "glass" | "wire";
  brightness: number;
}

export const CELL_SIZE = 0.34;
export const SCENE_RADIUS = 3.15;
export const MAX_PITCH = 0.72;
export const MAX_VELOCITY = 1.8;
export const INITIAL_YAW = -0.58;
export const INITIAL_PITCH = 0.3;

export function seededRandom(seed: number) {
  let state = seed >>> 0;
  return () => {
    state = (Math.imul(state, 1664525) + 1013904223) >>> 0;
    return state / 4294967296;
  };
}

export function createVoxels(): Voxel[] {
  const random = seededRandom(26106);
  const cells: Voxel[] = [];
  for (let x = -5; x <= 5; x++) {
    for (let y = -5; y <= 6; y++) {
      for (let z = -4; z <= 4; z++) {
        const base = y <= -1 && y >= -5 && Math.abs(x) <= 4;
        const lime = x <= 0 && x >= -5 && y >= 0 && y <= 4 && z >= 0;
        const cyan = x >= 1 && y >= -1 && y <= 4 && z <= 2;
        const magenta = x >= -2 && x <= 2 && y >= 2 && z <= -1;
        if (!base && !lime && !cyan && !magenta) continue;
        const core = x >= -1 && x <= 0 && y >= 0 && y <= 1 && z >= 2 && z <= 3;
        const region: Region = core
          ? "core"
          : lime
            ? "lime"
            : cyan
              ? "cyan"
              : magenta
                ? "magenta"
                : "graphite";
        // Keep adjoining regions connected, but break up their outer silhouettes.
        if (!core && random() < (y === 6 || Math.abs(x) === 5 ? 0.22 : 0.07)) continue;
        const density = random();
        cells.push({
          x: x * CELL_SIZE,
          y: (y - 0.5) * CELL_SIZE,
          z: z * CELL_SIZE,
          region,
          fill: core || density < (base ? 0.26 : 0.23) ? "solid" : density < 0.4 ? "glass" : "wire",
          brightness: 0.55 + random() * 0.45,
        });
      }
    }
  }
  return cells;
}

export const clampPitch = (pitch: number) => Math.max(-MAX_PITCH, Math.min(MAX_PITCH, pitch));
export const clampVelocity = (speed: number) =>
  Math.max(-MAX_VELOCITY, Math.min(MAX_VELOCITY, speed));

/** Time-based damping: 0.92 per 60 Hz frame, with exact integrated displacement. */
export function coast(velocity: number, seconds: number) {
  const decay = -Math.log(0.92) * 60;
  const next = velocity * Math.exp(-decay * seconds);
  return { velocity: Math.abs(next) < 0.002 ? 0 : next, delta: (velocity - next) / decay };
}

/** Fit a bounding sphere at every rotation, including sparse drifting fragments. */
export function cameraDistance(aspect: number, fovDegrees = 36) {
  const vertical = (fovDegrees * Math.PI) / 360;
  const horizontal = Math.atan(Math.tan(vertical) * aspect);
  return (SCENE_RADIUS / Math.sin(Math.min(vertical, horizontal))) * 1.06;
}
