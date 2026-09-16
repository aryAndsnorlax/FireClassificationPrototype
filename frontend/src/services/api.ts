import {
  COMPREHENSIVE_INDIAN_HOTSPOTS,
  evaluateRuleBasedLabel,
} from "./telemetryEngine";
import type { HotSpot, HotSpotFilterState } from "../types/hotSpot";

const API_BASE = "http://localhost:8000";

// Live in-memory state allowing the frontend to react to simulation events
let currentHotspots: HotSpot[] = [...COMPREHENSIVE_INDIAN_HOTSPOTS];

type HotspotChangeListener = (hotspots: HotSpot[]) => void;
const listeners: Set<HotspotChangeListener> = new Set();

export function subscribeHotspots(listener: HotspotChangeListener): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

function notifyListeners() {
  listeners.forEach((fn) => fn([...currentHotspots]));
}

interface GeoJsonHotspotFeature {
  type: string;
  geometry: {
    type: string;
    coordinates: [number, number]; // [longitude, latitude] in GeoJSON
  };
  properties: {
    id: string | number;
    class?: string;
    confidence?: number;
    frp?: number;
    brightness?: number;
    sensor?: string;
    acq_date?: string;
    facility_type?: string;
    distance_to_facility_m?: number;
    persistence_score?: number;
    frp_ratio_to_baseline?: number;
    lc_class?: string;
    cluster_size?: number;
    is_anomaly?: boolean;
    risk_score?: number;
  };
}

interface GeoJsonCollection {
  type: string;
  features: GeoJsonHotspotFeature[];
}

interface BackendAlertItem {
  id: string | number;
  latitude: number;
  longitude: number;
  class: string;
  frp: number;
  brightness?: number;
  confidence?: string;
  frp_ratio_to_baseline?: number;
  acq_date?: string;
  facility_type?: string;
  risk_score?: number;
}

export interface HotspotStats {
  total_hotspots: number;
  high_risk_count: number;
  anomaly_count: number;
  class_breakdown: Record<string, number>;
  avg_frp: number | null;
  latest_acq_date: string | null;
}

/**
 * Normalizes GeoJSON feature from FastAPI into the frontend Hotspot interface.
 * Correctly converts GeoJSON [lon, lat] coordinates to Leaflet [lat, lon].
 */
function mapGeoJsonFeatureToHotspot(feature: GeoJsonHotspotFeature): HotSpot {
  const [lon, lat] = feature.geometry.coordinates;
  const p = feature.properties;

  const rawClass = p.class || "unknown";
  const validClasses = [
    "industrial_fire",
    "persistent_industrial",
    "coal_seam_fire",
    "agricultural_burning",
    "wildfire",
    "unknown",
  ];
  const classification = validClasses.includes(rawClass)
    ? (rawClass as HotSpot["classification"])
    : "unknown";

  const frp = p.frp ?? 35.0;
  const confidence = p.confidence
    ? p.confidence > 1
      ? Math.round(p.confidence)
      : Math.round(p.confidence * 100)
    : 80;

  const isAnomaly = Boolean(p.is_anomaly);
  const risk_score =
    p.risk_score ??
    (isAnomaly
      ? 0.91
      : classification === "industrial_fire"
      ? 0.94
      : classification === "persistent_industrial"
      ? 0.88
      : classification === "coal_seam_fire"
      ? 0.83
      : classification === "wildfire"
      ? 0.72
      : 0.4);

  const facilityDistKm =
    p.distance_to_facility_m != null
      ? p.distance_to_facility_m / 1000
      : classification === "industrial_fire" ||
        classification === "persistent_industrial"
      ? 0.4
      : 6.5;

  const persistence = p.persistence_score
    ? Math.round(p.persistence_score * 20)
    : isAnomaly
    ? 12
    : 3;

  return {
    id: String(p.id).startsWith("HOT-") ? String(p.id) : `HOT-${p.id}`,
    latitude: lat,
    longitude: lon,
    frp,
    brightness: p.brightness ?? Math.round(300 + frp * 0.5),
    confidence,
    classification,
    risk_score,
    is_anomaly: isAnomaly,
    facility_distance_km: Number(facilityDistKm.toFixed(2)),
    facility_type: p.facility_type || "Industrial Asset",
    persistence,
    timestamp: p.acq_date || new Date().toISOString(),
    sensor: p.sensor || "VIIRS (375m)",
    frp_ratio_to_baseline: p.frp_ratio_to_baseline ?? (isAnomaly ? 3.5 : 1.1),
    lc_class: p.lc_class || "industrial",
    cluster_size: p.cluster_size ?? 1,
  };
}

/**
 * Checks if the local FastAPI backend is active
 */
