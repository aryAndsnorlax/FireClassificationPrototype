/**
 * AgniNetra Dynamic Telemetry & Feature Engineering Engine
 * 
 * Direct TypeScript implementation of the project's Python pipelines:
 * - src/utils/config.py (FACILITY_PROXIMITY_M = 1000, PERSISTENCE_FREQ_THRESHOLD = 0.6, FRP_ANOMALY_RATIO = 3.0)
 * - src/labeling/rule_based_labels.py (weak labeling logic)
 * - src/features/temporal_features.py (grid-based persistence and FRP ratio to baseline)
 * - src/features/clustering.py (DBSCAN spatial clustering)
 */

import type { FireClassification, HotSpot } from "../types/hotSpot";

export const STUBBLE_BURNING_STATES = new Set(["Punjab", "Haryana", "Uttar Pradesh"]);
export const STUBBLE_BURNING_MONTHS = new Set([10, 11]);

export interface PipelineEvaluation {
  classification: FireClassification;
  risk_score: number;
  is_anomaly: boolean;
  confidence: number;
  decisionPath: string[];
  riskAttribution: {
    factor: string;
    level: "CRITICAL" | "HIGH" | "ELEVATED" | "NOMINAL";
    impact: string;
  }[];
}

/**
 * Evaluates a hotspot using the EXACT decision tree from src/labeling/rule_based_labels.py
 */
