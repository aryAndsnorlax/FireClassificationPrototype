import { useEffect } from "react";
import {
  MapContainer,
  TileLayer,
  CircleMarker,
  Popup,
  Tooltip,
  useMap,
} from "react-leaflet";
import { Maximize2, Layers } from "lucide-react";
import { CLASS_COLORS, CLASS_LABELS, FIRE_CLASSES } from "../data/fireClasses";
import type { HotSpot } from "../types/hotSpot";

interface FireMapProps {
  hotspots: HotSpot[];
  selectedHotspot: HotSpot | null;
  onSelectHotspot: (hotspot: HotSpot) => void;
  onViewAnalysis?: (hotspot: HotSpot) => void;
  height?: string | number;
}

const INDIA_CENTER: [number, number] = [22.5, 79.5];
const DEFAULT_ZOOM = 5;

// Component to smoothly pan and zoom to target hotspot when selected
function MapRecenter({ target }: { target: [number, number] | null }) {
  const map = useMap();
  useEffect(() => {
    if (target) {
      map.flyTo(target, 8, { duration: 1.2 });
    }
  }, [target, map]);
  return null;
}

// Reset button to return to whole-India view
function MapControls() {
  const map = useMap();
  const handleReset = () => {
    map.flyTo(INDIA_CENTER, DEFAULT_ZOOM, { duration: 1 });
  };

  return (
    <div className="map-gis-controls">
      <button
        type="button"
        className="map-gis-btn"
        onClick={handleReset}
        title="Reset map view to India"
      >
        <Maximize2 size={14} />
        <span>Fit India View</span>
      </button>
    </div>
  );
}