export async function checkBackendHealth(): Promise<{
  isOnline: boolean;
  status: string;
}> {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 1200);
    const res = await fetch(`${API_BASE}/health`, { signal: controller.signal });
    clearTimeout(timeoutId);
    if (res.ok) {
      const data = await res.json();
      return { isOnline: true, status: data.status || "ok" };
    }
  } catch {
    // Offline
  }
  return { isOnline: false, status: "offline" };
}

/**
 * Fetch classified hotspots.
 * Attempts to query FastAPI backend; smoothly falls back to current dynamic hotspots if unavailable.
 */
export async function getHotspots(
  filters?: Partial<HotSpotFilterState>
): Promise<HotSpot[]> {
  try {
    const params = new URLSearchParams();
    if (filters?.classification && filters.classification !== "all") {
      params.append("class", filters.classification);
    }
    if (filters?.anomalyOnly) {
      params.append("anomaly_only", "true");
    }
    if (filters?.riskThreshold && filters.riskThreshold > 0) {
      params.append("min_risk", filters.riskThreshold.toString());
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 1500);

    const response = await fetch(`${API_BASE}/hotspots/?${params.toString()}`, {
      signal: controller.signal,
    });
    clearTimeout(timeoutId);

    if (response.ok) {
      const geojson: GeoJsonCollection = await response.json();
      if (geojson.features && geojson.features.length > 0) {
        let results = geojson.features.map(mapGeoJsonFeatureToHotspot);
        if (filters?.anomalyOnly) {
          results = results.filter((h) => h.is_anomaly);
        }
        if (filters?.riskThreshold && filters.riskThreshold > 0) {
          results = results.filter((h) => h.risk_score >= filters.riskThreshold!);
        }
        return results;
      }
    }
  } catch {
    // Backend offline or unreachable: use active telemetry engine state
  }

  // Filter local telemetry engine data
  let data = [...currentHotspots];
  if (filters?.classification && filters.classification !== "all") {
    data = data.filter((h) => h.classification === filters.classification);
  }
  if (filters?.anomalyOnly) {
    data = data.filter((h) => h.is_anomaly);
  }
  if (filters?.riskThreshold && filters.riskThreshold > 0) {
    data = data.filter((h) => h.risk_score >= (filters.riskThreshold || 0));
  }

  return data;
}

/**
 * Fetch anomaly alerts from FastAPI /alerts/ endpoint or fallback to anomalies.
 */
export async function getAlerts(): Promise<HotSpot[]> {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 1500);
    const res = await fetch(`${API_BASE}/alerts/`, { signal: controller.signal });
    clearTimeout(timeoutId);

    if (res.ok) {
      const items: BackendAlertItem[] = await res.json();
      if (Array.isArray(items) && items.length > 0) {
        return items.map((item) => ({
          id: String(item.id).startsWith("HOT-") ? String(item.id) : `HOT-${item.id}`,
          latitude: item.latitude,
          longitude: item.longitude,
          frp: item.frp,
          brightness: item.brightness ?? Math.round(310 + item.frp * 0.5),
          confidence: item.confidence ? (isNaN(Number(item.confidence)) ? 90 : Number(item.confidence)) : 90,
          classification: (item.class as HotSpot["classification"]) || "industrial_fire",
          risk_score: item.risk_score ?? 0.92,
          is_anomaly: true,
          facility_distance_km: 0.4,
          facility_type: item.facility_type || "Industrial Facility",
          persistence: 10,
          timestamp: item.acq_date || new Date().toISOString(),
          frp_ratio_to_baseline: item.frp_ratio_to_baseline || 3.5,
        }));
      }
    }
  } catch {
    // Fallback to local anomaly state
  }

  return currentHotspots.filter((h) => h.is_anomaly || h.risk_score >= 0.75);
}

/**
 * Simulates a new satellite overpass (e.g. VIIRS Suomi-NPP or NOAA-20).
 * Increments persistence, updates acquisition timestamps, and injects realistic telemetry noise.
 */
export function simulateSatellitePass(sensor: string = "VIIRS_NOAA20 (375m)"): HotSpot[] {
  const now = new Date().toISOString();
  currentHotspots = currentHotspots.map((h) => {
    // Small realistic radiometric drift (+- 5%)
    const drift = (Math.random() * 0.1 - 0.05);
    const newFrp = Number((h.frp * (1 + drift)).toFixed(1));
    const newPersistence = h.persistence + 1;
    return {
      ...h,
      frp: newFrp,
      persistence: newPersistence,
      timestamp: now,
      sensor,
    };
  });
  notifyListeners();
  return currentHotspots;
}

/**
 * Injects a sudden thermal spike at an industrial facility to demonstrate anomaly detection
 */
