import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  Polyline,
  ZoomControl,
  useMap,
} from "react-leaflet";

import { divIcon } from "leaflet";
import { useEffect } from "react";

import "leaflet/dist/leaflet.css";

import type { Hop } from "../hooks/useApi";

interface Props {
  hops: Hop[];
  selectedHopIndex: number | null;
}

/**
 * Returns true only when the hop contains usable geographic coordinates.
 *
 * Invalid/unresolved values such as:
 * - null
 * - NaN
 * - out-of-range values
 * - (0, 0) placeholders
 *
 * are never placed on the map.
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

/**
 * Creates a numbered orange forensic marker.
 *
 * The number is the ORIGINAL Received-chain hop number.
 */
function createHopIcon(hopNumber: number, selected: boolean) {
  return divIcon({
    className: "forensic-hop-marker",
    html: `
      <div
        style="
          width: 30px;
          height: 30px;
          border-radius: 9999px;
          background: ${selected ? "#ea580c" : "#f97316"};
          border: 2px solid ${selected ? "#fff7ed" : "#fed7aa"};
          color: white;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 12px;
          font-weight: 800;
          font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
          transform: ${selected ? "scale(1.15)" : "scale(1)"};
          box-shadow:
            0 0 0 ${selected ? "7px" : "4px"} rgba(249, 115, 22, ${
              selected ? "0.28" : "0.14"
            }),
            0 4px 14px rgba(0, 0, 0, 0.35);
          transition:
            transform 160ms ease,
            box-shadow 160ms ease;
        "
      >
        ${hopNumber}
      </div>
    `,
    iconSize: [30, 30],
    iconAnchor: [15, 15],
    popupAnchor: [0, -18],
  });
}

/**
 * Automatically frames the map around every geolocatable hop.
 */
function FitToLocations({ hops }: { hops: Hop[] }) {
  const map = useMap();

  useEffect(() => {
    const validHops = hops.filter(hasValidGeo);

    if (validHops.length === 0) {
      return;
    }

    const points = validHops.map(
      (hop) => [hop.geo!.lat!, hop.geo!.lon!] as [number, number],
    );

    if (points.length === 1) {
      map.flyTo(points[0], 7, {
        duration: 1.2,
        easeLinearity: 0.25,
      });

      return;
    }

    map.fitBounds(points, {
      padding: [45, 45],
      maxZoom: 8,
      animate: true,
      duration: 1.2,
      easeLinearity: 0.25,
    });
  }, [hops, map]);

  return null;
}

/**
 * Smoothly moves the map to the selected hop.
 *
 * Unresolved hops are selectable in the sequence but do not move the map.
 */
function FocusSelectedHop({ hops, selectedHopIndex }: Props) {
  const map = useMap();

  useEffect(() => {
    if (selectedHopIndex == null) {
      return;
    }

    const hop = hops[selectedHopIndex];

    if (!hop || !hasValidGeo(hop)) {
      return;
    }

    const lat = hop.geo!.lat!;
    const lon = hop.geo!.lon!;

    map.flyTo([lat, lon], 9, {
      duration: 1.1,
      easeLinearity: 0.2,
    });
  }, [hops, selectedHopIndex, map]);

  return null;
}

/**
 * Popup content for a geolocated hop.
 */
function HopPopup({ hop, hopNumber }: { hop: Hop; hopNumber: number }) {
  const geo = hop.geo;

  return (
    <div className="min-w-[220px] text-xs">
      <div className="mb-2 text-[10px] font-bold uppercase tracking-wider text-orange-600">
        Hop {hopNumber} · Observed Mail Infrastructure
      </div>

      <div className="text-sm font-semibold text-zinc-900">
        {geo?.isp || "Unknown organization"}
      </div>

      <div className="mt-1 text-zinc-700">
        {geo?.city || "Unknown city"}
        {geo?.country ? `, ${geo.country}` : ""}
      </div>

      <div className="mt-2 font-mono text-[10px] text-zinc-500">
        {hop.ip || "Unknown IP"}
      </div>

      {hop.from_host && (
        <div className="mt-2">
          <div className="text-[9px] font-semibold uppercase tracking-wide text-zinc-400">
            From
          </div>

          <div className="mt-0.5 break-all font-mono text-[10px] text-zinc-600">
            {hop.from_host}
          </div>
        </div>
      )}

      {hop.by_host && (
        <div className="mt-2">
          <div className="text-[9px] font-semibold uppercase tracking-wide text-zinc-400">
            By
          </div>

          <div className="mt-0.5 break-all font-mono text-[10px] text-zinc-600">
            {hop.by_host}
          </div>
        </div>
      )}

      {geo?.source && (
        <div className="mt-2 text-[9px] text-zinc-400">
          Geo source: {geo.source}
        </div>
      )}

      <div className="mt-3 border-t border-zinc-200 pt-2 text-[9px] leading-relaxed text-zinc-500">
        ⓘ This is the location of observed mail infrastructure, not the
        sender&apos;s physical location.
      </div>
    </div>
  );
}

