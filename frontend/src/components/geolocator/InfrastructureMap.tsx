import { useEffect, useMemo, useState } from "react";
import { MapContainer, Marker, Polyline, TileLayer, Tooltip, useMap } from "react-leaflet";
import { divIcon, latLngBounds } from "leaflet";
import "leaflet/dist/leaflet.css";
import "./infrastructure-map.css";
import { coordinates, verdictVisuals } from "@/lib/infrastructure";
import type { ReputationVerdict } from "@/types/analysis";
import type { InfrastructureObservation, InfrastructureRouteSegment } from "@/types/infrastructure";

function Viewport({ records }: { records: InfrastructureObservation[] }) {
  const map = useMap();
  useEffect(() => {
    const points = records.flatMap((record) => {
      const point = coordinates(record);
      return point ? [point] : [];
    });
    const fit = () => {
      map.invalidateSize({ animate: false });
      if (points.length)
        map.fitBounds(latLngBounds(points), { padding: [36, 36], maxZoom: 7, animate: false });
      else map.setView([20, 10], 1, { animate: false });
    };
    fit();
    const observer = new ResizeObserver(fit);
    observer.observe(map.getContainer());
    return () => observer.disconnect();
  }, [map, records]);
  return null;
}

function markerIcon(verdict: ReputationVerdict, selected: boolean, demo: boolean) {
  const visual = verdictVisuals[verdict];
  const size = selected ? 48 : 40;
  return divIcon({
    className: "sentinel-map-marker-shell",
    html: `<span class="sentinel-map-marker${selected ? " is-selected" : ""}${demo ? " is-demo" : ""}" style="--marker-color:${visual.color};--marker-glow:${visual.glow}" aria-hidden="true"><span class="sentinel-map-marker-ring"></span><span class="sentinel-map-marker-core"></span></span>`,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
  });
}

export default function InfrastructureMap({
  records,
  segments,
  selectedId,
  onSelect,
}: {
  records: InfrastructureObservation[];
  segments: InfrastructureRouteSegment[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}) {
  const [tileError, setTileError] = useState(false);
  const byId = useMemo(() => new Map(records.map((record) => [record.id, record])), [records]);
  return (
    <div
      className="sentinel-infrastructure-map relative isolate overflow-hidden rounded-sm border border-network/25"
      aria-label="Observed infrastructure map"
    >
      <MapContainer
        center={[20, 10]}
        zoom={2}
        minZoom={0}
        maxZoom={18}
        scrollWheelZoom={false}
        className="z-0 h-[420px] w-full bg-[#050909] sm:h-[540px]"
        attributionControl
      >
        <TileLayer
          url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          className="sentinel-dark-map-tiles"
          eventHandlers={{ tileerror: () => setTileError(true) }}
        />
        <Viewport records={records} />
        {segments.map((segment) => {
          const start = byId.get(segment.from_observation_id);
          const end = byId.get(segment.to_observation_id);
          const a = start && coordinates(start);
          const b = end && coordinates(end);
          if (!a || !b) return null;
          return (
            <Polyline
              key={`${start.id}-${end.id}`}
              positions={[a, b]}
              pathOptions={{
                color: "#4de8e5",
                weight: 2,
                opacity: 0.8,
                dashArray: "5 7",
                className: "sentinel-routing-line",
              }}
            >
              <Tooltip>
                Observed Mail Routing · {segment.from_timestamp} → {segment.to_timestamp}
                {start.demo || end.demo ? " · Includes simulated location" : ""}
              </Tooltip>
            </Polyline>
          );
        })}
        {records.map((record) => {
          const point = coordinates(record);
          if (!point) return null;
          return (
            <Marker
              key={record.id}
              position={point}
              icon={markerIcon(record.verdict, record.id === selectedId, record.demo)}
              eventHandlers={{ click: () => onSelect(record.id) }}
            >
              <Tooltip>
                {record.ip_address} · {record.verdict}
                {record.demo ? " · SIMULATED" : ""}
              </Tooltip>
            </Marker>
          );
        })}
      </MapContainer>
      <div className="sentinel-map-legend" aria-label="Threat reputation legend">
        <p>Threat Reputation</p>
        <div>
          {(
            Object.entries(verdictVisuals) as [
              ReputationVerdict,
              (typeof verdictVisuals)[ReputationVerdict],
            ][]
          ).map(([verdict, visual]) => (
            <span key={verdict}>
              <i
                style={
                  {
                    "--legend-color": visual.color,
                    "--legend-glow": visual.glow,
                  } as React.CSSProperties
                }
              />
              {verdict[0] + verdict.slice(1).toLowerCase()}
            </span>
          ))}
        </div>
      </div>
      {tileError && (
        <p
          role="status"
          className="border-t border-border bg-surface px-4 py-2 text-xs text-warning"
        >
          Some map tiles could not load. Persisted observations remain available in the list below.
        </p>
      )}
    </div>
  );
}
