export type FireClassification =
  | "industrial_fire"
  | "persistent_industrial"
  | "coal_seam_fire"
  | "agricultural_burning"
  | "wildfire"
  | "unknown";

export type RiskLevel = "critical" | "high" | "moderate" | "low";

export interface HotSpot {
  id: string;
  name?: string;
  location_name?: string;

  latitude: number;
  longitude: number;

  frp: number;
  brightness: number;
  confidence: number;

  classification: FireClassification;

  risk_score: number;
  is_anomaly: boolean;

  facility_distance_km: number;
  facility_type?: string;
  persistence: number;

  timestamp: string;
  sensor?: string;
  frp_ratio_to_baseline?: number;
  lc_class?: string;
  state?: string;
  cluster_size?: number;
}

// Type alias
export type Hotspot = HotSpot;

export interface HotSpotFilterState {
  classification: string;
  riskThreshold: number;
  anomalyOnly: boolean;
  searchQuery: string;
}

export type HotspotFilterState = HotSpotFilterState;