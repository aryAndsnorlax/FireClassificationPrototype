import { useState } from "react";
import {
  Radio,
  Clock,
  TrendingUp,
  Satellite,
  Calendar,
  AlertCircle,
  Crosshair,
} from "lucide-react";
import PageHeader from "../components/PageHeader";
import ActivityTimeline from "../components/ActivityTimeline";
import type { HotSpot } from "../types/hotSpot";
import type { NavTabId } from "../components/Navigation";

interface ActivityPageProps {
  hotspots: HotSpot[];
  selectedHotspot: HotSpot | null;
  onSelectHotspot: (hotspot: HotSpot) => void;
  onNavigate: (tab: NavTabId, hotspot?: HotSpot) => void;
}

export default function ActivityPage({
  hotspots,
  selectedHotspot,
  onSelectHotspot,
}: ActivityPageProps) {
  const [activeIncident, setActiveIncident] = useState<HotSpot>(
    selectedHotspot || hotspots[0]
  );

  const handleSelect = (h: HotSpot) => {
    setActiveIncident(h);
    onSelectHotspot(h);
  };

  return (
    <div className="portal-page-container">
      <PageHeader
        category="TEMPORAL SURVEILLANCE &amp; MONITORING"
        title="Multi-Satellite Overpass & Activity Progression"
        subtitle="Tracking multi-pass orbital persistence, thermal emission escalation trends, and chronological sensor audit trails."
        badge="ORBITAL TRACKING ACTIVE"
      />

      {/* Target Selector Strip */}
      <div className="gov-card hotspot-selector-bar">
        <div className="selector-label">
          <Crosshair size={14} />
          <span>INSPECT ORBITAL TIMELINE FOR:</span>
        </div>
        <div className="selector-pills">
          {hotspots.map((h) => {
            const isSelected = h.id === activeIncident.id;
            return (
              <button
                key={h.id}
                type="button"
                className={`selector-pill ${isSelected ? "is-selected" : ""}`}
                onClick={() => handleSelect(h)}
              >
                <span className="pill-id">{h.id}</span>
                <span className="pill-name">
                  {h.name?.split(" ")[0] || h.location_name?.split(",")[0]}
                </span>
                <span className="pill-persistence">({h.persistence}p)</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Primary Timeline Component */}
      <div className="gov-card">
        <div className="gov-card-header">
          <div className="card-header-title">
            <Radio size={16} />
            <span>
              Orbital Pass Progression: {activeIncident.id} &mdash;{" "}
              {activeIncident.name || activeIncident.location_name}
            </span>
          </div>
          <div className="card-header-meta-badge">
            Persistence: {activeIncident.persistence} Detections
          </div>
        </div>

        <ActivityTimeline hotspot={activeIncident} />
      </div>

      {/* Multi-Satellite Detection Log & Orbit Summary */}
      <div className="activity-details-grid">
        {/* Left: Orbit Overpass History */}
        <div className="gov-card">
          <div className="gov-card-header">
            <div className="card-header-title">
              <Satellite size={16} />
              <span>Sensor Orbital Ingestion Log</span>
            </div>
          </div>

          <div className="orbit-log-list">
            <div className="orbit-log-item">
              <div className="log-sat-icon">
                <Satellite size={16} />
              </div>
              <div className="log-info">
                <div className="log-sat-title">
                  <strong>VIIRS (Suomi-NPP)</strong> &bull; 375m I-Band
                </div>
                <div className="log-sat-desc">
                  Acquired daytime thermal pass over Punjab &amp; Gujarat industrial corridors. High-confidence detections confirmed.
                </div>
                <div className="log-time-meta">
                  <Calendar size={11} />
                  <span>18:40 IST &bull; 13-SEP-2026</span>
                </div>
              </div>
            </div>

            <div className="orbit-log-item">
              <div className="log-sat-icon">
                <Satellite size={16} />
              </div>
              <div className="log-info">
                <div className="log-sat-title">
                  <strong>MODIS (Terra / Aqua)</strong> &bull; 1km Thermal
                </div>
                <div className="log-sat-desc">
                  Mid-infrared 3.96&mu;m channel verification. Confirmed intense radiative signature in Dhanbad coalfields.
                </div>
                <div className="log-time-meta">
                  <Calendar size={11} />
                  <span>16:15 IST &bull; 13-SEP-2026</span>
                </div>
              </div>
            </div>

            <div className="orbit-log-item">
              <div className="log-sat-icon">
                <Satellite size={16} />
              </div>
              <div className="log-info">
                <div className="log-sat-title">
                  <strong>INSAT-3D / 3DR Imager</strong> &bull; Geostationary
                </div>
                <div className="log-sat-desc">
                  Half-hourly rapid-scan radiometric surveillance. Continuous flare monitoring over Western petrochemical clusters.
                </div>
                <div className="log-time-meta">
                  <Calendar size={11} />
                  <span>14:30 IST &bull; 13-SEP-2026</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right: Operational Persistence Intelligence */}
        <div className="gov-card">
          <div className="gov-card-header">
            <div className="card-header-title">
              <TrendingUp size={16} />
              <span>Persistence &amp; Temporal Dynamics</span>
            </div>
          </div>

          <div className="persistence-insights">
            <div className="insight-block">
              <div className="insight-title">
                <Clock size={14} className="text-navy" />
                <span>Multi-Pass Temporal Verification</span>
              </div>
              <p className="insight-text">
                Transient thermal blips (e.g., highly reflective metal roofs, solar reflection) typically register only in a single overpass. Sustained detections across 3 or more satellite cycles reliably confirm an active heat source.
              </p>
            </div>

            <div className="insight-block">
              <div className="insight-title">
                <AlertCircle size={14} className="text-danger" />
                <span>Thermal Escalation Warning Criteria</span>
              </div>
              <p className="insight-text">
                When Fire Radiative Power increases by &gt;30% between successive overpasses within 6 hours, the system raises the incident severity score to alert emergency response teams.
              </p>
            </div>

            <div className="insight-stat-box">
              <div className="stat-row">
                <span>Mean Revisit Cadence:</span>
                <strong>~3.5 Hours</strong>
              </div>
              <div className="stat-row">
                <span>Active Target Persistence Average:</span>
                <strong>
                  {(
                    hotspots.reduce((acc, h) => acc + h.persistence, 0) /
                    hotspots.length
                  ).toFixed(1)}{" "}
                  Passes
                </strong>
              </div>
              <div className="stat-row">
                <span>Sustained Targets (&ge;10 Passes):</span>
                <strong>
                  {hotspots.filter((h) => h.persistence >= 10).length} Hotspots
                </strong>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Classification Distribution Breakdown (Phase 8) */}
      <div className="gov-card" style={{ marginTop: "20px" }}>
        <div className="gov-card-header">
          <div className="card-header-title">
            <Radio size={16} />
            <span>Active Incident Classification Distribution</span>
          </div>
          <div className="card-header-meta-badge">
            {hotspots.length} Verified Signatures
          </div>
        </div>
        <div style={{ padding: "16px" }}>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
              gap: "12px",
            }}
          >
            {(
              [
                "industrial_fire",
                "persistent_industrial",
                "coal_seam_fire",
                "agricultural_burning",
                "wildfire",
              ] as const
            ).map((cls) => {
              const count = hotspots.filter((h) => h.classification === cls).length;
              const pct = hotspots.length > 0 ? Math.round((count / hotspots.length) * 100) : 0;
              const colorMap: Record<string, string> = {
                industrial_fire: "#D32F2F",
                persistent_industrial: "#E65100",
                coal_seam_fire: "#795548",
                agricultural_burning: "#F9A825",
                wildfire: "#C62828",
              };
              const labelMap: Record<string, string> = {
                industrial_fire: "Industrial Fire",
                persistent_industrial: "Persistent Industrial",
                coal_seam_fire: "Coal Seam Fire",
                agricultural_burning: "Agricultural Burning",
                wildfire: "Wildfire",
              };
              return (
                <div
                  key={cls}
                  style={{
                    border: "1px solid #e2e8f0",
                    borderRadius: "4px",
                    padding: "12px",
                    backgroundColor: "#f8fafc",
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      marginBottom: "6px",
                    }}
                  >
                    <span
                      style={{
                        fontSize: "12px",
                        fontWeight: 700,
                        color: colorMap[cls],
                      }}
                    >
                      {labelMap[cls]}
                    </span>
                    <span
                      style={{
                        fontSize: "13px",
                        fontWeight: 800,
                        color: "#1e293b",
                      }}
                    >
                      {count} ({pct}%)
                    </span>
                  </div>
                  <div
                    style={{
                      width: "100%",
                      height: "6px",
                      backgroundColor: "#e2e8f0",
                      borderRadius: "3px",
                      overflow: "hidden",
                    }}
                  >
                    <div
                      style={{
                        width: `${pct}%`,
                        height: "100%",
                        backgroundColor: colorMap[cls],
                        borderRadius: "3px",
                        transition: "width 0.3s ease",
                      }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
