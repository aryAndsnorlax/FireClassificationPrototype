import { Flame, Factory, AlertOctagon, Repeat, AlertTriangle } from "lucide-react";
import type { HotSpot } from "../types/hotSpot";

interface OverviewStatsProps {
  hotspots: HotSpot[];
}

export default function OverviewStats({ hotspots }: OverviewStatsProps) {
  // Key Operational Metric Definitions per AgniNetra Implementation Plan:
  // 1. ACTIVE HOTSPOTS = total detected records
  // 2. INDUSTRIAL HOTSPOTS = industrial_fire + persistent_industrial
  // 3. HIGH-RISK HOTSPOTS = risk_score >= 0.85
  // 4. PERSISTENT SOURCES = multi-pass detected locations (persistence >= 10)
  // 5. ANOMALIES = statistical thermal spikes exceeding baseline (is_anomaly = true)
  const totalHotspots = hotspots.length;

  const industrialEvents = hotspots.filter(
    (h) =>
      h.classification === "industrial_fire" ||
      h.classification === "persistent_industrial"
  ).length;

  const highRiskEvents = hotspots.filter((h) => h.risk_score >= 0.85).length;

  const persistentSources = hotspots.filter((h) => h.persistence >= 10).length;

  const anomaliesCount = hotspots.filter((h) => h.is_anomaly).length;

  const stats = [
    {
      id: "total",
      label: "Active Hotspots",
      value: totalHotspots,
      desc: "Live satellite fire detections",
      icon: Flame,
      badgeColor: "#002147",
      accentBorder: "#002147",
    },
    {
      id: "industrial",
      label: "Industrial Sites",
      value: industrialEvents,
      desc: "Refineries & industrial plants",
      icon: Factory,
      badgeColor: "#ea580c",
      accentBorder: "#ea580c",
    },
    {
      id: "high_risk",
      label: "High-Risk Alerts",
      value: highRiskEvents,
      desc: "Requires immediate attention",
      icon: AlertOctagon,
      badgeColor: "#dc2626",
      accentBorder: "#dc2626",
    },
    {
      id: "persistent",
      label: "Persistent Flares",
      value: persistentSources,
      desc: "Continuous multi-pass activity",
      icon: Repeat,
      badgeColor: "#9a3412",
      accentBorder: "#9a3412",
    },
    {
      id: "anomalies",
      label: "Heat Spikes (Anomalies)",
      value: anomaliesCount,
      desc: "Sudden spike above baseline",
      icon: AlertTriangle,
      badgeColor: "#b91c1c",
      accentBorder: "#b91c1c",
    },
  ];

  return (
    <section className="overview-stats-grid" aria-label="Key Operational Statistics">
      {stats.map((item) => {
        const Icon = item.icon;
        return (
          <div
            key={item.id}
            className="stat-card"
            style={{ borderTop: `3px solid ${item.accentBorder}` }}
          >
            <div className="stat-card-header">
              <span className="stat-card-title">{item.label}</span>
              <div
                className="stat-card-icon"
                style={{ color: item.badgeColor }}
              >
                <Icon size={18} />
              </div>
            </div>

            <div className="stat-card-body">
              <span className="stat-card-number">{item.value}</span>
            </div>

            <div className="stat-card-footer">
              <span className="stat-card-desc">{item.desc}</span>
            </div>
          </div>
        );
      })}
    </section>
  );
}
