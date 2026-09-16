import { useState, useMemo } from "react";
import {
  BellRing,
  ShieldAlert,
  AlertTriangle,
  Factory,
  Clock,
  Download,
  Zap,
  Info,
} from "lucide-react";
import PageHeader from "../components/PageHeader";
import HotspotTable from "../components/HotspotTable";
import type { HotSpot } from "../types/hotSpot";
import type { NavTabId } from "../components/Navigation";

interface AlertsPageProps {
  hotspots: HotSpot[];
  selectedHotspot: HotSpot | null;
  onSelectHotspot: (hotspot: HotSpot) => void;
  onNavigate: (tab: NavTabId, hotspot?: HotSpot) => void;
}

type AlertFilterTab = "all" | "high_risk" | "industrial" | "persistent" | "anomaly";

export default function AlertsPage({
  hotspots,
  selectedHotspot,
  onSelectHotspot,
  onNavigate,
}: AlertsPageProps) {
  const [activeFilterTab, setActiveFilterTab] = useState<AlertFilterTab>("all");

  const filteredAlerts = useMemo(() => {
    switch (activeFilterTab) {
      case "high_risk":
        return hotspots.filter((h) => h.risk_score >= 0.85);
      case "industrial":
        return hotspots.filter(
          (h) =>
            h.classification === "industrial_fire" ||
            h.classification === "persistent_industrial"
        );
      case "persistent":
        return hotspots.filter((h) => h.persistence >= 10);
      case "anomaly":
        return hotspots.filter((h) => h.is_anomaly);
      case "all":
      default:
        return hotspots;
    }
  }, [hotspots, activeFilterTab]);

  const highRiskCount = hotspots.filter((h) => h.risk_score >= 0.85).length;
  const industrialCount = hotspots.filter(
    (h) =>
      h.classification === "industrial_fire" ||
      h.classification === "persistent_industrial"
  ).length;
  const persistentCount = hotspots.filter((h) => h.persistence >= 10).length;
  const anomalyCount = hotspots.filter((h) => h.is_anomaly).length;

  const handleExport = () => {
    const header = "ID,Classification,Risk,FRP,Confidence,Distance,Persistence,Timestamp,Anomaly\n";
    const csvRows = filteredAlerts
      .map(
        (h) =>
          `"${h.id}","${h.classification}",${h.risk_score},${h.frp},${h.confidence},${h.facility_distance_km},${h.persistence},"${h.timestamp}",${h.is_anomaly}`
      )
      .join("\n");
    navigator.clipboard.writeText(header + csvRows);
    alert(
      `AgniNetra Incident Alert Bulletin (${filteredAlerts.length} events) copied to clipboard in CSV format.`
    );
  };

  return (
    <div className="portal-page-container">
      <PageHeader
        category="Incident Dispatch & Monitoring"
        title="Thermal Incident Alerts"
        subtitle="Priority queue of satellite-detected heat events requiring attention, facility coordination, or field verification."
        badge={`${highRiskCount} Critical Alert${highRiskCount > 1 ? "s" : ""}`}
        actions={
          <button
            type="button"
            className="gov-action-btn"
            onClick={handleExport}
          >
            <Download size={14} />
            <span>Export CSV Bulletin</span>
          </button>
        }
      />

      {/* Guide Banner */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "8px",
          padding: "10px 16px",
          backgroundColor: "#ffffff",
          border: "1px solid #e2e8f0",
          borderRadius: "6px",
          fontSize: "13px",
          color: "#475569",
          boxShadow: "0 1px 2px rgba(0, 0, 0, 0.02)",
        }}
      >
        <Info size={16} style={{ color: "#002147", flexShrink: 0 }} />
        <span>
          Showing priority thermal detections across monitored regions in India. Filter by category or select an incident to inspect details.
        </span>
      </div>

      {/* Alert Severity KPI Cards */}
      <div className="alert-kpi-grid">
        <div
          className={`alert-kpi-card ${activeFilterTab === "all" ? "is-selected" : ""}`}
          onClick={() => setActiveFilterTab("all")}
        >
          <div className="kpi-icon-row">
            <BellRing size={18} style={{ color: "#002147" }} />
            <span className="kpi-tag">Total Alerts</span>
          </div>
          <div className="kpi-number">{hotspots.length}</div>
          <div className="kpi-subtext">All active detection records</div>
        </div>

        <div
          className={`alert-kpi-card ${activeFilterTab === "high_risk" ? "is-selected" : ""}`}
          onClick={() => setActiveFilterTab("high_risk")}
        >
          <div className="kpi-icon-row">
            <ShieldAlert size={18} style={{ color: "#dc2626" }} />
            <span className="kpi-tag" style={{ color: "#dc2626" }}>High Risk</span>
          </div>
          <div className="kpi-number" style={{ color: "#dc2626" }}>{highRiskCount}</div>
          <div className="kpi-subtext">Requires immediate response</div>
        </div>

        <div
          className={`alert-kpi-card ${activeFilterTab === "industrial" ? "is-selected" : ""}`}
          onClick={() => setActiveFilterTab("industrial")}
        >
          <div className="kpi-icon-row">
            <Factory size={18} style={{ color: "#ea580c" }} />
            <span className="kpi-tag">Industrial Zones</span>
          </div>
          <div className="kpi-number">{industrialCount}</div>
          <div className="kpi-subtext">Within facility perimeters (≤ 1km)</div>
        </div>

        <div
          className={`alert-kpi-card ${activeFilterTab === "persistent" ? "is-selected" : ""}`}
          onClick={() => setActiveFilterTab("persistent")}
        >
          <div className="kpi-icon-row">
            <Clock size={18} style={{ color: "#16a34a" }} />
            <span className="kpi-tag">Persistent Flares</span>
          </div>
          <div className="kpi-number">{persistentCount}</div>
          <div className="kpi-subtext">Repeated passes (≥ 10 visits)</div>
        </div>

        <div
          className={`alert-kpi-card ${activeFilterTab === "anomaly" ? "is-selected" : ""}`}
          onClick={() => setActiveFilterTab("anomaly")}
        >
          <div className="kpi-icon-row">
            <Zap size={18} style={{ color: "#b91c1c" }} />
            <span className="kpi-tag" style={{ color: "#b91c1c" }}>Heat Spikes</span>
          </div>
          <div className="kpi-number" style={{ color: "#b91c1c" }}>{anomalyCount}</div>
          <div className="kpi-subtext">Sudden surge above baseline</div>
        </div>
      </div>

      {/* Filter Tabs & Data Table */}
      <div className="gov-card">
        <div className="gov-card-header">
          <div className="filter-tab-buttons">
            <button
              type="button"
              className={`tab-filter-btn ${activeFilterTab === "all" ? "active" : ""}`}
              onClick={() => setActiveFilterTab("all")}
            >
              All Detections ({hotspots.length})
            </button>
            <button
              type="button"
              className={`tab-filter-btn ${activeFilterTab === "high_risk" ? "active" : ""}`}
              onClick={() => setActiveFilterTab("high_risk")}
            >
              <AlertTriangle size={13} />
              <span>High Risk ({highRiskCount})</span>
            </button>
            <button
              type="button"
              className={`tab-filter-btn ${activeFilterTab === "industrial" ? "active" : ""}`}
              onClick={() => setActiveFilterTab("industrial")}
            >
              <Factory size={13} />
              <span>Industrial ({industrialCount})</span>
            </button>
            <button
              type="button"
              className={`tab-filter-btn ${activeFilterTab === "persistent" ? "active" : ""}`}
              onClick={() => setActiveFilterTab("persistent")}
            >
              <Clock size={13} />
              <span>Persistent ({persistentCount})</span>
            </button>
            <button
              type="button"
              className={`tab-filter-btn ${activeFilterTab === "anomaly" ? "active" : ""}`}
              onClick={() => setActiveFilterTab("anomaly")}
            >
              <Zap size={13} />
              <span>Anomaly Spikes ({anomalyCount})</span>
            </button>
          </div>

          <div className="table-count-label">
            Showing <strong>{filteredAlerts.length}</strong> incidents
          </div>
        </div>

        <HotspotTable
          hotspots={filteredAlerts}
          selectedHotspotId={selectedHotspot?.id}
          onSelectHotspot={onSelectHotspot}
          onNavigateToAnalysis={(h) => onNavigate("analysis", h)}
        />
      </div>
    </div>
  );
}
