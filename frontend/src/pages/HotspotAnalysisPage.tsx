import {
  Crosshair,
  MapPin,
  Flame,
  Shield,
  Factory,
  Clock,
  Zap,
  Map,
  Thermometer,
  FileCheck,
} from "lucide-react";
import PageHeader from "../components/PageHeader";
import RiskExplanation from "../components/RiskExplanation";
import PipelineSimulator from "../components/PipelineSimulator";
import { updateHotspotTelemetry } from "../services/api";
import { CLASS_LABELS, CLASS_COLORS, getRiskBadge } from "../data/fireClasses";
import type { HotSpot } from "../types/hotSpot";
import type { NavTabId } from "../components/Navigation";

interface HotspotAnalysisPageProps {
  hotspots: HotSpot[];
  selectedHotspot: HotSpot | null;
  onSelectHotspot: (hotspot: HotSpot) => void;
  onNavigate: (tab: NavTabId, hotspot?: HotSpot) => void;
}

export default function HotspotAnalysisPage({
  hotspots,
  selectedHotspot,
  onSelectHotspot,
  onNavigate,
}: HotspotAnalysisPageProps) {
  // If no hotspot selected, default to highest risk hotspot
  const activeHotspot =
    selectedHotspot ||
    [...hotspots].sort((a, b) => b.risk_score - a.risk_score)[0] ||
    null;

  if (!activeHotspot) {
    return (
      <div className="portal-page-container">
        <PageHeader
          category="INCIDENT DIAGNOSTICS &amp; ATTRIBUTION"
          title="Hotspot Risk Analysis"
          subtitle="Select a hotspot to examine sensor telemetry and attribution metrics."
        />
        <div className="gov-card p-4">No hotspot data available.</div>
      </div>
    );
  }

  const riskBadge = getRiskBadge(activeHotspot.risk_score);
  const classColor = CLASS_COLORS[activeHotspot.classification];
  const dateStr = new Date(activeHotspot.timestamp).toLocaleString("en-GB", {
    day: "2-digit",
    month: "long",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "Asia/Kolkata",
  });

  return (
    <div className="portal-page-container">
      <PageHeader
        category="Incident Details &amp; Attribution"
        title={`Incident Technical Dossier — ${activeHotspot.id}`}
        subtitle="Multi-sensor satellite measurements, nearby facility distances, and explainable risk attribution."
        badge={riskBadge.label}
        actions={
          <button
            type="button"
            className="gov-action-btn primary"
            onClick={() => onNavigate("map", activeHotspot)}
          >
            <Map size={14} />
            <span>Locate on Map</span>
          </button>
        }
      />

      {/* Quick Hotspot Selector Bar */}
      <div className="gov-card hotspot-selector-bar">
        <div className="selector-label">
          <Crosshair size={15} />
          <span>Select Incident:</span>
        </div>
        <div className="selector-pills">
          {hotspots.map((h) => {
            const isSelected = h.id === activeHotspot.id;
            const hBadge = getRiskBadge(h.risk_score);
            return (
              <button
                key={h.id}
                type="button"
                className={`selector-pill ${isSelected ? "is-selected" : ""}`}
                onClick={() => onSelectHotspot(h)}
              >
                <span
                  className="pill-dot"
                  style={{ backgroundColor: hBadge.color }}
                />
                <span className="pill-id">{h.id}</span>
                <span className="pill-name">
                  {h.name?.split(" ")[0] || h.location_name?.split(",")[0]}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Overview Metadata Card */}
      <div className="gov-card dossier-summary-card">
        <div className="dossier-main-row">
          <div className="dossier-id-block">
            <span className="dossier-ref-label">Incident ID</span>
            <h2 className="dossier-id-text">{activeHotspot.id}</h2>
            <div className="dossier-time-stamp">
              <Clock size={13} />
              <span>Detected: {dateStr} IST</span>
            </div>
          </div>

          <div className="dossier-location-block">
            <span className="dossier-ref-label">Location / Plant</span>
            <h3 className="dossier-location-title">
              {activeHotspot.name || activeHotspot.location_name}
            </h3>
            <div className="dossier-coords">
              <MapPin size={13} />
              <span>
                {activeHotspot.latitude.toFixed(4)}° N,{" "}
                {activeHotspot.longitude.toFixed(4)}° E &bull;{" "}
                {activeHotspot.location_name || "India"}
              </span>
            </div>
          </div>

          <div className="dossier-classification-block">
            <span className="dossier-ref-label">Classification</span>
            <div>
              <span
                className="dossier-class-badge"
                style={{
                  backgroundColor: `${classColor}15`,
                  color: classColor,
                  borderColor: classColor,
                }}
              >
                <span
                  className="class-dot"
                  style={{ backgroundColor: classColor }}
                />
                {CLASS_LABELS[activeHotspot.classification]}
              </span>
            </div>
            <div className="dossier-sub-type">
              {activeHotspot.facility_type || "Terrestrial Target"}
            </div>
          </div>

          <div className="dossier-risk-block">
            <span className="dossier-ref-label">Risk Priority</span>
            <div
              className="dossier-risk-score"
              style={{ color: riskBadge.color }}
            >
              {Math.round(activeHotspot.risk_score * 100)}%
            </div>
            <span
              className="dossier-risk-tag"
              style={{
                color: riskBadge.color,
                backgroundColor: riskBadge.bg,
                borderColor: riskBadge.borderColor,
              }}
            >
              {riskBadge.label}
            </span>
          </div>
        </div>

        {/* Technical Telemetry 6-Tile Grid */}
        <div className="dossier-telemetry-grid">
          <div className="telemetry-box">
            <div className="telemetry-box-label">
              <Flame size={15} style={{ color: "#ea580c" }} />
              <span>Heat Output (FRP)</span>
            </div>
            <div className="telemetry-box-value">
              {activeHotspot.frp.toFixed(1)} <span className="unit">MW</span>
            </div>
            <div className="telemetry-box-note">
              Fire Radiative Power
            </div>
          </div>

          <div className="telemetry-box">
            <div className="telemetry-box-label">
              <Thermometer size={15} style={{ color: "#dc2626" }} />
              <span>Brightness Temp</span>
            </div>
            <div className="telemetry-box-value">
              {activeHotspot.brightness.toFixed(1)} <span className="unit">K</span>
            </div>
            <div className="telemetry-box-note">
              Thermal sensor channel
            </div>
          </div>

          <div className="telemetry-box">
            <div className="telemetry-box-label">
              <Shield size={15} style={{ color: "#16a34a" }} />
              <span>Confidence</span>
            </div>
            <div className="telemetry-box-value">
              {activeHotspot.confidence} <span className="unit">%</span>
            </div>
            <div className="telemetry-box-note">
              Algorithm certainty score
            </div>
          </div>

          <div className="telemetry-box">
            <div className="telemetry-box-label">
              <Factory size={15} style={{ color: "#002147" }} />
              <span>Facility Distance</span>
            </div>
            <div className="telemetry-box-value">
              {activeHotspot.facility_distance_km < 1
                ? `${(activeHotspot.facility_distance_km * 1000).toFixed(0)} m`
                : `${activeHotspot.facility_distance_km.toFixed(1)} km`}
            </div>
            <div className="telemetry-box-note">
              Nearest registered asset
            </div>
          </div>

          <div className="telemetry-box">
            <div className="telemetry-box-label">
              <Clock size={15} style={{ color: "#1d4ed8" }} />
              <span>Satellite Passes</span>
            </div>
            <div className="telemetry-box-value">
              {activeHotspot.persistence} <span className="unit">Passes</span>
            </div>
            <div className="telemetry-box-note">
              Confirmed orbital visits
            </div>
          </div>

          <div className="telemetry-box">
            <div className="telemetry-box-label">
              <Zap size={15} style={{ color: "#d97706" }} />
              <span>Anomaly Status</span>
            </div>
            <div className="telemetry-box-value">
              {activeHotspot.is_anomaly ? (
                <span className="anomaly-yes">Surge Detected</span>
              ) : (
                <span className="anomaly-no">Normal Baseline</span>
              )}
            </div>
            <div className="telemetry-box-note">
              Historical tile average
            </div>
          </div>
        </div>
      </div>

      {/* Explainable Risk Assessment Section */}
      <RiskExplanation hotspot={activeHotspot} />

      {/* Facility & Environmental Context Card */}
      <div className="gov-card context-info-card">
        <div className="gov-card-header">
          <div className="card-header-title">
            <FileCheck size={16} />
            <span>Facility Buffer &amp; Environmental Land-Use Context</span>
          </div>
        </div>

        <div className="context-content-grid">
          <div className="context-item">
            <span className="ctx-label">Associated Facility:</span>
            <strong className="ctx-val">
              {activeHotspot.facility_type || "Industrial Asset Buffer"}
            </strong>
          </div>
          <div className="context-item">
            <span className="ctx-label">Zoning Classification:</span>
            <strong className="ctx-val">
              {activeHotspot.classification === "industrial_fire" ||
              activeHotspot.classification === "persistent_industrial"
                ? "Industrial / Petrochemical Cluster"
                : activeHotspot.classification === "coal_seam_fire"
                ? "Mining & Extraction Zone"
                : activeHotspot.classification === "agricultural_burning"
                ? "Rural Agricultural Holding"
                : "Forest & Ecological Reserve"}
            </strong>
          </div>
          <div className="context-item">
            <span className="ctx-label">Proximity Buffer Zone:</span>
            <strong className="ctx-val">
              {activeHotspot.facility_distance_km <= 0.5
                ? "Zone 1 — Immediate Perimeter (< 500m)"
                : activeHotspot.facility_distance_km <= 2.0
                ? "Zone 2 — Secondary Risk Boundary (< 2 km)"
                : "Zone 3 — Rural / Isolated (> 2 km)"}
            </strong>
          </div>
          <div className="context-item">
            <span className="ctx-label">Demonstration Status:</span>
            <strong className="ctx-val">
              Deterministic Rule Assessment (Mock Dataset)
            </strong>
          </div>
        </div>
      </div>

      {/* Interactive Feature & Rule Classification Simulator Lab */}
      <div style={{ marginTop: "20px" }}>
        <PipelineSimulator
          hotspot={activeHotspot}
          onApplyToHotspot={(updates) => {
            updateHotspotTelemetry(activeHotspot.id, updates);
            onSelectHotspot({ ...activeHotspot, ...updates });
          }}
        />
      </div>
    </div>
  );
}
