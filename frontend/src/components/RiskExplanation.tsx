import {
  Flame,
  Factory,
  RefreshCw,
  Zap,
  Info,
  CheckCircle,
} from "lucide-react";
import type { HotSpot } from "../types/hotSpot";

interface RiskExplanationProps {
  hotspot: HotSpot | null;
}

interface RiskFactor {
  title: string;
  value: string;
  severity: "high" | "medium" | "low";
  description: string;
  icon: typeof Flame;
}

export default function RiskExplanation({ hotspot }: RiskExplanationProps) {
  if (!hotspot) {
    return (
      <section className="risk-analysis-box empty">
        <div className="empty-state-content">
          <Info size={24} />
          <p>
            Select a hotspot to review the explainable risk attribution factors.
          </p>
        </div>
      </section>
    );
  }

  // Derive human-readable risk attribution factors dynamically from hotspot attributes
  const factors: RiskFactor[] = [];

  // 1. Thermal Output Factor
  if (hotspot.frp >= 60) {
    factors.push({
      title: "HIGH THERMAL POWER OUTPUT",
      value: `${hotspot.frp.toFixed(1)} MW`,
      severity: "high",
      description:
        "Elevated fire radiative power exceeding the 60 MW threshold, consistent with intensive industrial flare or uncontrolled combustion.",
      icon: Flame,
    });
  } else if (hotspot.frp >= 35) {
    factors.push({
      title: "MODERATE THERMAL FLUX",
      value: `${hotspot.frp.toFixed(1)} MW`,
      severity: "medium",
      description:
        "Radiative power higher than standard agricultural burning, requiring facility boundary verification.",
      icon: Flame,
    });
  } else {
    factors.push({
      title: "LOW THERMAL INTENSITY",
      value: `${hotspot.frp.toFixed(1)} MW`,
      severity: "low",
      description:
        "Thermal output within typical controlled open-field burning range.",
      icon: Flame,
    });
  }

  // 2. Facility Proximity Factor
  if (hotspot.facility_distance_km <= 0.5) {
    factors.push({
      title: "IMMEDIATE INDUSTRIAL PROXIMITY",
      value: `${(hotspot.facility_distance_km * 1000).toFixed(0)} m buffer`,
      severity: "high",
      description: `Located directly within the perimeter of ${hotspot.facility_type || "a registered industrial complex"}.`,
      icon: Factory,
    });
  } else if (hotspot.facility_distance_km <= 2.0) {
    factors.push({
      title: "NEAR INDUSTRIAL ASSET BOUNDARY",
      value: `${hotspot.facility_distance_km.toFixed(1)} km`,
      severity: "medium",
      description:
        "Inside the secondary 2.0 km industrial monitoring buffer zone.",
      icon: Factory,
    });
  } else {
    factors.push({
      title: "OUTSIDE INDUSTRIAL BUFFER",
      value: `${hotspot.facility_distance_km.toFixed(1)} km`,
      severity: "low",
      description:
        "Situated over 2.0 km from the nearest registered industrial asset.",
      icon: Factory,
    });
  }

  // 3. Multi-Pass Persistence Factor
  if (hotspot.persistence >= 10) {
    factors.push({
      title: "HIGH MULTI-PASS PERSISTENCE",
      value: `${hotspot.persistence} satellite passes`,
      severity: "high",
      description:
        "Repeated detections across multiple orbital cycles rule out brief reflections or transient sensor noise.",
      icon: RefreshCw,
    });
  } else if (hotspot.persistence >= 4) {
    factors.push({
      title: "RECURRING DETECTION CYCLE",
      value: `${hotspot.persistence} passes`,
      severity: "medium",
      description:
        "Detected across consecutive orbit cycles, indicating sustained heat source.",
      icon: RefreshCw,
    });
  } else {
    factors.push({
      title: "INITIAL RECONNAISSANCE PASS",
      value: `${hotspot.persistence} pass`,
      severity: "low",
      description:
        "Recently detected; awaiting subsequent orbit passes for persistence confirmation.",
      icon: RefreshCw,
    });
  }

  // 4. Baseline Statistical Anomaly
  if (hotspot.is_anomaly) {
    factors.push({
      title: "STATISTICAL BASELINE ANOMALY",
      value: "SIGMA > 3.0",
      severity: "high",
      description:
        "Thermal emission exceeds historical mean for this geographic tile by over 3 standard deviations.",
      icon: Zap,
    });
  }

  return (
    <section className="risk-analysis-box" aria-label="Risk Attribution Analysis">
      <div className="analysis-box-header">
        <div className="header-left">
          <span className="box-eyebrow">RISK ATTRIBUTION &amp; EXPLAINABILITY</span>
          <h3 className="box-title">Why This Hotspot Is Prioritized</h3>
        </div>

        <div className="score-badge-card">
          <span className="score-caption">COMPUTED RISK SCORE</span>
          <span className="score-big">
            {Math.round(hotspot.risk_score * 100)}%
          </span>
        </div>
      </div>

      <div className="factors-grid">
        {factors.map((factor) => {
          const Icon = factor.icon;
          const sevClass = `sev-${factor.severity}`;

          return (
            <div key={factor.title} className={`factor-card ${sevClass}`}>
              <div className="factor-top">
                <div className="factor-icon-wrap">
                  <Icon size={16} />
                </div>
                <div className="factor-title-col">
                  <h4 className="factor-name">{factor.title}</h4>
                  <span className="factor-measurement">{factor.value}</span>
                </div>
                <span className={`factor-status-pill ${sevClass}`}>
                  {factor.severity.toUpperCase()} IMPACT
                </span>
              </div>

              <p className="factor-text">{factor.description}</p>
            </div>
          );
        })}
      </div>

      <div className="analysis-disclaimer">
        <CheckCircle size={14} className="disclaimer-icon" />
        <span>
          <strong>Methodology Note:</strong> Risk score and attribution factors in this demonstration portal are evaluated deterministically from NASA FIRMS telemetry, OpenStreetMap industrial buffer distances, and orbital persistence metrics.
        </span>
      </div>
    </section>
  );
}
