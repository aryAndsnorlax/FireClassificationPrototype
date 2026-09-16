import { useState, useMemo } from "react";
import PageHeader from "../components/PageHeader";
import FireMap from "../components/FireMap";
import FilterBar from "../components/FilterBar";
import AlertPanel from "../components/AlertPanel";
import type { HotSpot, HotSpotFilterState } from "../types/hotSpot";
import type { NavTabId } from "../components/Navigation";

interface FireMapPageProps {
  hotspots: HotSpot[];
  selectedHotspot: HotSpot | null;
  onSelectHotspot: (hotspot: HotSpot) => void;
  onNavigate: (tab: NavTabId, hotspot?: HotSpot) => void;
}

export default function FireMapPage({
  hotspots,
  selectedHotspot,
  onSelectHotspot,
  onNavigate,
}: FireMapPageProps) {
  const [filters, setFilters] = useState<HotSpotFilterState>({
    classification: "all",
    riskThreshold: 0,
    anomalyOnly: false,
    searchQuery: "",
  });

  // Filter hotspots based on user criteria
  const filteredHotspots = useMemo(() => {
    return hotspots.filter((h) => {
      if (
        filters.classification !== "all" &&
        h.classification !== filters.classification
      ) {
        return false;
      }
      if (filters.riskThreshold > 0 && h.risk_score < filters.riskThreshold) {
        return false;
      }
      if (filters.anomalyOnly && !h.is_anomaly) {
        return false;
      }
      return true;
    });
  }, [hotspots, filters]);

  return (
    <div className="portal-page-container">
      <PageHeader
        category="GEOGRAPHIC INFORMATION SYSTEM (GIS)"
        title="National Fire & Thermal Hotspot Map"
        subtitle="Visualizing real-time satellite thermal detections over the Indian subcontinent with classification overlays and industrial buffer analytics."
        badge={`${filteredHotspots.length} HOTSPOTS VISIBLE`}
      />

      {/* Filter Toolbar */}
      <FilterBar
        filters={filters}
        onFilterChange={setFilters}
        totalFiltered={filteredHotspots.length}
      />

      {/* Main GIS Layout: Map + Inspector Sidebar */}
      <div className="gis-layout-grid">
        <div className="gis-map-panel">
          <FireMap
            hotspots={filteredHotspots}
            selectedHotspot={selectedHotspot}
            onSelectHotspot={onSelectHotspot}
            onViewAnalysis={(h) => onNavigate("analysis", h)}
            height="620px"
          />
        </div>

        <div className="gis-sidebar-panel">
          <AlertPanel
            hotspot={selectedHotspot}
            onViewAnalysis={(h) => onNavigate("analysis", h)}
          />
        </div>
      </div>
    </div>
  );
}
