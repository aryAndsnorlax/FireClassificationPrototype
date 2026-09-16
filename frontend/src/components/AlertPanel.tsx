import { useState } from "react";
import {
  AlertTriangle,
  Flame,
  ShieldCheck,
  Clock,
  Crosshair,
  Factory,
  Share2,
  CheckCircle2,
  ExternalLink,
} from "lucide-react";
import { CLASS_LABELS, getRiskBadge, CLASS_COLORS } from "../data/fireClasses";
import type { HotSpot } from "../types/hotSpot";

interface AlertPanelProps {
  hotspot: HotSpot | null;
  onCenterMap?: () => void;
  onViewAnalysis?: (hotspot: HotSpot) => void;
}

export default function AlertPanel({
  hotspot,
  onCenterMap,
  onViewAnalysis,
}: AlertPanelProps) {
  const [dispatching, setDispatching] = useState(false);
  const [dispatched, setDispatched] = useState(false);

  if (!hotspot) {
    return (
      <aside className="institutional-panel empty" aria-label="Incident Summary">
        <div className="panel-empty-state">
          <Crosshair size={32} className="empty-icon" />
          <h3>No Incident Selected</h3>
          <p>
            Select a hotspot from the map or incident table to review operational telemetry and risk factors.
          </p>
        </div>
      </aside>
    );
  }

  const riskBadge = getRiskBadge(hotspot.risk_score);
  const classColor = CLASS_COLORS[hotspot.classification] || "#757575";

  const handleDispatch = () => {
    setDispatching(true);
    setTimeout(() => {
      setDispatching(false);
      setDispatched(true);
    }, 700);
  };

  return (
    <aside className="institutional-panel" aria-label="Incident Summary Panel">
      {/* Top Banner Status */}
      <div className="panel-header-strip">
        <div className="badge-group">
          <span
            className="institutional-risk-tag"
            style={{
              color: riskBadge.color,
              backgroundColor: riskBadge.bg,
              borderColor: riskBadge.borderColor,
            }}
          >
            <AlertTriangle size={13} />
            {riskBadge.label}
          </span>

          {hotspot.is_anomaly && (
            <span className="institutional-anomaly-tag">STATISTICAL ANOMALY</span>
          )}
        </div>

        <span className="incident-id-tag">REF: {hotspot.id}</span>
      </div>

      {/* Main Target Header */}
      <div className="incident-main-info">
        <div className="class-row">
          <span
            className="class-color-indicator"
            style={{ backgroundColor: classColor }}
          />
          <h2 className="incident-class-title">
            {CLASS_LABELS[hotspot.classification]}
          </h2>
        </div>

        <div className="incident-location-title">
          {hotspot.name ||
            hotspot.location_name ||
            `${hotspot.latitude.toFixed(4)}° N, ${hotspot.longitude.toFixed(4)}° E`}
        </div>

        <div className="incident-coords">
          <Crosshair size={12} />
          <span>
            {hotspot.latitude.toFixed(4)}° N, {hotspot.longitude.toFixed(4)}° E
          </span>
        </div>
      </div>

      {/* Telemetry Metrics */}
      <div className="incident-telemetry-grid">
        <div className="telemetry-cell">
          <div className="cell-label">
            <ShieldCheck size={12} />
            <span>CONFIDENCE</span>
          </div>
          <div className="cell-val">{hotspot.confidence}%</div>
          <div className="cell-track">
            <div
              className="cell-track-fill"
              style={{
                width: `${hotspot.confidence}%`,
                backgroundColor: "#138808",
              }}
            />
          </div>
        </div>

        <div className="telemetry-cell">
          <div className="cell-label">
            <Flame size={12} />
            <span>THERMAL INTENSITY (FRP)</span>
          </div>
          <div className="cell-val highlight">{hotspot.frp.toFixed(1)} MW</div>
          <div className="cell-track">
            <div
              className="cell-track-fill"
              style={{
                width: `${Math.min(100, (hotspot.frp / 100) * 100)}%`,
                backgroundColor: "#D32F2F",
              }}
            />
          </div>
        </div>

        <div className="telemetry-cell">
          <div className="cell-label">
            <Factory size={12} />
            <span>FACILITY DISTANCE</span>
          </div>
          <div className="cell-val">
            {hotspot.facility_distance_km < 1
              ? `${(hotspot.facility_distance_km * 1000).toFixed(0)} m`
              : `${hotspot.facility_distance_km.toFixed(1)} km`}
          </div>
          <div className="cell-sub">{hotspot.facility_type || "Asset Buffer"}</div>
        </div>

        <div className="telemetry-cell">
          <div className="cell-label">
            <Clock size={12} />
            <span>PERSISTENCE</span>
          </div>
          <div className="cell-val">{hotspot.persistence} Detections</div>
          <div className="cell-sub">Multi-pass orbital cycle</div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="incident-action-container">
        {onViewAnalysis && (
          <button
            type="button"
            className="action-btn-primary"
            onClick={() => onViewAnalysis(hotspot)}
          >
            <ExternalLink size={14} />
            <span>Open Detailed Hotspot Analysis</span>
          </button>
        )}

        <button
          type="button"
          className={`dispatch-alert-btn ${dispatched ? "is-dispatched" : ""}`}
          onClick={handleDispatch}
          disabled={dispatching}
        >
          {dispatched ? (
            <>
              <CheckCircle2 size={15} />
              <span>INCIDENT LOGGED &amp; DISPATCHED</span>
            </>
          ) : dispatching ? (
            <span>GENERATING ADVISORY...</span>
          ) : (
            <>
              <AlertTriangle size={15} />
              <span>LOG INCIDENT BULLETIN</span>
            </>
          )}
        </button>

        <div className="action-button-row">
          {onCenterMap && (
            <button
              type="button"
              className="action-btn-secondary"
              onClick={onCenterMap}
            >
              <Crosshair size={13} />
              <span>Center on Map</span>
            </button>
          )}
          <button
            type="button"
            className="action-btn-secondary"
            onClick={() =>
              alert(`Institutional Incident Brief for ${hotspot.id} prepared.`)
            }
          >
            <Share2 size={13} />
            <span>Export Brief</span>
          </button>
        </div>
      </div>
    </aside>
  );
}