export function evaluateRuleBasedLabel(params: {
  distance_to_facility_m: number;
  persistence_score: number; // 0.0 to 1.0 (fraction of days detected)
  frp_ratio_to_baseline: number; // e.g. 1.0 = baseline, 3.5 = 3.5x baseline
  lc_class: string;
  state?: string;
  month?: number;
  frp: number;
  brightness?: number;
  cluster_size?: number;
}): PipelineEvaluation {
  const {
    distance_to_facility_m,
    persistence_score,
    frp_ratio_to_baseline,
    lc_class,
    state = "Punjab",
    month = 10,
    frp,
  } = params;

  const nearFacility = distance_to_facility_m <= 1000;
  const isPersistent = persistence_score >= 0.6;
  const isSpike = frp_ratio_to_baseline >= 3.0;

  const decisionPath: string[] = [];
  const riskAttribution: PipelineEvaluation["riskAttribution"] = [];

  let classification: FireClassification = "unknown";
  let risk_score = 0.4;
  let is_anomaly = false;
  let confidence = 82;

  // Step 1: Spatial Proximity Join (OSM 1000m Buffer)
  if (nearFacility) {
    decisionPath.push(`Proximity: ${distance_to_facility_m}m <= 1,000m buffer (INSIDE INDUSTRIAL PERIMETER)`);
    riskAttribution.push({
      factor: "Facility Boundary Buffer",
      level: "CRITICAL",
      impact: `Within ${distance_to_facility_m.toFixed(0)}m of mapped industrial polygon (high asset vulnerability).`,
    });

    // Step 2: Temporal Persistence Check (90-day window)
    if (isPersistent) {
      decisionPath.push(`Persistence: ${(persistence_score * 100).toFixed(0)}% >= 60% threshold (CONFIRMED PERSISTENT SOURCE)`);
      
      // Step 3: FRP Baseline Deviation
      if (isSpike) {
        decisionPath.push(`Intensity Ratio: ${frp_ratio_to_baseline.toFixed(1)}x >= 3.0x threshold (ANOMALY SPIKE DETECTED)`);
        classification = "industrial_fire";
        risk_score = Math.min(0.98, 0.88 + (frp_ratio_to_baseline - 3.0) * 0.03);
        is_anomaly = true;
        confidence = 95;
        riskAttribution.push({
          factor: "Thermal Radiative Surge",
          level: "CRITICAL",
          impact: `FRP is ${frp_ratio_to_baseline.toFixed(1)}x historical mean, indicating uncontrolled combustion/explosion at plant.`,
        });
      } else {
        decisionPath.push(`Intensity Ratio: ${frp_ratio_to_baseline.toFixed(1)}x < 3.0x (NOMINAL FLARE / KILN OPERATION)`);
        classification = "persistent_industrial";
        risk_score = 0.84;
        is_anomaly = false;
        confidence = 96;
        riskAttribution.push({
          factor: "Steady-State Industrial Operation",
          level: "HIGH",
          impact: "Continuous operational flare or blast furnace within registered operational envelope.",
        });
      }
    } else {
      decisionPath.push(`Persistence: ${(persistence_score * 100).toFixed(0)}% < 60% (TRANSIENT / NEW HEAT SOURCE AT FACILITY)`);
      if (isSpike) {
        decisionPath.push(`Intensity Ratio: ${frp_ratio_to_baseline.toFixed(1)}x >= 3.0x (NEW INDUSTRIAL ACCIDENT)`);
        classification = "industrial_fire";
        risk_score = 0.92;
        is_anomaly = true;
        confidence = 92;
      } else {
        decisionPath.push("Low persistence + near facility -> Treated as early industrial surveillance target");
        classification = "persistent_industrial";
        risk_score = 0.78;
        is_anomaly = false;
        confidence = 80;
      }
    }
  } else {
    // Outside facility (>1000m)
    decisionPath.push(`Proximity: ${distance_to_facility_m}m > 1,000m (OUTSIDE INDUSTRIAL PERIMETER)`);
    const lc = lc_class.toLowerCase();

    if (lc === "cropland") {
      const isStubbleState = STUBBLE_BURNING_STATES.has(state);
      const isStubbleMonth = STUBBLE_BURNING_MONTHS.has(month);

      if (isStubbleState && isStubbleMonth) {
        decisionPath.push(`Landcover: Cropland + State: ${state} + Month: ${month} (MATCHES STUBBLE HARVEST SEASON)`);
        classification = "agricultural_burning";
        risk_score = Math.min(0.5, 0.3 + (frp / 100) * 0.15);
        is_anomaly = false;
        confidence = 88;
        riskAttribution.push({
          factor: "Seasonal Agrarian Residue",
          level: "NOMINAL",
          impact: "Paddy crop residue burning characteristic of post-monsoon harvest window.",
        });
      } else {
        decisionPath.push(`Landcover: Cropland outside harvest window (${state}, Month ${month}) -> Review required`);
        classification = "unknown";
        risk_score = 0.45;
        confidence = 65;
      }
    } else if (["forest", "scrub", "grassland"].includes(lc)) {
      decisionPath.push(`Landcover: ${lc} (WILDLAND / VEGETATION FIRE)`);
      classification = "wildfire";
      risk_score = Math.min(0.85, 0.65 + (frp / 120) * 0.15);
      is_anomaly = frp > 50;
      confidence = 86;
      riskAttribution.push({
        factor: "Forest Canopy Biomass",
        level: "HIGH",
        impact: `Spreading biomass fire in ${lc} terrain requiring forest division containment.`,
      });
    } else if (lc === "mining") {
      decisionPath.push(`Landcover: Mining (COAL MINE / SUBSURFACE SEAM FIRE)`);
      classification = "coal_seam_fire";
      risk_score = 0.83;
      is_anomaly = false;
      confidence = 90;
      riskAttribution.push({
        factor: "Subsurface Carbon Combustion",
        level: "ELEVATED",
        impact: "Chronic open-cast or subsurface coal seam smoldering with high ground thermal signature.",
      });
    } else {
      decisionPath.push(`Landcover: ${lc} does not match specific heuristic -> Flagged as Unknown`);
      classification = "unknown";
      risk_score = 0.38;
      confidence = 60;
    }
  }

  return {
    classification,
    risk_score: Number(risk_score.toFixed(2)),
    is_anomaly,
    confidence,
    decisionPath,
    riskAttribution,
  };
}

