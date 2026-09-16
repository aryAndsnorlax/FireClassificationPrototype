import { useState, useMemo } from "react";
import {
  Cpu,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
} from "lucide-react";
import { evaluateRuleBasedLabel } from "../services/telemetryEngine";
import { CLASS_LABELS, CLASS_COLORS, getRiskBadge } from "../data/fireClasses";
import type { HotSpot } from "../types/hotSpot";

interface PipelineSimulatorProps {
  hotspot?: HotSpot | null;
  onApplyToHotspot?: (updatedParams: Partial<HotSpot>) => void;
}

export default function PipelineSimulator({
  hotspot,
  onApplyToHotspot,
}: PipelineSimulatorProps) {
  // Initialize from selected hotspot or realistic industrial defaults
  const [distanceM, setDistanceM] = useState<number>(
    hotspot ? Math.round(hotspot.facility_distance_km * 1000) : 400
  );
  const [frp, setFrp] = useState<number>(hotspot ? hotspot.frp : 85.0);
  const [baselineFrp, setBaselineFrp] = useState<number>(
    hotspot
      ? Math.round(hotspot.frp / (hotspot.frp_ratio_to_baseline || 1.2))
      : 22.0
  );
  const [persistencePct, setPersistencePct] = useState<number>(
    hotspot ? Math.min(100, Math.round((hotspot.persistence / 20) * 100)) : 70
  );
  const [lcClass, setLcClass] = useState<string>(
    hotspot?.lc_class || "industrial"
  );
  const [state, setState] = useState<string>(hotspot?.state || "Punjab");
  const [month, setMonth] = useState<number>(10); // Default to October harvest

  // Calculate live FRP ratio
  const frpRatio = baselineFrp > 0 ? Number((frp / baselineFrp).toFixed(2)) : 1.0;
  const persistenceScore = persistencePct / 100;

  // Run dynamic evaluation using the exact project logic
  const evaluation = useMemo(() => {
    return evaluateRuleBasedLabel({
      distance_to_facility_m: distanceM,
      persistence_score: persistenceScore,
      frp_ratio_to_baseline: frpRatio,
      lc_class: lcClass,
      state,
      month,
      frp,
    });
  }, [distanceM, persistenceScore, frpRatio, lcClass, state, month, frp]);

  const classColor = CLASS_COLORS[evaluation.classification];
  const riskBadge = getRiskBadge(evaluation.risk_score);

  const handleApply = () => {
    if (onApplyToHotspot && hotspot) {
      onApplyToHotspot({
        frp,
        classification: evaluation.classification,
        risk_score: evaluation.risk_score,
        is_anomaly: evaluation.is_anomaly,
        facility_distance_km: Number((distanceM / 1000).toFixed(2)),
        frp_ratio_to_baseline: frpRatio,
        persistence: Math.max(1, Math.round(persistenceScore * 20)),
      });
    }
  };

  const handlePreset = (type: "accident" | "flare" | "stubble" | "wildfire" | "coal") => {
    switch (type) {
      case "accident":
        setDistanceM(350);
        setFrp(98.0);
        setBaselineFrp(24.0); // 4.08x ratio
        setPersistencePct(75);
        setLcClass("industrial");
        break;
      case "flare":
        setDistanceM(300);
        setFrp(42.0);
        setBaselineFrp(38.0); // 1.1x ratio
        setPersistencePct(85);
        setLcClass("industrial");
        break;
      case "stubble":
        setDistanceM(7500);
        setFrp(32.0);
        setBaselineFrp(30.0);
        setPersistencePct(15);
        setLcClass("cropland");
        setState("Punjab");
        setMonth(10);
        break;
      case "wildfire":
        setDistanceM(14000);
        setFrp(65.0);
        setBaselineFrp(20.0);
        setPersistencePct(25);
        setLcClass("forest");
        break;
      case "coal":
        setDistanceM(900);
        setFrp(60.0);
        setBaselineFrp(45.0);
        setPersistencePct(90);
        setLcClass("mining");
        break;
    }
  };

  return (
    <div className="gov-card pipeline-simulator-card">
      <div className="gov-card-header">
        <div className="card-header-title">
          <Cpu size={16} />
          <span>Interactive Feature &amp; Rule Classification Lab</span>
        </div>
        <div className="card-header-meta-badge">
          Rule-Based Weak Labeling &bull; <code>src/labeling/rule_based_labels.py</code>
        </div>
      </div>

      <div style={{ padding: "16px" }}>
        {/* Preset scenario buttons */}
        <div style={{ marginBottom: "16px" }}>
          <div style={{ fontSize: "11px", fontWeight: 700, color: "#64748b", marginBottom: "6px" }}>
            PRESET SCENARIO INJECTION:
          </div>
          <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
            <button
              type="button"
              className="tab-filter-btn"
              onClick={() => handlePreset("accident")}
              style={{ borderLeft: "3px solid #D32F2F" }}
            >
              Industrial Plant Fire (&ge;3x Spike)
            </button>
            <button
              type="button"
              className="tab-filter-btn"
              onClick={() => handlePreset("flare")}
              style={{ borderLeft: "3px solid #E65100" }}
            >
              Nominal Refinery Flare (Steady)
            </button>
            <button
              type="button"
              className="tab-filter-btn"
              onClick={() => handlePreset("stubble")}
              style={{ borderLeft: "3px solid #F9A825" }}
            >
              Punjab Stubble Burning (Oct/Nov)
            </button>
            <button
              type="button"
              className="tab-filter-btn"
              onClick={() => handlePreset("wildfire")}
              style={{ borderLeft: "3px solid #C62828" }}
            >
              Wildfire (Canopy Forest)
            </button>
            <button
              type="button"
              className="tab-filter-btn"
              onClick={() => handlePreset("coal")}
              style={{ borderLeft: "3px solid #795548" }}
            >
              Coalfield Pit Smolder (Mining)
            </button>
          </div>
        </div>

        {/* Two-Column Grid: Sliders & Controls on Left, Real-Time Inference on Right */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1.2fr 1fr",
            gap: "20px",
          }}
        >
          {/* Controls Column */}
          <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
            {/* Facility Proximity */}
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", marginBottom: "4px" }}>
                <span>
                  <strong>Facility Buffer Distance:</strong>{" "}
                  <span style={{ color: distanceM <= 1000 ? "#D32F2F" : "#138808", fontWeight: 700 }}>
                    {distanceM} m {distanceM <= 1000 ? "(≤ 1000m Buffer Active)" : "(Outside Buffer)"}
                  </span>
                </span>
                <span style={{ color: "#64748b", fontSize: "11px" }}>Threshold: 1,000m</span>
              </div>
              <input
                type="range"
                min="50"
                max="10000"
                step="50"
                value={distanceM}
                onChange={(e) => setDistanceM(Number(e.target.value))}
                style={{ width: "100%", accentColor: distanceM <= 1000 ? "#D32F2F" : "#000080" }}
              />
            </div>

            {/* Fire Radiative Power (FRP) & Baseline */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
              <div>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", marginBottom: "4px" }}>
                  <span>
                    <strong>Observed FRP:</strong> {frp} MW
                  </span>
                </div>
                <input
                  type="range"
                  min="5"
                  max="200"
                  step="1"
                  value={frp}
                  onChange={(e) => setFrp(Number(e.target.value))}
                  style={{ width: "100%", accentColor: "#FF9933" }}
                />
              </div>

              <div>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", marginBottom: "4px" }}>
                  <span>
                    <strong>Location Baseline FRP:</strong> {baselineFrp} MW
                  </span>
                </div>
                <input
                  type="range"
                  min="5"
                  max="100"
                  step="1"
                  value={baselineFrp}
                  onChange={(e) => setBaselineFrp(Number(e.target.value))}
                  style={{ width: "100%", accentColor: "#64748b" }}
                />
              </div>
            </div>

            {/* Calculated Ratio Badge */}
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                padding: "8px 12px",
                backgroundColor: frpRatio >= 3.0 ? "#FEF2F2" : "#F8FAFC",
                border: `1px solid ${frpRatio >= 3.0 ? "#F87171" : "#E2E8F0"}`,
                borderRadius: "4px",
                fontSize: "12px",
              }}
            >
              <span>
                <strong>Calculated FRP Ratio (FRP / Baseline):</strong>
              </span>
              <strong style={{ color: frpRatio >= 3.0 ? "#DC2626" : "#1E293B", fontSize: "14px" }}>
                {frpRatio.toFixed(2)}x {frpRatio >= 3.0 ? "(>= 3.0x ACCIDENT TRIGGER)" : "(Nominal variation)"}
              </strong>
            </div>

            {/* Persistence & Land Cover */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
              <div>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", marginBottom: "4px" }}>
                  <span>
                    <strong>Persistence Frequency:</strong> {persistencePct}%
                  </span>
                  <span style={{ color: "#64748b", fontSize: "11px" }}>Threshold: 60%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  step="5"
                  value={persistencePct}
                  onChange={(e) => setPersistencePct(Number(e.target.value))}
                  style={{ width: "100%", accentColor: persistencePct >= 60 ? "#E65100" : "#64748b" }}
                />
              </div>

              <div>
                <label style={{ fontSize: "12px", fontWeight: 700, display: "block", marginBottom: "4px" }}>
                  Land Cover Classification:
                </label>
                <select
                  value={lcClass}
                  onChange={(e) => setLcClass(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "6px 8px",
                    borderRadius: "4px",
                    border: "1px solid #CBD5E1",
                    fontSize: "12px",
                  }}
                >
                  <option value="industrial">Industrial Facility / Urban</option>
                  <option value="mining">Mining / Coal Extraction</option>
                  <option value="cropland">Agricultural Cropland</option>
                  <option value="forest">Dense Forest Canopy</option>
                  <option value="scrub">Dry Scrub / Shrubland</option>
                  <option value="grassland">Open Grassland</option>
                  <option value="other">Other / Water / Wetland</option>
                </select>
              </div>
            </div>

            {/* Stubble season inputs if cropland */}
            {lcClass === "cropland" && (
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "1fr 1fr",
                  gap: "12px",
                  padding: "10px",
                  backgroundColor: "#FEF3C7",
                  border: "1px solid #FCD34D",
                  borderRadius: "4px",
                }}
              >
                <div>
                  <label style={{ fontSize: "11px", fontWeight: 700, display: "block", marginBottom: "3px" }}>
                    State / Territory:
                  </label>
                  <select
                    value={state}
                    onChange={(e) => setState(e.target.value)}
                    style={{ width: "100%", padding: "4px 6px", fontSize: "11px" }}
                  >
                    <option value="Punjab">Punjab (Stubble Target)</option>
                    <option value="Haryana">Haryana (Stubble Target)</option>
                    <option value="Uttar Pradesh">Uttar Pradesh (Stubble Target)</option>
                    <option value="Gujarat">Gujarat</option>
                    <option value="Jharkhand">Jharkhand</option>
                    <option value="Odisha">Odisha</option>
                  </select>
                </div>
                <div>
                  <label style={{ fontSize: "11px", fontWeight: 700, display: "block", marginBottom: "3px" }}>
                    Harvest Month:
                  </label>
                  <select
                    value={month}
                    onChange={(e) => setMonth(Number(e.target.value))}
                    style={{ width: "100%", padding: "4px 6px", fontSize: "11px" }}
                  >
                    <option value={10}>October (Peak Stubble)</option>
                    <option value={11}>November (Late Stubble)</option>
                    <option value={4}>April (Wheat Harvest)</option>
                    <option value={7}>July (Monsoon Off-Season)</option>
                  </select>
                </div>
              </div>
            )}
          </div>

          {/* Results Column */}
          <div
            style={{
              backgroundColor: "#F8FAFC",
              border: "1px solid #E2E8F0",
              borderRadius: "4px",
              padding: "14px",
              display: "flex",
              flexDirection: "column",
              justifyContent: "space-between",
            }}
          >
            <div>
              <div style={{ fontSize: "10px", fontWeight: 700, letterSpacing: "0.5px", color: "#64748b", marginBottom: "6px" }}>
                PIPELINE INFERENCE RESULTS
              </div>

              {/* Classification Label Result */}
              <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "12px" }}>
                <span
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "6px",
                    padding: "6px 12px",
                    borderRadius: "4px",
                    fontSize: "13px",
                    fontWeight: 700,
                    backgroundColor: `${classColor}18`,
                    color: classColor,
                    border: `1px solid ${classColor}`,
                  }}
                >
                  <span
                    style={{
                      width: "8px",
                      height: "8px",
                      borderRadius: "50%",
                      backgroundColor: classColor,
                    }}
                  />
                  {CLASS_LABELS[evaluation.classification]}
                </span>

                <span
                  style={{
                    padding: "4px 8px",
                    borderRadius: "4px",
                    fontSize: "11px",
                    fontWeight: 700,
                    backgroundColor: riskBadge.bg,
                    color: riskBadge.color,
                    border: `1px solid ${riskBadge.borderColor}`,
                  }}
                >
                  Risk: {Math.round(evaluation.risk_score * 100)}% &bull; {riskBadge.label}
                </span>
              </div>

              {/* Anomaly Badge */}
              <div style={{ marginBottom: "12px" }}>
                {evaluation.is_anomaly ? (
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "6px",
                      padding: "6px 10px",
                      backgroundColor: "#FEE2E2",
                      color: "#991B1B",
                      border: "1px solid #F87171",
                      borderRadius: "4px",
                      fontSize: "11px",
                      fontWeight: 700,
                    }}
                  >
                    <AlertTriangle size={14} />
                    <span>EMERGENCY ANOMALY FLAGGED: FRP spikes 3x baseline near industrial asset</span>
                  </div>
                ) : (
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "6px",
                      padding: "6px 10px",
                      backgroundColor: "#ECFDF5",
                      color: "#065F46",
                      border: "1px solid #A7F3D0",
                      borderRadius: "4px",
                      fontSize: "11px",
                      fontWeight: 600,
                    }}
                  >
                    <CheckCircle2 size={14} />
                    <span>NOMINAL BEHAVIOUR: Operational envelope within steady-state variance</span>
                  </div>
                )}
              </div>

              {/* Step-by-Step Decision Trace */}
              <div style={{ fontSize: "11px", marginBottom: "8px" }}>
                <strong style={{ color: "#334155" }}>Decision Path Execution:</strong>
                <ul
                  style={{
                    margin: "6px 0 0 0",
                    paddingLeft: "16px",
                    color: "#475569",
                    fontSize: "11px",
                    lineHeight: "1.4",
                  }}
                >
                  {evaluation.decisionPath.map((step, i) => (
                    <li key={i} style={{ marginBottom: "4px" }}>
                      {step}
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            {/* Apply Button if connected to active hotspot */}
            {hotspot && onApplyToHotspot && (
              <button
                type="button"
                className="gov-action-btn primary"
                onClick={handleApply}
                style={{ width: "100%", justifyContent: "center", marginTop: "12px" }}
              >
                <RefreshCw size={13} />
                <span>Apply Inferred Parameters to Incident #{hotspot.id}</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
