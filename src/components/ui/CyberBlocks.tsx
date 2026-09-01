import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

/**
 * SPECIAL VISUAL ELEMENT
 * Original abstract "interconnected data cubes" mark built from SVG only.
 * Used on the landing page, hero areas and empty states.
 */
export function CyberBlocks({ className }: { className?: string }) {
  const cubes = [
    { x: 120, y: 40, s: 62, c: "var(--accent)", d: 0 },
    { x: 40, y: 108, s: 52, c: "var(--network)", d: 0.15 },
    { x: 196, y: 104, s: 46, c: "var(--ai)", d: 0.3 },
    { x: 108, y: 168, s: 70, c: "var(--accent)", d: 0.45 },
    { x: 212, y: 200, s: 38, c: "var(--network)", d: 0.6 },
    { x: 44, y: 216, s: 34, c: "var(--ai)", d: 0.75 },
  ];

  const links: [number, number][] = [
    [0, 1],
    [0, 2],
    [1, 3],
    [2, 3],
    [3, 4],
    [3, 5],
    [1, 5],
    [2, 4],
  ];

  return (
    <div className={cn("relative", className)}>
      <div className="pointer-events-none absolute inset-0 rounded-full bg-accent/5 blur-3xl" />
      <svg viewBox="0 0 300 300" className="relative h-full w-full" role="presentation">
        <g stroke="oklch(1 0 0 / 14%)" strokeWidth="1">
          {links.map(([a, b], i) => {
            const from = cubes[a]!;
            const to = cubes[b]!;
            return (
              <motion.line
                key={i}
                x1={from.x + from.s / 2}
                y1={from.y + from.s / 2}
                x2={to.x + to.s / 2}
                y2={to.y + to.s / 2}
                initial={{ pathLength: 0, opacity: 0 }}
                animate={{ pathLength: 1, opacity: 1 }}
                transition={{ duration: 0.9, delay: 0.2 + i * 0.06, ease: "easeOut" }}
              />
            );
          })}
        </g>
        {cubes.map((cube, i) => (
          <motion.g
            key={i}
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: cube.d, ease: [0.22, 1, 0.36, 1] }}
          >
            {/* isometric-ish stacked block */}
            <rect
              x={cube.x}
              y={cube.y}
              width={cube.s}
              height={cube.s}
              rx="3"
              fill="oklch(0.18 0 0)"
              stroke={cube.c}
              strokeOpacity="0.7"
            />
            <rect
              x={cube.x + 6}
              y={cube.y + 6}
              width={cube.s - 12}
              height={cube.s - 12}
              rx="2"
              fill={cube.c}
              fillOpacity="0.12"
            />
            <circle cx={cube.x + cube.s / 2} cy={cube.y + cube.s / 2} r="3" fill={cube.c} />
          </motion.g>
        ))}
      </svg>
    </div>
  );
}