/**
 * 18 Comprehensive Real-World Indian Hotspots
 * Represents real industrial hubs, refineries, coalfields, stubble belts, and biosphere reserves.
 */
export const COMPREHENSIVE_INDIAN_HOTSPOTS: HotSpot[] = [
  {
    id: "HOT-001",
    name: "Ludhiana Focal Point Industrial Belt",
    location_name: "Ludhiana, Punjab",
    latitude: 30.901,
    longitude: 75.8573,
    frp: 82.4,
    brightness: 341.2,
    confidence: 94,
    classification: "industrial_fire",
    risk_score: 0.94,
    is_anomaly: true,
    facility_distance_km: 0.4,
    facility_type: "Textile & Metallurgical Processing Cluster",
    persistence: 12,
    timestamp: "2026-09-15T02:40:00Z",
    sensor: "VIIRS_NPP (375m)",
    frp_ratio_to_baseline: 4.8,
    lc_class: "industrial",
    state: "Punjab",
    cluster_size: 4,
  },
  {
    id: "HOT-002",
    name: "Jamnagar Petrochemical & Refining Complex",
    location_name: "Jamnagar, Gujarat",
    latitude: 22.4707,
    longitude: 70.0577,
    frp: 91.5,
    brightness: 348.6,
    confidence: 96,
    classification: "persistent_industrial",
    risk_score: 0.88,
    is_anomaly: false,
    facility_distance_km: 0.3,
    facility_type: "Petroleum Refinery Flare Stack #3",
    persistence: 24,
    timestamp: "2026-09-15T02:35:00Z",
    sensor: "VIIRS_NOAA20 (375m)",
    frp_ratio_to_baseline: 1.15,
    lc_class: "industrial",
    state: "Gujarat",
    cluster_size: 1,
  },
  {
    id: "HOT-003",
    name: "Jharia Coalfield Pit #4 Underground Fire",
    location_name: "Dhanbad, Jharkhand",
    latitude: 23.7438,
    longitude: 86.4131,
    frp: 64.8,
    brightness: 332.1,
    confidence: 89,
    classification: "coal_seam_fire",
    risk_score: 0.83,
    is_anomaly: false,
    facility_distance_km: 1.1,
    facility_type: "Open-cast Coal Mining Complex",
    persistence: 38,
    timestamp: "2026-09-15T02:20:00Z",
    sensor: "MODIS_Terra (1km)",
    frp_ratio_to_baseline: 1.35,
    lc_class: "mining",
    state: "Jharkhand",
    cluster_size: 6,
  },
  {
    id: "HOT-004",
    name: "Amritsar Rural Harvest Stubble Fire",
    location_name: "Amritsar, Punjab",
    latitude: 31.634,
    longitude: 74.8723,
    frp: 28.5,
    brightness: 312.4,
    confidence: 76,
    classification: "agricultural_burning",
    risk_score: 0.38,
    is_anomaly: false,
    facility_distance_km: 9.4,
    facility_type: "Agricultural Cropland",
    persistence: 2,
    timestamp: "2026-09-15T02:10:00Z",
    sensor: "VIIRS_NPP (375m)",
    frp_ratio_to_baseline: 0.95,
    lc_class: "cropland",
    state: "Punjab",
    cluster_size: 8,
  },
  {
    id: "HOT-005",
    name: "Simlipal Biosphere Reserve Forest Fire",
    location_name: "Mayurbhanj, Odisha",
    latitude: 21.8715,
    longitude: 86.3312,
    frp: 54.2,
    brightness: 326.7,
    confidence: 85,
    classification: "wildfire",
    risk_score: 0.72,
    is_anomaly: false,
    facility_distance_km: 14.8,
    facility_type: "Protected Biosphere Reserve",
    persistence: 6,
    timestamp: "2026-09-15T01:55:00Z",
    sensor: "MODIS_Aqua (1km)",
    frp_ratio_to_baseline: 2.1,
    lc_class: "forest",
    state: "Odisha",
    cluster_size: 3,
  },
  {
    id: "HOT-006",
    name: "Singrauli NTPC Thermal Power Station",
    location_name: "Singrauli, Madhya Pradesh",
    latitude: 24.1997,
    longitude: 82.6644,
    frp: 78.9,
    brightness: 339.4,
    confidence: 93,
    classification: "industrial_fire",
    risk_score: 0.91,
    is_anomaly: true,
    facility_distance_km: 0.5,
    facility_type: "Super Thermal Power Plant",
    persistence: 15,
    timestamp: "2026-09-15T01:40:00Z",
    sensor: "VIIRS_NOAA20 (375m)",
    frp_ratio_to_baseline: 3.65,
    lc_class: "industrial",
    state: "Madhya Pradesh",
    cluster_size: 2,
  },
  {
    id: "HOT-007",
    name: "Bhiwadi RIICO Industrial Cluster",
    location_name: "Alwar, Rajasthan",
    latitude: 28.2104,
    longitude: 76.8606,
    frp: 49.3,
    brightness: 322.0,
    confidence: 82,
    classification: "industrial_fire",
    risk_score: 0.79,
    is_anomaly: true,
    facility_distance_km: 0.7,
    facility_type: "Chemical & Paint Manufacturing",
    persistence: 8,
    timestamp: "2026-09-15T01:15:00Z",
    sensor: "VIIRS_NPP (375m)",
    frp_ratio_to_baseline: 3.1,
    lc_class: "industrial",
    state: "Rajasthan",
    cluster_size: 2,
  },
  {
    id: "HOT-008",
    name: "Sangrur Paddy Residue Cluster",
    location_name: "Sangrur, Punjab",
    latitude: 30.2458,
    longitude: 75.8421,
    frp: 31.0,
    brightness: 316.8,
    confidence: 79,
    classification: "agricultural_burning",
    risk_score: 0.42,
    is_anomaly: false,
    facility_distance_km: 6.8,
    facility_type: "Paddy Stubble Farm Holdings",
    persistence: 3,
    timestamp: "2026-09-15T00:50:00Z",
    sensor: "VIIRS_NPP (375m)",
    frp_ratio_to_baseline: 1.08,
    lc_class: "cropland",
    state: "Punjab",
    cluster_size: 5,
  },
  {
    id: "HOT-009",
    name: "Barauni Petroleum Refinery Flare Stack",
    location_name: "Begusarai, Bihar",
    latitude: 25.4419,
    longitude: 86.0028,
    frp: 86.2,
    brightness: 344.1,
    confidence: 95,
    classification: "persistent_industrial",
    risk_score: 0.87,
    is_anomaly: false,
    facility_distance_km: 0.25,
    facility_type: "Crude Refining & Petrochem Flare",
    persistence: 28,
    timestamp: "2026-09-15T00:30:00Z",
    sensor: "VIIRS_NOAA20 (375m)",
    frp_ratio_to_baseline: 1.12,
    lc_class: "industrial",
    state: "Bihar",
    cluster_size: 1,
  },
  {
    id: "HOT-010",
    name: "Hazira Heavy Chemical & Steel Corridor",
    location_name: "Surat, Gujarat",
    latitude: 21.1158,
    longitude: 72.6489,
    frp: 98.4,
    brightness: 351.2,
    confidence: 97,
    classification: "persistent_industrial",
    risk_score: 0.89,
    is_anomaly: false,
    facility_distance_km: 0.35,
    facility_type: "LNG Terminal & Metallurgical Plant",
    persistence: 31,
    timestamp: "2026-09-15T00:15:00Z",
    sensor: "VIIRS_NPP (375m)",
    frp_ratio_to_baseline: 1.2,
    lc_class: "industrial",
    state: "Gujarat",
    cluster_size: 2,
  },
  {
    id: "HOT-011",
    name: "Visakhapatnam Steel Complex Blast Furnace",
    location_name: "Visakhapatnam, Andhra Pradesh",
    latitude: 17.6322,
    longitude: 83.1812,
    frp: 74.5,
    brightness: 336.8,
    confidence: 91,
    classification: "industrial_fire",
    risk_score: 0.93,
    is_anomaly: true,
    facility_distance_km: 0.45,
    facility_type: "Integrated Steel Works & Coking Plant",
    persistence: 18,
    timestamp: "2026-09-14T23:45:00Z",
    sensor: "VIIRS_NOAA20 (375m)",
    frp_ratio_to_baseline: 4.1,
    lc_class: "industrial",
    state: "Andhra Pradesh",
    cluster_size: 3,
  },
  {
    id: "HOT-012",
    name: "Raniganj Coalfield Subsurface Mine Seam",
    location_name: "Paschim Bardhaman, West Bengal",
    latitude: 23.6214,
    longitude: 87.1147,
    frp: 58.7,
    brightness: 329.4,
    confidence: 87,
    classification: "coal_seam_fire",
    risk_score: 0.82,
    is_anomaly: false,
    facility_distance_km: 0.9,
    facility_type: "Subsurface Coal Seam Strata",
    persistence: 42,
    timestamp: "2026-09-14T23:15:00Z",
    sensor: "MODIS_Terra (1km)",
    frp_ratio_to_baseline: 1.28,
    lc_class: "mining",
    state: "West Bengal",
    cluster_size: 5,
  },
  {
    id: "HOT-013",
    name: "Karnal Rice Belt Post-Harvest Fire",
    location_name: "Karnal, Haryana",
    latitude: 29.6857,
    longitude: 76.9905,
    frp: 34.2,
    brightness: 318.5,
    confidence: 81,
    classification: "agricultural_burning",
    risk_score: 0.44,
    is_anomaly: false,
    facility_distance_km: 8.2,
    facility_type: "Paddy Farmland",
    persistence: 3,
    timestamp: "2026-09-14T22:50:00Z",
    sensor: "VIIRS_NPP (375m)",
    frp_ratio_to_baseline: 1.05,
    lc_class: "cropland",
    state: "Haryana",
    cluster_size: 6,
  },
  {
    id: "HOT-014",
    name: "Bandipur Dry Deciduous Forest Fire",
    location_name: "Chamarajanagar, Karnataka",
    latitude: 11.6667,
    longitude: 76.6333,
    frp: 62.0,
    brightness: 330.2,
    confidence: 86,
    classification: "wildfire",
    risk_score: 0.76,
    is_anomaly: false,
    facility_distance_km: 18.5,
    facility_type: "Protected Forest Reserve",
    persistence: 5,
    timestamp: "2026-09-14T22:20:00Z",
    sensor: "MODIS_Aqua (1km)",
    frp_ratio_to_baseline: 1.85,
    lc_class: "forest",
    state: "Karnataka",
    cluster_size: 4,
  },
  {
    id: "HOT-015",
    name: "Tarapur MIDC Chemical Zone Flare",
    location_name: "Palghar, Maharashtra",
    latitude: 19.8286,
    longitude: 72.6983,
    frp: 68.3,
    brightness: 334.6,
    confidence: 88,
    classification: "industrial_fire",
    risk_score: 0.89,
    is_anomaly: true,
    facility_distance_km: 0.6,
    facility_type: "Speciality Chemical Formulation Plant",
    persistence: 9,
    timestamp: "2026-09-14T21:45:00Z",
    sensor: "VIIRS_NPP (375m)",
    frp_ratio_to_baseline: 3.4,
    lc_class: "industrial",
    state: "Maharashtra",
    cluster_size: 2,
  },
  {
    id: "HOT-016",
    name: "Korba Super Thermal Power Complex",
    location_name: "Korba, Chhattisgarh",
    latitude: 22.3595,
    longitude: 82.6841,
    frp: 88.0,
    brightness: 345.5,
    confidence: 94,
    classification: "persistent_industrial",
    risk_score: 0.86,
    is_anomaly: false,
    facility_distance_km: 0.4,
    facility_type: "Thermal Power Station & Ash Handling",
    persistence: 26,
    timestamp: "2026-09-14T21:10:00Z",
    sensor: "VIIRS_NOAA20 (375m)",
    frp_ratio_to_baseline: 1.18,
    lc_class: "industrial",
    state: "Chhattisgarh",
    cluster_size: 2,
  },
  {
    id: "HOT-017",
    name: "Gir National Park Fringe Scrub Fire",
    location_name: "Junagadh, Gujarat",
    latitude: 21.134,
    longitude: 70.825,
    frp: 41.5,
    brightness: 320.1,
    confidence: 80,
    classification: "wildfire",
    risk_score: 0.68,
    is_anomaly: false,
    facility_distance_km: 12.0,
    facility_type: "Sanctuary Perimeter Buffer",
    persistence: 4,
    timestamp: "2026-09-14T20:30:00Z",
    sensor: "MODIS_Terra (1km)",
    frp_ratio_to_baseline: 1.4,
    lc_class: "scrub",
    state: "Gujarat",
    cluster_size: 3,
  },
  {
    id: "HOT-018",
    name: "Digboi Heritage Refinery Flare",
    location_name: "Tinsukia, Assam",
    latitude: 27.3822,
    longitude: 95.6311,
    frp: 62.4,
    brightness: 331.0,
    confidence: 89,
    classification: "persistent_industrial",
    risk_score: 0.85,
    is_anomaly: false,
    facility_distance_km: 0.3,
    facility_type: "Crude Distillation Unit Flare",
    persistence: 35,
    timestamp: "2026-09-14T19:50:00Z",
    sensor: "INSAT-3D (Geostationary)",
    frp_ratio_to_baseline: 1.1,
    lc_class: "industrial",
    state: "Assam",
    cluster_size: 1,
  },
];

