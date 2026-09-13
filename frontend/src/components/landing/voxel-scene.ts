import * as THREE from "three";
import { EffectComposer } from "three/addons/postprocessing/EffectComposer.js";
import { RenderPass } from "three/addons/postprocessing/RenderPass.js";
import { UnrealBloomPass } from "three/addons/postprocessing/UnrealBloomPass.js";
import { OutputPass } from "three/addons/postprocessing/OutputPass.js";
import {
  CELL_SIZE,
  INITIAL_PITCH,
  INITIAL_YAW,
  cameraDistance,
  clampPitch,
  clampVelocity,
  coast,
  createVoxels,
  seededRandom,
  type Region,
} from "./voxel-data";

const palette: Record<Region, string> = {
  graphite: "#444b46",
  lime: "#d7ff00",
  cyan: "#60f5e0",
  magenta: "#f624c4",
  core: "#efff8a",
};

function buildStructure() {
  const assembly = new THREE.Group();
  const cells = createVoxels();
  const cube = new THREE.BoxGeometry(CELL_SIZE * 0.91, CELL_SIZE * 0.91, CELL_SIZE * 0.91);
  const edgeBox = new THREE.BoxGeometry(CELL_SIZE, CELL_SIZE, CELL_SIZE);
  const edges = new THREE.EdgesGeometry(edgeBox);
  edgeBox.dispose();
  const edgeArray = edges.getAttribute("position");
  const transform = new THREE.Object3D();
  const color = new THREE.Color();
  const ownedMaterials: THREE.Material[] = [];

  for (const region of Object.keys(palette) as Region[]) {
    const regionCells = cells.filter((cell) => cell.region === region);
    for (const fill of ["solid", "glass"] as const) {
      const filled = regionCells.filter((cell) => cell.fill === fill);
      if (!filled.length) continue;
      const material = new THREE.MeshStandardMaterial({
        color: palette[region],
        roughness: 0.55,
        metalness: region === "graphite" ? 0.5 : 0.15,
        emissive: palette[region],
        emissiveIntensity: region === "core" ? 2.4 : region === "graphite" ? 0.025 : 0.16,
        transparent: fill === "glass",
        opacity: fill === "glass" ? 0.13 : 1,
        depthWrite: fill !== "glass",
      });
      ownedMaterials.push(material);
      const mesh = new THREE.InstancedMesh(cube, material, filled.length);
      filled.forEach((cell, index) => {
        transform.position.set(cell.x, cell.y, cell.z);
        transform.updateMatrix();
        mesh.setMatrixAt(index, transform.matrix);
        mesh.setColorAt(index, color.setScalar(cell.brightness));
      });
      mesh.computeBoundingSphere();
      assembly.add(mesh);
    }

    const lines: number[] = [];
    const points: number[] = [];
    for (const cell of regionCells) {
      for (let i = 0; i < edgeArray.count; i++) {
        lines.push(
          edgeArray.getX(i) + cell.x,
          edgeArray.getY(i) + cell.y,
          edgeArray.getZ(i) + cell.z,
        );
      }
      // Dense, static forensic-matrix points on graphite cell edges.
      if (region === "graphite" || cell.fill === "wire") {
        for (let i = 0; i < edgeArray.count; i += 2) {
          for (let step = 0; step < 3; step++) {
            const t = step / 3;
            points.push(
              THREE.MathUtils.lerp(edgeArray.getX(i), edgeArray.getX(i + 1), t) + cell.x,
              THREE.MathUtils.lerp(edgeArray.getY(i), edgeArray.getY(i + 1), t) + cell.y,
              THREE.MathUtils.lerp(edgeArray.getZ(i), edgeArray.getZ(i + 1), t) + cell.z,
            );
          }
        }
      }
    }
    const lineGeometry = new THREE.BufferGeometry();
    lineGeometry.setAttribute("position", new THREE.Float32BufferAttribute(lines, 3));
    const lineMaterial = new THREE.LineBasicMaterial({
      color: palette[region],
      transparent: true,
      opacity: region === "graphite" ? 0.32 : 0.55,
    });
    assembly.add(new THREE.LineSegments(lineGeometry, lineMaterial));
    const pointGeometry = new THREE.BufferGeometry();
    pointGeometry.setAttribute("position", new THREE.Float32BufferAttribute(points, 3));
    assembly.add(
      new THREE.Points(
        pointGeometry,
        new THREE.PointsMaterial({
          color: region === "graphite" ? "#c8d4c7" : palette[region],
          size: region === "graphite" ? 0.019 : 0.014,
          transparent: true,
          opacity: region === "graphite" ? 0.85 : 0.4,
          depthWrite: false,
        }),
      ),
    );
  }
  edges.dispose();

  const random = seededRandom(2106);
  const fragments: { mesh: THREE.Mesh | THREE.LineSegments; y: number; phase: number }[] = [];
  const fragmentGeometry = new THREE.PlaneGeometry(0.12, 0.12);
  const fragmentEdges = new THREE.EdgesGeometry(fragmentGeometry);
  for (let i = 0; i < 18; i++) {
    const region = (["lime", "cyan", "magenta"] as const)[i % 3]!;
    const fragment =
      i % 3 === 0
        ? new THREE.LineSegments(
            fragmentEdges,
            new THREE.LineBasicMaterial({ color: palette[region] }),
          )
        : new THREE.Mesh(
            fragmentGeometry,
            new THREE.MeshBasicMaterial({ color: palette[region], side: THREE.DoubleSide }),
          );
    const angle = random() * Math.PI * 2;
    fragment.position.set(
      Math.cos(angle) * (2.0 + random() * 0.35),
      0.3 + random() * 1.4,
      Math.sin(angle) * 1.8,
    );
    fragment.rotation.set(random() * 0.7, random() * 1.2, random() * 0.4);
    fragments.push({ mesh: fragment, y: fragment.position.y, phase: random() * Math.PI * 2 });
    assembly.add(fragment);
  }
  const coreLight = new THREE.PointLight("#ddff5a", 2.5, 3, 2);
  coreLight.position.set(-0.15, 0.05, 1.1);
  assembly.add(coreLight);
  return { assembly, fragments, coreLight, ownedMaterials, cube, fragmentGeometry, fragmentEdges };
}

