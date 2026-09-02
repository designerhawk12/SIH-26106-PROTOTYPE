import { CyberDataCube } from "@/components/visuals/CyberDataCube";

/**
 * SPECIAL VISUAL ELEMENT
 * Original abstract "interconnected data cubes" mark built from SVG only.
 * Used on the landing page, hero areas and empty states.
 */
export function CyberBlocks({ className }: { className?: string }) {
  return <CyberDataCube {...(className ? { className } : {})} />;
}