export default function Map({ hops, selectedHopIndex }: Props) {
  /**
   * Preserve the ORIGINAL Received-chain hop index.
   *
   * Example:
   *
   * Hop 1 → unresolved
   * Hop 2 → Mountain View
   * Hop 3 → another location
   *
   * The map therefore displays:
   *
   * 🟠 2
   * 🟠 3
   *
   * rather than renumbering them as 1 and 2.
   */
  const geolocatedHops = hops
    .map((hop, index) => ({
      hop,
      originalIndex: index,
    }))
    .filter(({ hop }) => hasValidGeo(hop));

  const routePoints = geolocatedHops.map(
    ({ hop }) => [hop.geo!.lat!, hop.geo!.lon!] as [number, number],
  );

  return (
    <div className="overflow-hidden rounded-xl border border-zinc-800">
      {/* Map-specific styling */}
      <style>
        {`
          .forensic-map-shell .leaflet-control-zoom {
            border: 1px solid rgba(255, 255, 255, 0.12) !important;
            border-radius: 12px !important;
            overflow: hidden;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.28) !important;
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
          }

          .forensic-map-shell .leaflet-control-zoom a {
            width: 34px !important;
            height: 34px !important;
            line-height: 34px !important;
            background: rgba(9, 9, 11, 0.58) !important;
            color: rgba(255, 255, 255, 0.88) !important;
            border: 0 !important;
            font-size: 20px !important;
            font-weight: 500;
            transition:
              background 140ms ease,
              color 140ms ease;
          }

          .forensic-map-shell .leaflet-control-zoom a:hover {
            background: rgba(24, 24, 27, 0.80) !important;
            color: #fb923c !important;
          }

          .forensic-map-shell .leaflet-control-zoom a:active {
            background: rgba(249, 115, 22, 0.24) !important;
          }

          .forensic-map-shell .leaflet-control-attribution {
            background: rgba(9, 9, 11, 0.58) !important;
            color: rgba(255, 255, 255, 0.45) !important;
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
          }

          .forensic-map-shell .leaflet-control-attribution a {
            color: rgba(255, 255, 255, 0.70) !important;
          }

          .forensic-map-shell .leaflet-marker-icon {
            transition: filter 160ms ease;
          }

          .forensic-map-shell .leaflet-marker-icon:hover {
            filter:
              drop-shadow(0 0 8px rgba(249, 115, 22, 0.55));
          }

          .forensic-map-shell .leaflet-popup-content-wrapper {
            border-radius: 12px !important;
          }

          .forensic-map-shell .leaflet-popup-tip {
            box-shadow: none !important;
          }
        `}
      </style>

      <div className="forensic-map-shell">
        <MapContainer
          center={[20, 0]}
          zoom={2}
          scrollWheelZoom={true}
          touchZoom={true}
          dragging={true}
          zoomControl={false}
          zoomAnimation={true}
          fadeAnimation={true}
          markerZoomAnimation={true}
          wheelDebounceTime={20}
          wheelPxPerZoomLevel={100}
          zoomSnap={0.5}
          zoomDelta={0.5}
          style={{
            height: "300px",
            width: "100%",
            background: "#09090b",
          }}
        >
          <TileLayer
            url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
            maxZoom={19}
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          />

          {/* Transparent custom zoom controls */}
          <ZoomControl position="topleft" />

          {/* Received-chain geographic path */}
          {routePoints.length >= 2 && (
            <Polyline
              positions={routePoints}
              pathOptions={{
                color: "#f97316",
                weight: 3,
                opacity: 0.72,
                dashArray: "7 8",
              }}
            />
          )}

          {/* One numbered marker for every geolocatable hop */}
          {geolocatedHops.map(({ hop, originalIndex }) => {
            const hopNumber = originalIndex + 1;
            const selected = selectedHopIndex === originalIndex;

            return (
              <Marker
                key={`${hop.ip}-${originalIndex}`}
                position={[hop.geo!.lat!, hop.geo!.lon!]}
                icon={createHopIcon(hopNumber, selected)}
              >
                <Popup>
                  <HopPopup hop={hop} hopNumber={hopNumber} />
                </Popup>
              </Marker>
            );
          })}

          <FitToLocations hops={hops} />

          <FocusSelectedHop hops={hops} selectedHopIndex={selectedHopIndex} />
        </MapContainer>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap items-center gap-x-4 gap-y-2 border-t border-zinc-800 bg-zinc-950 px-3 py-2">
        <div className="flex items-center gap-2 text-[9px] uppercase tracking-wider text-zinc-500">
          <span
            className="
              flex
              h-4
              w-4
              items-center
              justify-center
              rounded-full
              border
              border-orange-200
              bg-orange-500
              text-[8px]
              font-bold
              text-white
            "
          >
            1
          </span>
          Observed Infrastructure
        </div>

        <div className="h-3 w-px bg-zinc-800" />

        <div className="flex items-center gap-2 text-[9px] text-zinc-600">
          <span className="h-px w-5 border-t-2 border-dashed border-orange-500" />
          Received-chain path
        </div>
      </div>

      {geolocatedHops.length === 0 && (
        <div className="border-t border-zinc-800 bg-zinc-950 px-3 py-2 text-[10px] text-zinc-600">
          No geolocatable mail infrastructure was found.
        </div>
      )}
    </div>
  );
}
