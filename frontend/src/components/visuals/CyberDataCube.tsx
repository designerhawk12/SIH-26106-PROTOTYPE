import { motion, useMotionValue, useSpring, useTransform, type MotionValue } from "framer-motion";
import { Binary, Fingerprint, Mail, Network, ShieldCheck } from "lucide-react";
import {
  useEffect,
  useRef,
  type CSSProperties,
  type PointerEvent as ReactPointerEvent,
} from "react";
import { DataPulse } from "@/components/effects/DataPulse";
import { useGlobalPointerMotion } from "@/hooks/useGlobalPointerMotion";
import { cn } from "@/lib/utils";

const blocks = [
  {
    x: 128,
    y: 72,
    z: 16,
    size: 62,
    tone: "accent",
    label: "Message",
    Icon: Mail,
    parallax: 4,
    float: 4,
  },
  {
    x: 66,
    y: 144,
    z: -8,
    size: 50,
    tone: "network",
    label: "Route",
    Icon: Network,
    parallax: 2.5,
    float: 3,
  },
  {
    x: 218,
    y: 136,
    z: 2,
    size: 48,
    tone: "ai",
    label: "Intent",
    Icon: Binary,
    parallax: 3.25,
    float: 3.5,
  },
  {
    x: 138,
    y: 218,
    z: 20,
    size: 66,
    tone: "accent",
    label: "Evidence",
    Icon: Fingerprint,
    parallax: 5,
    float: 4.5,
  },
  {
    x: 232,
    y: 224,
    z: -4,
    size: 38,
    tone: "network",
    label: "Trust",
    Icon: ShieldCheck,
    parallax: 2,
    float: 2.5,
  },
] as const;

const links = [
  [128, 72, 66, 144],
  [128, 72, 218, 136],
  [66, 144, 138, 218],
  [218, 136, 138, 218],
  [138, 218, 232, 224],
] as const;

const HORIZONTAL_DRAG_SENSITIVITY = 0.75;
const VERTICAL_DRAG_SENSITIVITY = 0.45;
const MAX_VERTICAL_ROTATION = 60;

function clampVerticalRotation(value: number) {
  return Math.max(-MAX_VERTICAL_ROTATION, Math.min(MAX_VERTICAL_ROTATION, value));
}

function DataBlock({
  x,
  y,
  z,
  size,
  tone,
  label,
  Icon,
  index,
  parallax,
  float,
  pointerX,
  pointerY,
  reduceMotion,
}: (typeof blocks)[number] & {
  index: number;
  pointerX: MotionValue<number>;
  pointerY: MotionValue<number>;
  reduceMotion: boolean;
}) {
  const manualRotateX = useMotionValue(reduceMotion ? -6 : -7);
  const manualRotateY = useMotionValue(-12);
  const parallaxInfluence = useMotionValue(1);
  const dragState = useRef<{
    pointerId: number;
    startClientX: number;
    startClientY: number;
    startRotateX: number;
    startRotateY: number;
  } | null>(null);
  const removeReleaseFallback = useRef<(() => void) | null>(null);
  const translateX = useTransform(() => pointerX.get() * parallax * parallaxInfluence.get());
  const translateY = useTransform(() => pointerY.get() * parallax * 0.65 * parallaxInfluence.get());
  const rotateX = useTransform(() => pointerY.get() * -parallax * 0.5 * parallaxInfluence.get());
  const rotateY = useTransform(() => pointerX.get() * parallax * 0.7 * parallaxInfluence.get());
  const style = {
    "--cube-size": `${size / 3}cqw`,
    "--cube-half": `${size / 6}cqw`,
    "--cube-color": `var(--${tone})`,
    left: `${x / 3}%`,
    top: `${y / 3}%`,
    width: `${size / 3}cqw`,
    height: `${size / 3}cqw`,
    transform: `translate3d(-50%, -50%, ${z / 3}cqw)`,
  } as CSSProperties;

  useEffect(
    () => () => {
      removeReleaseFallback.current?.();
    },
    [],
  );

  const finishDrag = (element: HTMLDivElement, pointerId: number) => {
    if (dragState.current?.pointerId !== pointerId) return;

    dragState.current = null;
    removeReleaseFallback.current?.();
    removeReleaseFallback.current = null;
    if (element.hasPointerCapture(pointerId)) element.releasePointerCapture(pointerId);
    parallaxInfluence.set(1);
    element.dataset["dragging"] = "false";
  };

  const startDrag = (event: ReactPointerEvent<HTMLDivElement>) => {
    if (event.pointerType === "mouse" && event.button !== 0) return;

    event.currentTarget.setPointerCapture(event.pointerId);
    dragState.current = {
      pointerId: event.pointerId,
      startClientX: event.clientX,
      startClientY: event.clientY,
      startRotateX: manualRotateX.get(),
      startRotateY: manualRotateY.get(),
    };
    parallaxInfluence.set(0);
    event.currentTarget.dataset["dragging"] = "true";

    const draggedElement = event.currentTarget;
    const releaseFromWindow = (releaseEvent: PointerEvent) => {
      finishDrag(draggedElement, releaseEvent.pointerId);
    };
    window.addEventListener("pointerup", releaseFromWindow, { once: true });
    window.addEventListener("pointercancel", releaseFromWindow, { once: true });
    removeReleaseFallback.current = () => {
      window.removeEventListener("pointerup", releaseFromWindow);
      window.removeEventListener("pointercancel", releaseFromWindow);
    };
  };

  const updateDrag = (event: ReactPointerEvent<HTMLDivElement>) => {
    const activeDrag = dragState.current;
    if (!activeDrag || activeDrag.pointerId !== event.pointerId) return;

    manualRotateY.set(
      activeDrag.startRotateY +
        (event.clientX - activeDrag.startClientX) * HORIZONTAL_DRAG_SENSITIVITY,
    );
    manualRotateX.set(
      clampVerticalRotation(
        activeDrag.startRotateX -
          (event.clientY - activeDrag.startClientY) * VERTICAL_DRAG_SENSITIVITY,
      ),
    );
  };

  const stopDrag = (event: ReactPointerEvent<HTMLDivElement>) => {
    finishDrag(event.currentTarget, event.pointerId);
  };

  return (
    <div className="cyber-cube-anchor" style={style} data-cube-label={label}>
      <motion.div
        className="h-full w-full"
        style={
          reduceMotion
            ? { transformStyle: "preserve-3d" }
            : {
                x: translateX,
                y: translateY,
                rotateX,
                rotateY,
                transformPerspective: 850,
                transformStyle: "preserve-3d",
              }
        }
      >
        <motion.div
          className="h-full w-full"
          animate={reduceMotion ? {} : { y: [0, -float, 0], rotateZ: [0, 0.45, 0] }}
          transition={{
            y: {
              duration: 4.4 + index * 0.35,
              delay: 0.35 + index * 0.16,
              repeat: Infinity,
              ease: "easeInOut",
            },
            rotateZ: {
              duration: 5.2 + index * 0.4,
              delay: 0.35 + index * 0.16,
              repeat: Infinity,
              ease: "easeInOut",
            },
          }}
        >
          <motion.div
            className={cn(
              "cyber-cube cursor-grab touch-none select-none active:cursor-grabbing",
              "data-[dragging=true]:cursor-grabbing",
            )}
            initial={{ opacity: 0, scale: 0.76 }}
            animate={{ opacity: 1, scale: 1 }}
            style={{
              rotateX: manualRotateX,
              rotateY: manualRotateY,
              transformStyle: "preserve-3d",
            }}
            transition={{
              opacity: { duration: 0.4, delay: 0.08 + index * 0.07 },
              scale: {
                duration: 0.5,
                delay: 0.08 + index * 0.07,
                ease: [0.16, 1, 0.3, 1],
              },
            }}
            onPointerDown={startDrag}
            onPointerMove={updateDrag}
            onPointerUp={stopDrag}
            onPointerCancel={stopDrag}
            onLostPointerCapture={stopDrag}
            draggable={false}
            data-dragging="false"
            title={label}
          >
            <span className="cyber-cube-face cyber-cube-front">
              <Icon className="h-[28%] w-[28%]" strokeWidth={1.35} />
            </span>
            <span className="cyber-cube-face cyber-cube-back" />
            <span className="cyber-cube-face cyber-cube-right" />
            <span className="cyber-cube-face cyber-cube-left" />
            <span className="cyber-cube-face cyber-cube-top" />
            <span className="cyber-cube-face cyber-cube-bottom" />
          </motion.div>
        </motion.div>
      </motion.div>
    </div>
  );
}