export default function FireMap({
  hotspots,
  selectedHotspot,
  onSelectHotspot,
  onViewAnalysis,
  height = "520px",
}: FireMapProps) {
  const recenterTarget: [number, number] | null = selectedHotspot
    ? [selectedHotspot.latitude, selectedHotspot.longitude]
    : null;

  return (
    <div
      className="fire-map-wrapper"
      style={{ height }}
      aria-label-label="AgniNetra GIS Hotspot Map"
    >
      {/* GIS Bar Top */}
      <div className="map-gis-header">
        <div className="gis-header-left">
          <Layers size={14} className="gis-icon" />
          <span className="gis-title">
            TERRESTRIAL THERMAL SATELLITE OVERLAY (NASA FIRMS / MODIS / VIIRS)
          </span>
        </div>
        <div className="gis-header-right">
          <span className="gis-counter-label">PLOTTED HOTSPOTS:</span>
          <span className="gis-counter-value">{hotspots.length}</span>
        </div>
      </div>

      <MapContainer
        center={INDIA_CENTER}
        zoom={DEFAULT_ZOOM}
        minZoom={4}
        maxZoom={16}
        scrollWheelZoom={true}
        className="leaflet-gis-root"
      >
        {/* OpenStreetMap Standard Basemap */}
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          maxZoom={19}
        />

        <MapRecenter target={recenterTarget} />
        <MapControls />

        {hotspots.map((hotspot) => {
          const isSelected = selectedHotspot?.id === hotspot.id;
          const color =
            CLASS_COLORS[hotspot.classification] || CLASS_COLORS.unknown;
          const isCritical = hotspot.risk_score >= 0.85;

          // Dynamic radius scaled to thermal FRP
          const baseRadius = Math.max(7, Math.min(16, hotspot.frp / 6));
          const radius = isSelected ? baseRadius + 4 : baseRadius;

          return (
            <CircleMarker
              key={hotspot.id}
              center={[hotspot.latitude, hotspot.longitude]}
              radius={radius}
              pathOptions={{
                fillColor: color,
                fillOpacity: isSelected ? 0.95 : 0.82,
                color: isSelected ? "#000080" : isCritical ? "#D32F2F" : "#333333",
                weight: isSelected ? 3 : isCritical ? 2 : 1,
              }}
              eventHandlers={{
                click: () => onSelectHotspot(hotspot),
              }}
            >
              <Tooltip
                direction="top"
                offset={[0, -10]}
                opacity={0.96}
                className="gis-tooltip"
              >
                <div>
                  <strong>{hotspot.id}</strong> —{" "}
                  {CLASS_LABELS[hotspot.classification]}
                  <br />
                  <span style={{ color: isCritical ? "#D32F2F" : "#333333" }}>
                    FRP: {hotspot.frp.toFixed(1)} MW | Risk:{" "}
                    {Math.round(hotspot.risk_score * 100)}%
                  </span>
                </div>
              </Tooltip>

              <Popup className="gis-popup">
                <div className="popup-gis-card">
                  <div className="popup-gis-header">
                    <span className="popup-gis-id">{hotspot.id}</span>
                    <span
                      className="popup-gis-class"
                      style={{
                        backgroundColor: `${color}18`,
                        color,
                        borderColor: color,
                      }}
                    >
                      {CLASS_LABELS[hotspot.classification]}
                    </span>
                  </div>

                  <div className="popup-gis-name">
                    {hotspot.name ||
                      hotspot.location_name ||
                      `${hotspot.latitude.toFixed(4)}°N, ${hotspot.longitude.toFixed(4)}°E`}
                  </div>

                  <div className="popup-gis-grid">
                    <div className="popup-metric">
                      <span className="p-label">THERMAL POWER</span>
                      <span className="p-val">{hotspot.frp.toFixed(1)} MW</span>
                    </div>
                    <div className="popup-metric">
                      <span className="p-label">RISK SCORE</span>
                      <span
                        className="p-val"
                        style={{
                          color: isCritical ? "#D32F2F" : "#E65100",
                          fontWeight: 700,
                        }}
                      >
                        {Math.round(hotspot.risk_score * 100)}%
                      </span>
                    </div>
                    <div className="popup-metric">
                      <span className="p-label">CONFIDENCE</span>
                      <span className="p-val">{hotspot.confidence}%</span>
                    </div>
                    <div className="popup-metric">
                      <span className="p-label">BRIGHTNESS</span>
                      <span className="p-val">{hotspot.brightness.toFixed(1)} K</span>
                    </div>
                    <div className="popup-metric">
                      <span className="p-label">FACILITY DIST.</span>
                      <span className="p-val">
                        {hotspot.facility_distance_km < 1
                          ? `${(hotspot.facility_distance_km * 1000).toFixed(0)} m`
                          : `${hotspot.facility_distance_km.toFixed(1)} km`}
                      </span>
                    </div>
                    <div className="popup-metric">
                      <span className="p-label">PERSISTENCE</span>
                      <span className="p-val">{hotspot.persistence} passes</span>
                    </div>
                    <div className="popup-metric">
                      <span className="p-label">ANOMALY SPIKE</span>
                      <span
                        className="p-val"
                        style={{
                          color: hotspot.is_anomaly ? "#D32F2F" : "#138808",
                          fontWeight: 700,
                        }}
                      >
                        {hotspot.is_anomaly ? "YES (Spike)" : "NO (Nominal)"}
                      </span>
                    </div>
                    <div className="popup-metric">
                      <span className="p-label">ACQUISITION</span>
                      <span className="p-val">
                        {new Date(hotspot.timestamp).toLocaleTimeString("en-GB", {
                          hour: "2-digit",
                          minute: "2-digit",
                          timeZone: "Asia/Kolkata",
                        })}{" "}
                        IST
                      </span>
                    </div>
                  </div>

                  <div className="popup-footer-row">
                    <button
                      type="button"
                      className="popup-select-btn"
                      onClick={() => {
                        onSelectHotspot(hotspot);
                        if (onViewAnalysis) {
                          onViewAnalysis(hotspot);
                        }
                      }}
                    >
                      Inspect Dossier &amp; Analysis &rarr;
                    </button>
                  </div>
                </div>
              </Popup>
            </CircleMarker>
          );
        })}
      </MapContainer>

      {/* Institutional Legend */}
      <div className="map-gis-legend">
        <div className="legend-title">CLASSIFICATION LEGEND</div>
        <div className="legend-items">
          {FIRE_CLASSES.map((cls) => (
            <div key={cls} className="legend-item">
              <span
                className="legend-dot"
                style={{ backgroundColor: CLASS_COLORS[cls] }}
              />
              <span className="legend-text">{CLASS_LABELS[cls]}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
