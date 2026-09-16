import { Eye, MapPin, AlertTriangle } from "lucide-react";
import { CLASS_LABELS, CLASS_COLORS, getRiskBadge } from "../data/fireClasses";
import type { HotSpot } from "../types/hotSpot";

interface HotspotTableProps {
  hotspots: HotSpot[];
  selectedHotspotId?: string;
  onSelectHotspot: (hotspot: HotSpot) => void;
  onNavigateToAnalysis?: (hotspot: HotSpot) => void;
}

export default function HotspotTable({
  hotspots,
  selectedHotspotId,
  onSelectHotspot,
  onNavigateToAnalysis,
}: HotspotTableProps) {
  if (hotspots.length === 0) {
    return (
      <div className="table-empty-state">
        <AlertTriangle size={32} className="empty-icon" />
        <h3>No Matching Hotspots Found</h3>
        <p>Adjust your filter criteria to view detected fire incidents.</p>
      </div>
    );
  }

  return (
    <div className="institutional-table-container">
      <table className="institutional-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Location & Coordinates</th>
            <th>Classification</th>
            <th>Risk Level</th>
            <th>Heat (FRP)</th>
            <th>Confidence</th>
            <th>Facility Distance</th>
            <th>Persistence</th>
            <th>Detected At</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {hotspots.map((hotspot) => {
            const isSelected = hotspot.id === selectedHotspotId;
            const riskBadge = getRiskBadge(hotspot.risk_score);
            const classColor = CLASS_COLORS[hotspot.classification];
            const dateStr = new Date(hotspot.timestamp).toLocaleString("en-GB", {
              day: "2-digit",
              month: "short",
              hour: "2-digit",
              minute: "2-digit",
              timeZone: "Asia/Kolkata",
            });

            return (
              <tr
                key={hotspot.id}
                className={isSelected ? "row-selected" : ""}
                onClick={() => onSelectHotspot(hotspot)}
              >
                <td className="cell-id">
                  <strong>{hotspot.id}</strong>
                  {hotspot.is_anomaly && (
                    <span className="table-anomaly-tag">ANOMALY</span>
                  )}
                </td>

                <td className="cell-location">
                  <div className="location-name">
                    {hotspot.name || hotspot.location_name || "Unassigned Location"}
                  </div>
                  <div className="coord-subtext">
                    <MapPin size={11} />
                    <span>
                      {hotspot.latitude.toFixed(4)}° N, {hotspot.longitude.toFixed(4)}° E
                    </span>
                  </div>
                </td>

                <td className="cell-classification">
                  <span
                    className="class-badge"
                    style={{
                      backgroundColor: `${classColor}15`,
                      color: classColor,
                      borderColor: classColor,
                    }}
                  >
                    <span
                      className="class-badge-dot"
                      style={{ backgroundColor: classColor }}
                    />
                    {CLASS_LABELS[hotspot.classification]}
                  </span>
                </td>

                <td className="cell-risk">
                  <span
                    className="table-risk-badge"
                    style={{
                      color: riskBadge.color,
                      backgroundColor: riskBadge.bg,
                      borderColor: riskBadge.borderColor,
                    }}
                  >
                    {Math.round(hotspot.risk_score * 100)}% &bull; {riskBadge.label}
                  </span>
                </td>

                <td className="cell-frp">
                  <strong>{hotspot.frp.toFixed(1)}</strong> MW
                </td>

                <td className="cell-confidence">
                  <div className="confidence-num">{hotspot.confidence}%</div>
                  <div className="confidence-track">
                    <div
                      className="confidence-fill"
                      style={{ width: `${hotspot.confidence}%` }}
                    />
                  </div>
                </td>

                <td className="cell-facility">
                  <div className="facility-dist">
                    {hotspot.facility_distance_km < 1
                      ? `${(hotspot.facility_distance_km * 1000).toFixed(0)} m`
                      : `${hotspot.facility_distance_km.toFixed(1)} km`}
                  </div>
                  <div className="facility-type-sub">
                    {hotspot.facility_type || "Asset Buffer"}
                  </div>
                </td>

                <td className="cell-persistence">
                  <span className="persistence-pill">
                    {hotspot.persistence} passes
                  </span>
                </td>

                <td className="cell-time">{dateStr} IST</td>

                <td
                  className="cell-actions"
                  onClick={(e) => e.stopPropagation()}
                >
                  <button
                    type="button"
                    className="table-action-btn"
                    title="Open Detailed Hotspot Analysis"
                    onClick={() => {
                      onSelectHotspot(hotspot);
                      if (onNavigateToAnalysis) {
                        onNavigateToAnalysis(hotspot);
                      }
                    }}
                  >
                    <Eye size={13} />
                    <span>Analyze</span>
                  </button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
