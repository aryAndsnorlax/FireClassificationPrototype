import type { FireClassification } from "../types/hotSpot";

export const FIRE_CLASSES: FireClassification[] = [
  "industrial_fire",
  "persistent_industrial",
  "coal_seam_fire",
  "agricultural_burning",
  "wildfire",
  "unknown",
];

export const CLASS_COLORS: Record<FireClassification, string> = {
  industrial_fire: "#D32F2F",       // Red - Critical industrial fire
  persistent_industrial: "#E65100", // Dark Orange - Persistent industrial hotspot
  coal_seam_fire: "#795548",        // Brown - Subsurface coal seam fire
  agricultural_burning: "#F9A825",  // Amber/Yellow - Crop residue burning
  wildfire: "#C62828",              // Crimson - Forest / vegetation wildfire
  unknown: "#757575",               // Slate Grey - Unclassified anomaly
};

export const CLASS_LABELS: Record<FireClassification, string> = {
  industrial_fire: "Industrial Fire",
  persistent_industrial: "Persistent Industrial",
  coal_seam_fire: "Coal Seam Fire",
  agricultural_burning: "Agricultural Burning",
  wildfire: "Wildfire",
  unknown: "Unknown",
};

export function getRiskBadge(score: number): {
  label: string;
  color: string;
  bg: string;
  borderColor: string;
} {
  if (score >= 0.85) {
    return {
      label: "HIGH RISK (CRITICAL)",
      color: "#D32F2F",
      bg: "#FFEBEE",
      borderColor: "#FFCDD2",
    };
  }
  if (score >= 0.70) {
    return {
      label: "ACTIVE ALERT",
      color: "#E65100",
      bg: "#FFF3E0",
      borderColor: "#FFE0B2",
    };
  }
  if (score >= 0.50) {
    return {
      label: "MODERATE RISK",
      color: "#E67E22",
      bg: "#FFF8E1",
      borderColor: "#FFECB3",
    };
  }
  return {
    label: "LOW RISK",
    color: "#2E7D32",
    bg: "#E8F5E9",
    borderColor: "#C8E6C9",
  };
}