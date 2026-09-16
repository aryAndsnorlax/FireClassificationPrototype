import { useMemo, useState } from "react";
import {
  Map,
  BellRing,
  Crosshair,
  Activity,
  ArrowRight,
  ShieldAlert,
  Radio,
  FileText,
  AlertTriangle,
  Satellite,
  Zap,
  RotateCcw,
} from "lucide-react";
import OverviewStats from "../components/Overviewstats";
import FireMap from "../components/FireMap";
import PageHeader from "../components/PageHeader";
import {
  simulateSatellitePass,
  injectSpikeAnomaly,
  resetSimulation,
} from "../services/api";
import { CLASS_LABELS, CLASS_COLORS, getRiskBadge } from "../data/fireClasses";
import type { HotSpot } from "../types/hotSpot";
import type { NavTabId } from "../components/Navigation";

interface DashboardProps {
  hotspots: HotSpot[];
  selectedHotspot: HotSpot | null;
  onSelectHotspot: (hotspot: HotSpot) => void;
  onNavigate: (tab: NavTabId, hotspot?: HotSpot) => void;
}

export default function Dashboard({
  hotspots,
  selectedHotspot,
  onSelectHotspot,
  onNavigate,
}: DashboardProps) {
  const [simNotice, setSimNotice] = useState<string | null>(null);

  const handleSimPass = () => {
    simulateSatellitePass();
    setSimNotice("Simulated VIIRS (NOAA-20 375m) overpass: telemetry timestamps and multi-pass persistence incremented.");
    setTimeout(() => setSimNotice(null), 6000);
  };

  const handleInjectSpike = () => {
    injectSpikeAnomaly("HOT-002");
    setSimNotice("Injected industrial anomaly spike at Jamnagar Refinery (FRP ratio surged to 3.85x baseline, emergency alert triggered).");
    setTimeout(() => setSimNotice(null), 6000);
  };

  const handleReset = () => {
    resetSimulation();
    setSimNotice("Telemetry database restored to nominal baseline status.");
    setTimeout(() => setSimNotice(null), 5000);
  };
  // Top 4 critical / high-priority alerts
  const priorityAlerts = useMemo(() => {
    return [...hotspots]
      .sort((a, b) => b.risk_score - a.risk_score)
      .slice(0, 4);
  }, [hotspots]);

  const highRiskCount = hotspots.filter((h) => h.risk_score >= 0.85).length;

  return (
    <div className="portal-page-container">
      {/* Page Title Banner */}
      <PageHeader
        category="National Surveillance Overview"
        title="National Industrial Fire & Thermal Intelligence"
        subtitle="Live satellite tracking of active fires, industrial heat sources, and priority alerts across India."
        badge={
          highRiskCount > 0
            ? `${highRiskCount} Priority Alert${highRiskCount > 1 ? "s" : ""}`
            : "Normal Status"
        }
        actions={
          <div className="header-quick-actions">
            <button
              type="button"
              className="gov-action-btn primary"
              onClick={() => onNavigate("map")}
            >
              <Map size={14} />
              <span>Full GIS Map</span>
            </button>
            <button
              type="button"
              className="gov-action-btn"
              onClick={() => onNavigate("alerts")}
            >
              <BellRing size={14} />
              <span>Review Alerts</span>
            </button>
          </div>
        }
      />

      {/* Satellite Ingestion Simulation Control Strip */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: "12px",
          padding: "10px 16px",
          backgroundColor: "#ffffff",
          border: "1px solid #e2e8f0",
          borderRadius: "6px",
          boxShadow: "0 1px 2px rgba(0, 0, 0, 0.02)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "13px", color: "#475569" }}>
          <Radio size={15} style={{ color: "#002147" }} />
          <span>
            <strong>Active Surveillance:</strong> Tracking {hotspots.length} monitored locations across India
          </span>
        </div>

        <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
          <button
            type="button"
            className="tab-filter-btn"
            onClick={handleSimPass}
            title="Simulate a new orbital pass updating timestamps and incrementing persistence"
          >
            <Satellite size={13} />
            <span>Simulate Pass</span>
          </button>
          <button
            type="button"
            className="tab-filter-btn"
            onClick={handleInjectSpike}
            style={{ color: "#b91c1c", borderColor: "#fecaca", backgroundColor: "#fef2f2" }}
            title="Simulate a sudden heat spike at Jamnagar Refinery"
          >
            <Zap size={13} />
            <span>Test Anomaly Spike</span>
          </button>
          <button
            type="button"
            className="tab-filter-btn"
            onClick={handleReset}
            title="Restore default Indian telemetry catalog"
          >
            <RotateCcw size={13} />
            <span>Reset Data</span>
          </button>
        </div>
      </div>

      {simNotice && (
        <div
          style={{
            padding: "10px 14px",
            backgroundColor: "#EFF6FF",
            border: "1px solid #93C5FD",
            borderRadius: "4px",
            marginBottom: "16px",
            fontSize: "12px",
            color: "#1E40AF",
            display: "flex",
            alignItems: "center",
            gap: "8px",
          }}
        >
          <Activity size={14} />
          <span>{simNotice}</span>
        </div>
      )}

      {/* Dynamic Key Operational Statistics */}
      <OverviewStats hotspots={hotspots} />

      {/* Primary Dashboard Grid: Map Preview + High Priority Alerts */}
      <div className="dashboard-layout-grid">
        {/* Left Column: GIS Map Preview */}
        <div className="gov-card dashboard-map-card">
          <div className="gov-card-header">
            <div className="card-header-title">
              <Map size={16} />
              <span>Interactive Thermal Anomaly Map (India Overview)</span>
            </div>
            <button
              type="button"
              className="card-header-link"
              onClick={() => onNavigate("map")}
            >
              <span>Open Dedicated GIS &rarr;</span>
            </button>
          </div>

          <div className="card-map-wrapper">
            <FireMap
              hotspots={hotspots}
              selectedHotspot={selectedHotspot}
              onSelectHotspot={onSelectHotspot}
              onViewAnalysis={(h) => onNavigate("analysis", h)}
              height="380px"
            />
          </div>

          <div className="card-footer-strip">
            <Radio size={13} className="strip-icon" />
            <span>
              Click any thermal marker to inspect coordinates, estimated radiative power (FRP), and industrial buffer radius.
            </span>
          </div>
        </div>

        {/* Right Column: High-Priority Action Alerts Summary */}
        <div className="gov-card dashboard-alerts-card">
          <div className="gov-card-header">
            <div className="card-header-title">
              <ShieldAlert size={16} className="text-danger" />
              <span>High-Priority Incident Alerts</span>
            </div>
            <button
              type="button"
              className="card-header-link"
              onClick={() => onNavigate("alerts")}
            >
              <span>View All Alerts ({hotspots.filter((h) => h.risk_score >= 0.7).length}) &rarr;</span>
            </button>
          </div>

          <div className="priority-alerts-list">
            {priorityAlerts.map((alert) => {
              const riskBadge = getRiskBadge(alert.risk_score);
              const classColor = CLASS_COLORS[alert.classification];

              return (
                <div
                  key={alert.id}
                  className={`priority-alert-item ${
                    selectedHotspot?.id === alert.id ? "is-selected" : ""
                  }`}
                  onClick={() => onSelectHotspot(alert)}
                >
                  <div className="alert-item-top">
                    <span className="alert-id">{alert.id}</span>
                    <span
                      className="alert-risk-pill"
                      style={{
                        color: riskBadge.color,
                        backgroundColor: riskBadge.bg,
                        borderColor: riskBadge.borderColor,
                      }}
                    >
                      <AlertTriangle size={11} />
                      {Math.round(alert.risk_score * 100)}% &bull; {riskBadge.label}
                    </span>
                  </div>

                  <div className="alert-name-row">
                    <strong>{alert.name || alert.location_name}</strong>
                  </div>

                  <div className="alert-meta-row">
                    <span
                      className="alert-class-tag"
                      style={{
                        backgroundColor: `${classColor}15`,
                        color: classColor,
                      }}
                    >
                      {CLASS_LABELS[alert.classification]}
                    </span>
                    <span className="meta-text">
                      FRP: <strong>{alert.frp.toFixed(1)} MW</strong>
                    </span>
                    <span className="meta-text">
                      Buffer:{" "}
                      <strong>
                        {alert.facility_distance_km < 1
                          ? `${(alert.facility_distance_km * 1000).toFixed(0)}m`
                          : `${alert.facility_distance_km.toFixed(1)}km`}
                      </strong>
                    </span>
                  </div>

                  <div className="alert-item-footer">
                    <button
                      type="button"
                      className="alert-inspect-btn"
                      onClick={(e) => {
                        e.stopPropagation();
                        onNavigate("analysis", alert);
                      }}
                    >
                      <span>Examine Risk Factors</span>
                      <ArrowRight size={12} />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Secondary Row: Quick Nav Cards & Recent Activity Brief */}
      <div className="dashboard-bottom-grid">
        {/* Quick Nav Modules */}
        <div className="gov-card quick-nav-card">
          <div className="gov-card-header">
            <div className="card-header-title">
              <FileText size={16} />
              <span>Operational Quick Links</span>
            </div>
          </div>

          <div className="quick-links-grid">
            <div
              className="quick-link-box"
              onClick={() => onNavigate("map")}
              role="button"
              tabIndex={0}
            >
              <div className="link-icon-wrap" style={{ color: "#000080" }}>
                <Map size={22} />
              </div>
              <div className="link-text-wrap">
                <h4>Dedicated GIS Map</h4>
                <p>Full-screen thermal mapping with India-wide filters &amp; layer toggles.</p>
              </div>
              <ArrowRight size={14} className="link-arrow" />
            </div>

            <div
              className="quick-link-box"
              onClick={() => onNavigate("alerts")}
              role="button"
              tabIndex={0}
            >
              <div className="link-icon-wrap" style={{ color: "#D32F2F" }}>
                <BellRing size={22} />
              </div>
              <div className="link-text-wrap">
                <h4>Incident Triage &amp; Alerts</h4>
                <p>Filterable tabular dossier of high-risk thermal events and notifications.</p>
              </div>
              <ArrowRight size={14} className="link-arrow" />
            </div>

            <div
              className="quick-link-box"
              onClick={() => onNavigate("analysis")}
              role="button"
              tabIndex={0}
            >
              <div className="link-icon-wrap" style={{ color: "#E65100" }}>
                <Crosshair size={22} />
              </div>
              <div className="link-text-wrap">
                <h4>Hotspot Risk Analysis</h4>
                <p>Transparent explainability factors and proximity buffer diagnostics.</p>
              </div>
              <ArrowRight size={14} className="link-arrow" />
            </div>

            <div
              className="quick-link-box"
              onClick={() => onNavigate("activity")}
              role="button"
              tabIndex={0}
            >
              <div className="link-icon-wrap" style={{ color: "#138808" }}>
                <Activity size={22} />
              </div>
              <div className="link-text-wrap">
                <h4>Surveillance Activity Trend</h4>
                <p>Multi-satellite orbital pass history and chronological thermal curves.</p>
              </div>
              <ArrowRight size={14} className="link-arrow" />
            </div>
          </div>
        </div>

        {/* System Activity Bulletin */}
        <div className="gov-card activity-bulletin-card">
          <div className="gov-card-header">
            <div className="card-header-title">
              <Activity size={16} />
              <span>Surveillance Telemetry Bulletin</span>
            </div>
          </div>

          <div className="bulletin-list">
            <div className="bulletin-item">
              <span className="bulletin-dot active" />
              <div className="bulletin-text">
                <strong>VIIRS S-NPP Orbit Overpass Completed</strong>
                <p>Ingested 8 telemetry clusters over Northern and Western Industrial Corridors.</p>
                <span className="bulletin-time">18:40 IST &bull; Telemetry Feed Ingestion</span>
              </div>
            </div>

            <div className="bulletin-item">
              <span className="bulletin-dot critical" />
              <div className="bulletin-text">
                <strong>High Thermal Anomaly: Ludhiana Focal Point (HOT-001)</strong>
                <p>FRP recorded at 82.4 MW within 400m of metallurgical processing infrastructure.</p>
                <span className="bulletin-time">18:40 IST &bull; High Risk Flagged</span>
              </div>
            </div>

            <div className="bulletin-item">
              <span className="bulletin-dot info" />
              <div className="bulletin-text">
                <strong>Persistent Flare Tracked: Jamnagar Complex (HOT-002)</strong>
                <p>Confirmed ongoing industrial flare signature across 24 consecutive satellite passes.</p>
                <span className="bulletin-time">18:35 IST &bull; Persistence Confirmed</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
