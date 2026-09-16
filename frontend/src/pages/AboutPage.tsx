import {
  Layers,
  Cpu,
  Database,
  Satellite,
  ShieldCheck,
  CheckCircle,
  FileCode,
  ArrowRight,
  AlertTriangle,
  Radio,
} from "lucide-react";
import PageHeader from "../components/PageHeader";

export default function AboutPage() {
  const steps = [
    {
      num: "01",
      title: "Data Ingestion",
      subtitle: "FIRMS + OSM + Land Cover",
      desc: "NASA FIRMS thermal anomalies, OpenStreetMap industrial polygons, and Copernicus/Bhuvan land cover raster datasets.",
      icon: Satellite,
    },
    {
      num: "02",
      title: "Feature Engineering",
      subtitle: "Spatial & Temporal Signals",
      desc: "Spatial joins to industrial assets (1km buffer), 1km grid-cell bucketing, and historical persistence scores.",
      icon: Layers,
    },
    {
      num: "03",
      title: "Persistence & Clustering",
      subtitle: "Baseline Tracking",
      desc: "Distinguishing normal steady-state flare operations from sudden 3-6x FRP spikes at the same location.",
      icon: Database,
    },
    {
      num: "04",
      title: "Weak Labeling",
      subtitle: "Rule-Based Heuristics",
      desc: "Deterministic rule-based weak labeling bootstrapping ground truth from facility distance and temporal recurrence.",
      icon: Cpu,
    },
    {
      num: "05",
      title: "ML Classification",
      subtitle: "XGBoost Classifier",
      desc: "Gradient-boosted decision trees trained with location-safe cross-validation to prevent persistent source leakage.",
      icon: ShieldCheck,
    },
    {
      num: "06",
      title: "GIS & API Delivery",
      subtitle: "PostGIS + FastAPI + AgniNetra",
      desc: "Spatial indexing in PostGIS, low-latency GeoJSON streaming via FastAPI, and decision triage on the AgniNetra portal.",
      icon: FileCode,
    },
  ];

  return (
    <div className="portal-page-container">
      <PageHeader
        category="TECHNICAL SPECIFICATIONS &amp; ARCHITECTURE"
        title="About AgniNetra System Architecture"
        subtitle="End-to-end telemetry pipeline for early detection, classification, and risk monitoring of industrial fire incidents."
        badge="DEMONSTRATION PROTOTYPE"
      />

      {/* Architecture Flow Diagram */}
      <div className="gov-card arch-flow-card">
        <div className="gov-card-header">
          <div className="card-header-title">
            <Layers size={16} />
            <span>End-to-End System Processing Pipeline</span>
          </div>
          <div
            style={{
              fontSize: "11px",
              fontFamily: "monospace",
              color: "#000080",
              fontWeight: 600,
            }}
          >
            FIRMS + OSM + Land Cover &rarr; Ingestion &rarr; Features &rarr; XGBoost &rarr; PostGIS &rarr; FastAPI &rarr; AgniNetra
          </div>
        </div>

        <div className="arch-flow-stepper">
          {steps.map((step, idx) => {
            const Icon = step.icon;
            return (
              <div key={step.num} className="arch-step-box">
                <div className="step-badge-number">{step.num}</div>
                <div className="step-icon-wrap">
                  <Icon size={20} />
                </div>
                <h4 className="step-title">{step.title}</h4>
                <div className="step-sub">{step.subtitle}</div>
                <p className="step-desc">{step.desc}</p>
                {idx < steps.length - 1 && (
                  <div className="step-connector-arrow">
                    <ArrowRight size={16} />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Data Fusion: The 4 Core Signals */}
      <div className="gov-card" style={{ marginBottom: "20px" }}>
        <div className="gov-card-header">
          <div className="card-header-title">
            <Radio size={16} />
            <span>Multi-Source Data Fusion: The 4 Primary Detection Signals</span>
          </div>
        </div>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
            gap: "16px",
            padding: "16px",
          }}
        >
          <div style={{ borderLeft: "3px solid #000080", paddingLeft: "12px" }}>
            <strong style={{ fontSize: "13px", color: "#1a1a1a" }}>1. Spatial Proximity</strong>
            <p style={{ fontSize: "12px", color: "#555", margin: "4px 0 0 0" }}>
              OSM industrial polygon buffer matching (1,000m radius) cross-references manufacturing plants, refineries, chemical hubs, and mines.
            </p>
          </div>
          <div style={{ borderLeft: "3px solid #E65100", paddingLeft: "12px" }}>
            <strong style={{ fontSize: "13px", color: "#1a1a1a" }}>2. Temporal Persistence</strong>
            <p style={{ fontSize: "12px", color: "#555", margin: "4px 0 0 0" }}>
              Grid-based multi-orbit pass frequency distinguishes routine industrial flares (&ge;10 passes) from sudden transient fires.
            </p>
          </div>
          <div style={{ borderLeft: "3px solid #D32F2F", paddingLeft: "12px" }}>
            <strong style={{ fontSize: "13px", color: "#1a1a1a" }}>3. Thermal Intensity Ratio</strong>
            <p style={{ fontSize: "12px", color: "#555", margin: "4px 0 0 0" }}>
              FRP ratio to location baseline (&ge;3.0x threshold) flags industrial accidents and uncontrolled explosions vs baseline flares.
            </p>
          </div>
          <div style={{ borderLeft: "3px solid #F9A825", paddingLeft: "12px" }}>
            <strong style={{ fontSize: "13px", color: "#1a1a1a" }}>4. Land Cover Seasonality</strong>
            <p style={{ fontSize: "12px", color: "#555", margin: "4px 0 0 0" }}>
              Cropland classification combined with state-level harvest calendars (Punjab/Haryana in Oct-Nov) isolates agricultural burning.
            </p>
          </div>
        </div>
      </div>

      {/* Official Prototype Disclaimer Alert */}
      <div className="gov-card disclaimer-card">
        <div className="disclaimer-header">
          <CheckCircle size={18} className="text-green" />
          <span>Prototype Demonstration Notice &amp; Data Provenance</span>
        </div>
        <div className="disclaimer-body">
          <p>
            <strong>AgniNetra</strong> is currently operating as an{" "}
            <strong>institutional frontend demonstration prototype</strong> using representative telemetry records (e.g., Ludhiana Focal Point, Jamnagar Petrochemical Complex, Jharia Coalfields, Amritsar agricultural clusters).
          </p>
          <p>
            The backend service architecture connects directly to:
            <br />
            <code>
              src/ingestion (FIRMS/OSM) &rarr; src/features &rarr; src/models (XGBoost) &rarr; PostgreSQL / PostGIS Spatial DB &rarr; FastAPI (/hotspots, /alerts) &rarr; AgniNetra UI
            </code>
          </p>
          <p className="mb-0">
            All API abstractions are centralized in <code>src/services/api.ts</code>, enabling seamless streaming from the local FastAPI service on port 8000 when active, with automatic fallback to local demonstration data when offline.
          </p>
        </div>
      </div>

      {/* Core Technical Specifications & Stated Limitations Grid */}
      <div className="about-specs-grid">
        <div className="gov-card">
          <div className="gov-card-header">
            <div className="card-header-title">
              <Satellite size={16} />
              <span>Satellite Sensor Specifications</span>
            </div>
          </div>
          <div className="specs-list">
            <div className="spec-item">
              <strong>VIIRS (Suomi-NPP / NOAA-20):</strong>
              <span>375m high spatial resolution I-band (I4 3.74&mu;m &amp; I5 11.45&mu;m), ideal for pinpointing plant-scale fires.</span>
            </div>
            <div className="spec-item">
              <strong>MODIS (Terra &amp; Aqua):</strong>
              <span>1km spatial resolution, 36 spectral bands, calibrated fire radiative power (FRP) measurements.</span>
            </div>
            <div className="spec-item">
              <strong>INSAT-3D &amp; 3DR:</strong>
              <span>Geostationary continuous monitoring over the Indian subcontinent with half-hourly radiometric updates.</span>
            </div>
          </div>
        </div>

        <div className="gov-card">
          <div className="gov-card-header">
            <div className="card-header-title">
              <AlertTriangle size={16} style={{ color: "#E65100" }} />
              <span>Operational Limitations (Stated Upfront)</span>
            </div>
          </div>
          <div className="specs-list">
            <div className="spec-item">
              <strong>Satellite Revisit Latency:</strong>
              <span>Polar satellites (VIIRS/MODIS) overpass 2&ndash;4 times daily, leading to ~3&ndash;4 hour latency between detection and availability.</span>
            </div>
            <div className="spec-item">
              <strong>Spatial Resolution Trade-offs:</strong>
              <span>INSAT geostationary sensors provide 30-minute rapid updates but at ~4km coarse resolution, requiring polar sensor fusion for precision.</span>
            </div>
            <div className="spec-item">
              <strong>Weak-Label Heuristic Noise:</strong>
              <span>Initial weak labels rely on facility buffers; unusual high-intensity flares can occasionally trigger review flags prior to ML convergence.</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