/**
 * Generates dynamic multi-pass time-series for a hotspot to drive Recharts
 */
export function generateHotspotPassSeries(hotspot: HotSpot): {
  time: string;
  frp: number;
  baseline: number;
  ratio: number;
  satellite: string;
  isAnomaly: boolean;
}[] {
  const passes = Math.min(8, Math.max(4, Math.round(hotspot.persistence / 2)));
  const baseline = Number((hotspot.frp / (hotspot.frp_ratio_to_baseline || 1.0)).toFixed(1));
  const series = [];

  const baseDate = new Date(hotspot.timestamp);

  for (let i = passes - 1; i >= 0; i--) {
    const passDate = new Date(baseDate.getTime() - i * 3.5 * 3600 * 1000);
    const timeLabel = passDate.toLocaleTimeString("en-GB", {
      hour: "2-digit",
      minute: "2-digit",
      timeZone: "Asia/Kolkata",
    });

    let passFrp = baseline;
    if (i === 0) {
      passFrp = hotspot.frp;
    } else {
      // Historical variations around baseline
      const jitter = (Math.sin(i * 1.5) * 0.15 + 1.0);
      passFrp = Number((baseline * jitter).toFixed(1));
    }

    const currentRatio = Number((passFrp / baseline).toFixed(2));
    const isAnom = currentRatio >= 3.0;
    const satellites = ["VIIRS_NPP", "VIIRS_NOAA20", "MODIS_Terra", "INSAT-3D"];
    const sat = satellites[i % satellites.length];

    series.push({
      time: `${timeLabel} (${sat})`,
      frp: passFrp,
      baseline,
      ratio: currentRatio,
      satellite: sat,
      isAnomaly: isAnom,
    });
  }

  return series;
}
