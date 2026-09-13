import { useEffect, useRef, useState } from "react";
import { Move, RotateCcw } from "lucide-react";

export function HeroScene() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [status, setStatus] = useState<"loading" | "ready" | "unavailable">("loading");
  useEffect(() => {
    let cancelled = false;
    let dispose: (() => void) | undefined;
    // Load WebGL only on the client and only on the public landing route.
    void import("./voxel-scene")
      .then(({ mountVoxelScene }) => {
        if (cancelled || !canvasRef.current) return;
        try {
          dispose = mountVoxelScene(canvasRef.current, () => setStatus("unavailable"));
          setStatus("ready");
        } catch {
          setStatus("unavailable");
        }
      })
      .catch(() => {
        if (!cancelled) setStatus("unavailable");
      });
    return () => {
      cancelled = true;
      dispose?.();
    };
  }, []);

  return (
    <figure className="landing-scene" aria-label="Interactive evidence topology illustration">
      <div className="landing-scene-label" aria-hidden="true">
        <span /> EVIDENCE SIGNAL TOPOLOGY{" "}
        <span className="landing-scene-label-end">3D / INTERACTIVE</span>
      </div>
      <canvas
        ref={canvasRef}
        className="landing-canvas"
        data-ready={status === "ready"}
        tabIndex={status === "ready" ? 0 : -1}
        role="img"
        aria-label="Connected lime, cyan and magenta voxel structure above a graphite evidence matrix. Drag to rotate. Arrow keys rotate; Home resets. Decorative illustration, not live case data."
        aria-describedby="topology-help"
      />
      {status !== "ready" && (
        <p className="landing-scene-status" role="status">
          {status === "loading"
            ? "INITIALIZING VISUALIZATION"
            : "3D visualization unavailable on this device. All investigation features remain accessible."}
        </p>
      )}
      <figcaption id="topology-help" className="landing-scene-help">
        <span>
          <Move size={12} /> Drag to explore
        </span>
        <span className="landing-keyboard-help">Arrow keys to rotate</span>
        <button
          type="button"
          aria-label="Reset 3D orientation"
          onClick={() => {
            canvasRef.current?.dispatchEvent(new KeyboardEvent("keydown", { key: "Home" }));
          }}
        >
          <RotateCcw size={12} /> Reset
        </button>
      </figcaption>
    </figure>
  );
}
