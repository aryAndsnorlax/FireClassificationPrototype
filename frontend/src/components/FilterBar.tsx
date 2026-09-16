import { Filter, AlertTriangle, Zap, Check } from "lucide-react";
import { FIRE_CLASSES, CLASS_COLORS, CLASS_LABELS } from "../data/fireClasses";
import type { HotSpotFilterState } from "../types/hotSpot";

interface FilterBarProps {
  filters: HotSpotFilterState;
  onFilterChange: (filters: HotSpotFilterState) => void;
  totalFiltered: number;
}

export default function FilterBar({
  filters,
  onFilterChange,
  totalFiltered,
}: FilterBarProps) {
  const handleClassSelect = (cls: string) => {
    onFilterChange({
      ...filters,
      classification: cls,
    });
  };

  const toggleRiskThreshold = (threshold: number) => {
    onFilterChange({
      ...filters,
      riskThreshold: filters.riskThreshold === threshold ? 0 : threshold,
    });
  };

  const toggleAnomalyOnly = () => {
    onFilterChange({
      ...filters,
      anomalyOnly: !filters.anomalyOnly,
    });
  };

  return (
    <div className="gov-filter-bar" role="toolbar" aria-label="Hotspot Filters">
      <div className="gov-filter-section">
        <div className="gov-filter-label">
          <Filter size={13} />
          <span>CLASSIFICATION:</span>
        </div>

        <div className="gov-filter-buttons">
          <button
            type="button"
            className={`gov-filter-btn ${filters.classification === "all" ? "active" : ""}`}
            onClick={() => handleClassSelect("all")}
          >
            {filters.classification === "all" && <Check size={12} />}
            <span>All Classes</span>
          </button>

          {FIRE_CLASSES.map((cls) => {
            const isActive = filters.classification === cls;
            const color = CLASS_COLORS[cls];
            return (
              <button
                key={cls}
                type="button"
                className={`gov-filter-btn ${isActive ? "active" : ""}`}
                style={{
                  borderColor: isActive ? color : undefined,
                  color: isActive ? "#1A1A1A" : undefined,
                  backgroundColor: isActive ? `${color}18` : undefined,
                }}
                onClick={() => handleClassSelect(cls)}
              >
                <span
                  className="gov-filter-dot"
                  style={{ backgroundColor: color }}
                />
                <span>{CLASS_LABELS[cls]}</span>
              </button>
            );
          })}
        </div>
      </div>

      <div className="gov-filter-actions">
        <button
          type="button"
          className={`gov-toggle-btn ${filters.riskThreshold === 0.7 ? "is-active" : ""}`}
          onClick={() => toggleRiskThreshold(0.7)}
          title="Filter events with risk score ≥ 0.70"
        >
          <AlertTriangle size={13} />
          <span>Active Alerts (≥ 0.70)</span>
        </button>

        <button
          type="button"
          className={`gov-toggle-btn ${filters.anomalyOnly ? "is-active" : ""}`}
          onClick={toggleAnomalyOnly}
          title="Filter events flagged as statistical anomalies"
        >
          <Zap size={13} />
          <span>Anomalies Only</span>
        </button>

        <div className="gov-filter-counter">
          <span>MATCHING RECORDS:</span>
          <strong>{totalFiltered}</strong>
        </div>
      </div>
    </div>
  );
}
