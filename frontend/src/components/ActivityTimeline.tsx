import { useMemo } from "react";
import { Clock, TrendingUp, Satellite, AlertTriangle } from "lucide-react";
import {
  AreaChart,
  Area,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import { generateHotspotPassSeries } from "../services/telemetryEngine";
import type { HotSpot } from "../types/hotSpot";

interface ActivityTimelineProps {
  hotspot: HotSpot | null;
}

export default function ActivityTimeline({ hotspot }: ActivityTimelineProps) {
  const timelineData = useMemo(() => {
    if (!hotspot) return [];
    const series = generateHotspotPassSeries(hotspot);
    return series.map((s, idx) => ({
      time: s.time,
      frp: s.frp,
      baseline: s.baseline,
      ratio: s.ratio,
      satellite: s.satellite,
      isAnomaly: s.isAnomaly,
      status:
        idx === series.length - 1
          ? s.isAnomaly
            ? "ANOMALOUS RADIATIVE SPIKE"
            : "Latest Orbital Pass"
          : s.ratio >= 2.0
          ? "Escalating Thermal Energy"
          : "Nominal Baseline Cycle",
    }));
  }, [hotspot]);

  if (!hotspot) {
    return (
      <section className="institutional-activity-panel empty">
        <div className="empty-state-wrap">
          <Clock size={24} />
          <p>Select a hotspot to view chronological overpass progression.</p>
        </div>
      </section>
    );
  }

  const latest = timelineData[timelineData.length - 1];
  const isSpike = latest?.isAnomaly;
  const ratio = hotspot.frp_ratio_to_baseline || 1.1;

  return (
    <section
      className="institutional-activity-panel"
      aria-label="Activity Progression Timeline"
    >
      <div className="panel-top-row">
        <div className="top-title-col">
          <span className="panel-eyebrow">MULTI-SATELLITE TEMPORAL REVISIT AUDIT</span>
          <h3 className="panel-main-heading">
            Orbital Overpass Progression &amp; Historical Baseline Comparison
          </h3>
        </div>

        <div
          className="trend-indicator-badge"
          style={{
            backgroundColor: isSpike ? "#FEF2F2" : "#F0FDF4",
            color: isSpike ? "#DC2626" : "#16A34A",
            borderColor: isSpike ? "#F87171" : "#86EFAC",
          }}
        >
          {isSpike ? <AlertTriangle size={14} /> : <TrendingUp size={14} />}
          <span>
            {isSpike
              ? `ANOMALY DETECTED: FRP IS ${ratio.toFixed(1)}x HISTORICAL BASELINE`
              : `NOMINAL OPERATION: FRP WITHIN NORMAL VARIANCE (${ratio.toFixed(1)}x BASELINE)`}
          </span>
        </div>
      </div>

      {/* Recharts Area Chart in Light Institutional Style */}
      <div className="chart-box">
        <div className="chart-caption" style={{ display: "flex", gap: "16px", alignItems: "center" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <span
              style={{
                width: "10px",
                height: "10px",
                backgroundColor: isSpike ? "#D32F2F" : "#000080",
                borderRadius: "2px",
              }}
            />
            <span>Observed Fire Radiative Power (MW)</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <span
              style={{
                width: "12px",
                height: "2px",
                backgroundColor: "#94a3b8",
                borderStyle: "dashed",
              }}
            />
            <span style={{ color: "#64748b" }}>Historical Grid-Cell Baseline Mean</span>
          </div>
        </div>

        <div style={{ width: "100%", height: 200 }}>
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart
              data={timelineData}
              margin={{ top: 10, right: 20, left: -10, bottom: 0 }}
            >
              <defs>
                <linearGradient id="frpGovGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop
                    offset="5%"
                    stopColor={isSpike ? "#D32F2F" : "#000080"}
                    stopOpacity={0.3}
                  />
                  <stop
                    offset="95%"
                    stopColor={isSpike ? "#D32F2F" : "#000080"}
                    stopOpacity={0.0}
                  />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
              <XAxis
                dataKey="time"
                tick={{ fontSize: 10, fill: "#64748b" }}
                stroke="#cbd5e1"
              />
              <YAxis
                unit=" MW"
                tick={{ fontSize: 10, fill: "#64748b" }}
                stroke="#cbd5e1"
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#ffffff",
                  border: "1px solid #cbd5e1",
                  borderRadius: "4px",
                  fontSize: "12px",
                  color: "#1e293b",
                  boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
                }}
                formatter={(val: any, name: any) => [
                  `${val ?? 0} MW`,
                  name === "frp" ? "Observed FRP" : "Historical Baseline",
                ]}
              />
              <Area
                type="monotone"
                dataKey="frp"
                stroke={isSpike ? "#D32F2F" : "#000080"}
                strokeWidth={2.5}
                fillOpacity={1}
                fill="url(#frpGovGradient)"
              />
              <Line
                type="monotone"
                dataKey="baseline"
                stroke="#94a3b8"
                strokeWidth={1.5}
                strokeDasharray="4 4"
                dot={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Chronological Overpass Step Nodes */}
      <div className="timeline-stepper-gov">
        {timelineData.map((step, idx) => {
          const isLatest = idx === timelineData.length - 1;
          return (
            <div
              key={step.time}
              className={`timeline-step-node ${isLatest ? "is-latest" : ""}`}
            >
              <div className="step-time-header">
                <span className="step-time-text">{step.time}</span>
                {isLatest && (
                  <span
                    className="step-current-pill"
                    style={{
                      backgroundColor: isSpike ? "#D32F2F" : "#000080",
                    }}
                  >
                    LATEST PASS
                  </span>
                )}
              </div>

              <div className="step-track">
                <span
                  className={`step-dot-point ${isLatest ? "active" : ""}`}
                  style={{
                    backgroundColor: isLatest
                      ? isSpike
                        ? "#D32F2F"
                        : "#000080"
                      : "#94a3b8",
                  }}
                />
                {idx < timelineData.length - 1 && (
                  <span className="step-line-segment" />
                )}
              </div>

              <div className="step-content-card">
                <div
                  className="step-frp-number"
                  style={{ color: isLatest && isSpike ? "#D32F2F" : "#1e293b" }}
                >
                  {step.frp} MW
                </div>
                <div className="step-sat-name">
                  <Satellite size={12} />
                  <span>{step.satellite}</span>
                </div>
                <div
                  className="step-status-tag"
                  style={{
                    color: step.isAnomaly ? "#D32F2F" : "#475569",
                    fontWeight: step.isAnomaly ? 700 : 500,
                  }}
                >
                  {step.status} ({step.ratio.toFixed(1)}x base)
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
