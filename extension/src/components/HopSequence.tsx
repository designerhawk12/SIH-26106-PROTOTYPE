import type { Hop } from "../hooks/useApi";

interface Props {
  hops: Hop[];
  selectedHopIndex: number | null;
  onSelectHop: (index: number) => void;
}

/**
 * Determines whether a hop has usable geographic coordinates.
 */
function hasValidGeo(hop: Hop): boolean {
  const lat = hop.geo?.lat;
  const lon = hop.geo?.lon;

  return (
    typeof lat === "number" &&
    typeof lon === "number" &&
    Number.isFinite(lat) &&
    Number.isFinite(lon) &&
    lat >= -90 &&
    lat <= 90 &&
    lon >= -180 &&
    lon <= 180 &&
    !(lat === 0 && lon === 0)
  );
}

export default function HopSequence({
  hops,
  selectedHopIndex,
  onSelectHop,
}: Props) {
  if (hops.length === 0) {
    return (
      <div
        className="
          rounded-lg
          border
          border-zinc-800
          bg-zinc-900
          p-3
          text-xs
          text-zinc-500
        "
      >
        No hop data found for this message.
      </div>
    );
  }

  return (
    <div>
      <h3
        className="
          mb-2
          text-xs
          font-semibold
          uppercase
          tracking-wider
          text-zinc-500
        "
      >
        Hop-to-Hop Sequence
      </h3>

      <div className="space-y-2">
        {hops.map((hop, index) => {
          const selected = selectedHopIndex === index;
          const geolocatable = hasValidGeo(hop);

          return (
            <button
              key={`${hop.ip}-${index}`}
              type="button"
              onClick={() => onSelectHop(index)}
              className={`
                relative
                w-full
                rounded-lg
                border
                p-3
                text-left
                transition-all
                duration-200
                focus:outline-none
                focus:ring-1
                ${
                  selected
                    ? "border-orange-500/60 bg-orange-500/10 shadow-[0_0_22px_rgba(249,115,22,0.10)] focus:ring-orange-500/50"
                    : "border-zinc-800 bg-zinc-900 hover:border-zinc-700 hover:bg-zinc-800 focus:ring-emerald-500/50"
                }
              `}
            >
              <div className="flex items-center gap-3">
                {/* Hop number */}
                <div
                  className={`
                    flex
                    h-8
                    w-8
                    shrink-0
                    items-center
                    justify-center
                    rounded-full
                    border
                    text-xs
                    font-bold
                    transition-all
                    duration-200
                    ${
                      selected
                        ? "border-orange-200 bg-orange-500 text-white shadow-[0_0_16px_rgba(249,115,22,0.35)]"
                        : "border-emerald-500/30 bg-emerald-500/5 text-emerald-400"
                    }
                  `}
                >
                  {index + 1}
                </div>

                {/* Host sequence */}
                <div className="min-w-0 flex-1">
                  <div
                    className={`
                      truncate
                      text-xs
                      font-medium
                      ${selected ? "text-orange-300" : "text-zinc-200"}
                    `}
                  >
                    {hop.from_host || "Unknown source"}
                  </div>

                  <div className="text-[10px] text-zinc-600">↓</div>

                  <div className="truncate text-xs text-zinc-400">
                    {hop.by_host || "Unknown relay"}
                  </div>
                </div>

                {/* IP + geo */}
                <div className="max-w-[150px] text-right">
                  <div
                    className="
                      truncate
                      text-[10px]
                      font-mono
                      text-zinc-400
                    "
                  >
                    {hop.ip || "No IP"}
                  </div>

                  {hop.geo && (
                    <div
                      className={`
                        mt-1
                        truncate
                        text-[9px]
                        ${geolocatable ? "text-orange-400" : "text-zinc-600"}
                      `}
                    >
                      {hop.geo.city || "Unknown city"}
                      {hop.geo.country ? `, ${hop.geo.country}` : ""}
                    </div>
                  )}

                  {!hop.geo && (
                    <div className="mt-1 text-[9px] text-zinc-600">
                      No geolocation
                    </div>
                  )}
                </div>
              </div>

              {/* Selected state */}
              {selected && (
                <div
                  className="
                    mt-2
                    border-t
                    border-orange-500/20
                    pt-2
                    text-[9px]
                    uppercase
                    tracking-wider
                    text-orange-400
                  "
                >
                  {geolocatable
                    ? "Map location selected"
                    : "Hop selected • no map location available"}
                </div>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}