/** True CSS 3D data-block cluster used as the product's signature visual. */
export function CyberDataCube({
  className,
  compact = false,
}: {
  className?: string;
  compact?: boolean;
}) {
  const { normalizedX: pointerX, normalizedY: pointerY, reduceMotion } = useGlobalPointerMotion();
  const smoothPointerX = useSpring(pointerX, { stiffness: 105, damping: 23, mass: 0.62 });
  const smoothPointerY = useSpring(pointerY, { stiffness: 105, damping: 23, mass: 0.62 });

  return (
    <div
      className={cn(
        "cyber-cube-stage relative isolate overflow-hidden",
        compact && "cyber-cube-compact",
        className,
      )}
      data-global-pointer="true"
      role="img"
      aria-label="Interconnected email, infrastructure, AI, and forensic evidence data blocks"
    >
      <div className="pointer-events-none absolute inset-10 rounded-full bg-accent/[0.055] blur-3xl" />
      <svg
        aria-hidden
        viewBox="0 0 300 300"
        className="absolute inset-0 h-full w-full overflow-visible"
      >
        <g fill="none" stroke="currentColor" className="text-border-strong">
          {links.map(([x1, y1, x2, y2], index) => (
            <motion.line
              key={`${x1}-${y1}-${x2}-${y2}`}
              x1={x1}
              y1={y1}
              x2={x2}
              y2={y2}
              strokeWidth="1"
              strokeDasharray="3 5"
              initial={{ pathLength: 0, opacity: 0 }}
              animate={{ pathLength: 1, opacity: 0.8 }}
              transition={{ duration: 0.8, delay: 0.2 + index * 0.08 }}
            />
          ))}
        </g>
      </svg>
      <DataPulse className="left-[48%] top-[27%]" />
      <DataPulse className="left-[26%] top-[52%] bg-network" delay={0.55} />
      <DataPulse className="left-[72%] top-[49%] bg-ai" delay={1.05} />
      <div className="cyber-cube-cluster absolute inset-0">
        {blocks.map((block, index) => (
          <DataBlock
            key={block.label}
            {...block}
            index={index}
            pointerX={smoothPointerX}
            pointerY={smoothPointerY}
            reduceMotion={reduceMotion}
          />
        ))}
      </div>
      {!compact && (
        <div className="pointer-events-none absolute bottom-4 left-1/2 -translate-x-1/2 whitespace-nowrap font-mono text-[9px] uppercase tracking-[0.28em] text-muted-foreground/65">
          Evidence signal topology
        </div>
      )}
    </div>
  );
}