function createFloor() {
  return new THREE.Mesh(
    new THREE.PlaneGeometry(24, 24),
    new THREE.ShaderMaterial({
      transparent: true,
      depthWrite: false,
      vertexShader: `varying vec2 gridPosition;
      void main() { gridPosition = position.xy; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`,
      fragmentShader: `varying vec2 gridPosition;
      void main() {
        vec2 p = gridPosition / 0.38;
        vec2 grid = abs(fract(p - 0.5) - 0.5) / fwidth(p);
        float line = 1.0 - min(min(grid.x, grid.y), 1.0);
        float fade = exp(-length(gridPosition) * 0.5);
        float glow = exp(-length(gridPosition - vec2(-1., 1.)) * 0.5);
        vec3 color = mix(vec3(0.13, 0.16, 0.13), vec3(0.40, 0.46, 0.10), glow);
        gl_FragColor = vec4(color, line * fade * 0.17);
      }`,
    }),
  );
}

/** Landing-only renderer. No React updates, new GPU resources or network work in the frame loop. */
export function mountVoxelScene(canvas: HTMLCanvasElement, onFailure: () => void) {
  const renderer = new THREE.WebGLRenderer({
    canvas,
    antialias: true,
    alpha: false,
    powerPreference: "low-power",
  });
  renderer.setClearColor("#000000");
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 0.95;
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(36, 1, 0.1, 60);
  const structure = buildStructure();
  const { assembly, fragments, coreLight } = structure;
  scene.add(assembly);
  scene.add(new THREE.AmbientLight("#c7d1c4", 1.4));
  const key = new THREE.DirectionalLight("#f1fff3", 3);
  key.position.set(-3, 6, 5);
  scene.add(key);
  const floor = createFloor();
  floor.rotation.x = -Math.PI / 2;
  floor.position.y = -3.4;
  scene.add(floor);

  const composer = new EffectComposer(renderer);
  const renderPass = new RenderPass(scene, camera);
  const bloom = new UnrealBloomPass(new THREE.Vector2(1, 1), 0.28, 0.25, 1.08);
  const output = new OutputPass();
  composer.addPass(renderPass);
  composer.addPass(bloom);
  composer.addPass(output);

  const motionQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
  let reduced = motionQuery.matches;
  let yaw = INITIAL_YAW;
  let pitch = INITIAL_PITCH;
  let velocityX = 0;
  let velocityY = 0;
  let drag: { id: number; x: number; y: number; time: number } | null = null;
  let frame = 0;
  let last = 0;
  let elapsed = 0;
  let visible = true;
  let disposed = false;

  function render(now: number) {
    frame = 0;
    if (disposed || !visible || document.hidden) return;
    const delta = last ? Math.min((now - last) / 1000, 0.05) : 0;
    last = now;
    elapsed += delta;
    if (!drag) {
      const x = coast(velocityX, delta);
      const y = coast(velocityY, delta);
      velocityX = x.velocity;
      velocityY = y.velocity;
      yaw += x.delta;
      pitch = clampPitch(pitch + y.delta);
    }
    assembly.rotation.set(pitch, yaw, 0, "YXZ");
    const entrance = reduced ? 1 : 1 - Math.pow(1 - Math.min(elapsed / 0.95, 1), 3);
    assembly.scale.setScalar(0.94 + entrance * 0.06);
    assembly.position.y = reduced ? 0 : Math.sin(elapsed * 0.5) * 0.025;
    coreLight.intensity = reduced ? 2.5 : 2.5 + Math.sin(elapsed * 0.8) * 0.15;
    for (const fragment of fragments) {
      fragment.mesh.position.y =
        fragment.y + (reduced ? 0 : Math.sin(elapsed * 0.45 + fragment.phase) * 0.045);
    }
    composer.render();
    // Reduced motion draws only when resized/dragged or while user-initiated inertia settles.
    if (!reduced || velocityX || velocityY) schedule();
  }
  function schedule() {
    if (!frame && !disposed && visible && !document.hidden) frame = requestAnimationFrame(render);
  }
  function resize() {
    const { width, height } = canvas.getBoundingClientRect();
    if (!width || !height) return;
    camera.aspect = width / height;
    const distance = cameraDistance(camera.aspect);
    camera.position.set(0, distance * 0.26, distance * 0.966);
    camera.lookAt(0, 0, 0);
    camera.updateProjectionMatrix();
    renderer.setSize(width, height, false);
    composer.setSize(width, height);
    schedule();
  }
  function down(event: PointerEvent) {
    if (drag || (event.pointerType === "mouse" && event.button !== 0)) return;
    event.preventDefault();
    canvas.setPointerCapture(event.pointerId);
    drag = { id: event.pointerId, x: event.clientX, y: event.clientY, time: event.timeStamp };
    velocityX = velocityY = 0;
    canvas.dataset["dragging"] = "true";
  }
  function move(event: PointerEvent) {
    if (!drag || drag.id !== event.pointerId) return;
    const dt = Math.max((event.timeStamp - drag.time) / 1000, 0.008);
    const dx = (event.clientX - drag.x) * 0.005;
    const dy = (event.clientY - drag.y) * 0.004;
    yaw += dx;
    pitch = clampPitch(pitch + dy);
    velocityX = clampVelocity(dx / dt) * 0.7;
    velocityY = clampVelocity(dy / dt) * 0.7;
    drag.x = event.clientX;
    drag.y = event.clientY;
    drag.time = event.timeStamp;
    schedule();
  }
  function up(event: PointerEvent) {
    if (!drag || drag.id !== event.pointerId) return;
    if (event.type !== "pointerup" || event.timeStamp - drag.time > 90) velocityX = velocityY = 0;
    drag = null;
    canvas.dataset["dragging"] = "false";
    if (canvas.hasPointerCapture(event.pointerId)) canvas.releasePointerCapture(event.pointerId);
    schedule();
  }
  function keydown(event: KeyboardEvent) {
    if (!["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", "Home"].includes(event.key)) return;
    event.preventDefault();
    velocityX = velocityY = 0;
    if (event.key === "Home") {
      yaw = INITIAL_YAW;
      pitch = INITIAL_PITCH;
    }
    if (event.key === "ArrowLeft") yaw -= 0.13;
    if (event.key === "ArrowRight") yaw += 0.13;
    if (event.key === "ArrowUp") pitch = clampPitch(pitch - 0.1);
    if (event.key === "ArrowDown") pitch = clampPitch(pitch + 0.1);
    schedule();
  }
  function motionChange() {
    reduced = motionQuery.matches;
    schedule();
  }
  function visibilityChange() {
    last = 0;
    schedule();
  }
  function contextLost(event: Event) {
    event.preventDefault();
    cancelAnimationFrame(frame);
    disposed = true;
    visible = false;
    onFailure();
  }
  const resizeObserver = new ResizeObserver(resize);
  const intersectionObserver = new IntersectionObserver(([entry]) => {
    visible = entry?.isIntersecting ?? false;
    last = 0;
    schedule();
  });
  resizeObserver.observe(canvas);
  intersectionObserver.observe(canvas);
  canvas.addEventListener("pointerdown", down);
  canvas.addEventListener("pointermove", move);
  canvas.addEventListener("pointerup", up);
  canvas.addEventListener("pointercancel", up);
  canvas.addEventListener("lostpointercapture", up);
  canvas.addEventListener("keydown", keydown);
  canvas.addEventListener("webglcontextlost", contextLost);
  motionQuery.addEventListener("change", motionChange);
  document.addEventListener("visibilitychange", visibilityChange);
  resize();

  return () => {
    disposed = true;
    cancelAnimationFrame(frame);
    resizeObserver.disconnect();
    intersectionObserver.disconnect();
    canvas.removeEventListener("pointerdown", down);
    canvas.removeEventListener("pointermove", move);
    canvas.removeEventListener("pointerup", up);
    canvas.removeEventListener("pointercancel", up);
    canvas.removeEventListener("lostpointercapture", up);
    canvas.removeEventListener("keydown", keydown);
    canvas.removeEventListener("webglcontextlost", contextLost);
    motionQuery.removeEventListener("change", motionChange);
    document.removeEventListener("visibilitychange", visibilityChange);
    const geometries = new Set<THREE.BufferGeometry>([
      structure.cube,
      structure.fragmentGeometry,
      structure.fragmentEdges,
    ]);
    const materials = new Set<THREE.Material>(structure.ownedMaterials);
    scene.traverse((object) => {
      if (
        object instanceof THREE.Mesh ||
        object instanceof THREE.LineSegments ||
        object instanceof THREE.Points
      ) {
        geometries.add(object.geometry);
        if (Array.isArray(object.material))
          object.material.forEach((material) => materials.add(material));
        else materials.add(object.material);
      }
      if (object instanceof THREE.InstancedMesh) object.dispose();
    });
    geometries.forEach((geometry) => geometry.dispose());
    materials.forEach((material) => material.dispose());
    bloom.dispose();
    output.dispose();
    renderPass.dispose();
    composer.dispose();
    renderer.dispose();
  };
}