export function injectSpikeAnomaly(hotspotId: string = "HOT-002"): HotSpot[] {
  currentHotspots = currentHotspots.map((h) => {
    if (h.id === hotspotId) {
      const baseline = Number((h.frp / (h.frp_ratio_to_baseline || 1.1)).toFixed(1));
      const spikedFrp = Number((baseline * 3.85).toFixed(1)); // 3.85x surge
      const evalRes = evaluateRuleBasedLabel({
        distance_to_facility_m: h.facility_distance_km * 1000,
        persistence_score: Math.min(1.0, h.persistence / 20),
        frp_ratio_to_baseline: 3.85,
        lc_class: h.lc_class || "industrial",
        state: h.state,
        frp: spikedFrp,
      });

      return {
        ...h,
        frp: spikedFrp,
        brightness: Math.round(h.brightness + 35),
        frp_ratio_to_baseline: 3.85,
        is_anomaly: true,
        classification: evalRes.classification,
        risk_score: evalRes.risk_score,
        confidence: 97,
        timestamp: new Date().toISOString(),
      };
    }
    return h;
  });
  notifyListeners();
  return currentHotspots;
}

/**
 * Updates a specific hotspot's parameters in live state
 */
export function updateHotspotTelemetry(hotspotId: string, updates: Partial<HotSpot>): HotSpot[] {
  currentHotspots = currentHotspots.map((h) => {
    if (h.id === hotspotId) {
      return { ...h, ...updates };
    }
    return h;
  });
  notifyListeners();
  return currentHotspots;
}

/**
 * Resets telemetry to default Indian baseline
 */
export function resetSimulation(): HotSpot[] {
  currentHotspots = [...COMPREHENSIVE_INDIAN_HOTSPOTS];
  notifyListeners();
  return currentHotspots;
}

export const getHotSpots = getHotspots;

/**
 * Fetch aggregated dashboard surveillance stats from FastAPI /hotspots/stats.
 * Gracefully falls back to computing statistics over currentHotspots if offline.
 */
export async function getHotspotStats(): Promise<HotspotStats> {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 1500);
    const res = await fetch(`${API_BASE}/hotspots/stats`, { signal: controller.signal });
    clearTimeout(timeoutId);

    if (res.ok) {
      const stats: HotspotStats = await res.json();
      return stats;
    }
  } catch {
    // Fallback to local computation
  }

  const breakdown: Record<string, number> = {};
  let totalFrp = 0;
  let highRisk = 0;
  let anomalies = 0;

  for (const h of currentHotspots) {
    breakdown[h.classification] = (breakdown[h.classification] || 0) + 1;
    totalFrp += h.frp;
    if (h.risk_score >= 0.85) highRisk++;
    if (h.is_anomaly) anomalies++;
  }

  return {
    total_hotspots: currentHotspots.length,
    high_risk_count: highRisk,
    anomaly_count: anomalies,
    class_breakdown: breakdown,
    avg_frp: currentHotspots.length > 0 ? Number((totalFrp / currentHotspots.length).toFixed(1)) : null,
    latest_acq_date: currentHotspots[0]?.timestamp || null,
  };
}

/**
 * Fetch details for a specific hotspot from FastAPI /hotspots/{id}.
 * Falls back to local in-memory hotspots if offline.
 */
export async function getHotspotById(id: string | number): Promise<HotSpot | null> {
  const numericId = typeof id === "string" && id.startsWith("HOT-") ? id.replace("HOT-", "") : String(id);

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 1500);
    const res = await fetch(`${API_BASE}/hotspots/${numericId}`, { signal: controller.signal });
    clearTimeout(timeoutId);

    if (res.ok) {
      const detail = await res.json();
      return {
        id: `HOT-${detail.id}`,
        latitude: detail.latitude,
        longitude: detail.longitude,
        frp: detail.frp ?? 30.0,
        brightness: detail.brightness ?? 330,
        confidence: typeof detail.confidence === "number" ? detail.confidence : 85,
        classification: (detail.predicted_class as HotSpot["classification"]) || "unknown",
        risk_score: detail.risk_score ?? 0.5,
        is_anomaly: Boolean(detail.is_anomaly),
        facility_distance_km: detail.distance_to_facility_m != null ? Number((detail.distance_to_facility_m / 1000).toFixed(2)) : 1.0,
        facility_type: detail.nearest_facility_type || "Industrial Asset",
        persistence: detail.persistence_score != null ? Math.round(detail.persistence_score * 20) : 3,
        timestamp: detail.acq_date || new Date().toISOString(),
        sensor: detail.sensor || "VIIRS",
        frp_ratio_to_baseline: detail.frp_ratio_to_baseline ?? 1.1,
        lc_class: detail.lc_class || "industrial",
        cluster_size: detail.cluster_size ?? 1,
      };
    }
  } catch {
    // Fallback to local state
  }

  const found = currentHotspots.find((h) => h.id === String(id) || h.id === `HOT-${numericId}`);
  return found || null;
}