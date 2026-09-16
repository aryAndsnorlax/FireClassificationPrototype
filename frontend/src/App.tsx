import { useEffect, useState, useMemo } from "react";
import Header from "./components/Header";
import Navigation, { type NavTabId } from "./components/Navigation";
import Dashboard from "./pages/Dashboard";
import FireMapPage from "./pages/FireMapPage";
import AlertsPage from "./pages/AlertsPage";
import HotspotAnalysisPage from "./pages/HotspotAnalysisPage";
import ActivityPage from "./pages/ActivityPage";
import AboutPage from "./pages/AboutPage";
import { getHotspots, subscribeHotspots } from "./services/api";
import type { HotSpot } from "./types/hotSpot";

export default function App() {
  const [activeTab, setActiveTab] = useState<NavTabId>("dashboard");
  const [allHotspots, setAllHotspots] = useState<HotSpot[]>([]);
  const [selectedHotspot, setSelectedHotspot] = useState<HotSpot | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  // Subscribe to live telemetry simulation and data changes
  useEffect(() => {
    const unsubscribe = subscribeHotspots((updated) => {
      setAllHotspots(updated);
      setSelectedHotspot((prev) => {
        if (!prev) return updated[0] || null;
        const matching = updated.find((h) => h.id === prev.id);
        return matching || prev;
      });
    });
    return unsubscribe;
  }, []);

  // Initial load
  useEffect(() => {
    async function loadData() {
      setLoading(true);
      try {
        const data = await getHotspots();
        setAllHotspots(data);

        // Default selection: highest risk industrial hotspot
        if (data.length > 0) {
          const sorted = [...data].sort((a, b) => b.risk_score - a.risk_score);
          setSelectedHotspot(sorted[0]);
        }
      } catch (err) {
        console.error("Failed to load hotspots:", err);
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, []);

  // Alert and critical counts
  const alertCount = useMemo(() => {
    return allHotspots.filter((h) => h.risk_score >= 0.7).length;
  }, [allHotspots]);

  const criticalCount = useMemo(() => {
    return allHotspots.filter((h) => h.risk_score >= 0.85).length;
  }, [allHotspots]);

  // Unified navigation handler
  const handleNavigate = (tab: NavTabId, hotspot?: HotSpot) => {
    if (hotspot) {
      setSelectedHotspot(hotspot);
    }
    setActiveTab(tab);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <div className="portal-root">
      {/* Top Institutional Header */}
      <Header
        activeCount={allHotspots.length}
        criticalCount={criticalCount}
      />

      {/* Main Top Navigation Menu */}
      <Navigation
        activeTab={activeTab}
        onTabChange={(tab) => handleNavigate(tab)}
        alertCount={alertCount}
        criticalCount={criticalCount}
      />

      {/* Main Page Workspace */}
      <main className="portal-main-body">
        {loading ? (
          <div className="portal-loading-container">
            <div className="gov-spinner" />
            <div className="loading-label">
              Connecting to Satellite Surveillance Telemetry...
            </div>
          </div>
        ) : (
          <>
            {activeTab === "dashboard" && (
              <Dashboard
                hotspots={allHotspots}
                selectedHotspot={selectedHotspot}
                onSelectHotspot={setSelectedHotspot}
                onNavigate={handleNavigate}
              />
            )}

            {activeTab === "map" && (
              <FireMapPage
                hotspots={allHotspots}
                selectedHotspot={selectedHotspot}
                onSelectHotspot={setSelectedHotspot}
                onNavigate={handleNavigate}
              />
            )}

            {activeTab === "alerts" && (
              <AlertsPage
                hotspots={allHotspots}
                selectedHotspot={selectedHotspot}
                onSelectHotspot={setSelectedHotspot}
                onNavigate={handleNavigate}
              />
            )}

            {activeTab === "analysis" && (
              <HotspotAnalysisPage
                hotspots={allHotspots}
                selectedHotspot={selectedHotspot}
                onSelectHotspot={setSelectedHotspot}
                onNavigate={handleNavigate}
              />
            )}

            {activeTab === "activity" && (
              <ActivityPage
                hotspots={allHotspots}
                selectedHotspot={selectedHotspot}
                onSelectHotspot={setSelectedHotspot}
                onNavigate={handleNavigate}
              />
            )}

            {activeTab === "about" && <AboutPage />}
          </>
        )}
      </main>

      {/* Institutional Portal Footer */}
      <footer className="portal-footer">
        <div className="footer-tricolour-stripe" aria-hidden="true">
          <span className="stripe-saffron" />
          <span className="stripe-white" />
          <span className="stripe-green" />
        </div>

        <div className="portal-footer-container">
          <div className="footer-col-brand">
            <div className="footer-brand-title">AGNINETRA</div>
            <div className="footer-brand-sub">
              Industrial Fire Detection &amp; Monitoring System
            </div>
            <p className="footer-disclaimer-text">
              National GIS Demonstration Prototype &bull; For Technical Evaluation &amp; Demonstration Purposes Only.
            </p>
          </div>

          <div className="footer-col-nav">
            <span className="footer-heading">SYSTEM MODULES</span>
            <ul className="footer-links">
              <li>
                <button type="button" onClick={() => handleNavigate("dashboard")}>
                  Dashboard Overview
                </button>
              </li>
              <li>
                <button type="button" onClick={() => handleNavigate("map")}>
                  GIS Fire Map
                </button>
              </li>
              <li>
                <button type="button" onClick={() => handleNavigate("alerts")}>
                  Incident Alerts &amp; Triage
                </button>
              </li>
            </ul>
          </div>

          <div className="footer-col-nav">
            <span className="footer-heading">DIAGNOSTICS &amp; DOCS</span>
            <ul className="footer-links">
              <li>
                <button type="button" onClick={() => handleNavigate("analysis")}>
                  Hotspot Risk Analysis
                </button>
              </li>
              <li>
                <button type="button" onClick={() => handleNavigate("activity")}>
                  Temporal Activity Monitoring
                </button>
              </li>
              <li>
                <button type="button" onClick={() => handleNavigate("about")}>
                  System Architecture
                </button>
              </li>
            </ul>
          </div>
        </div>

        <div className="footer-bottom-bar">
          <div className="footer-bottom-content">
            <span>&copy; {new Date().getFullYear()} AgniNetra Demonstration System &bull; Telemetry: NASA FIRMS / ISRO INSAT-3D</span>
            <span>Frontend Prototype &bull; React + Leaflet + Recharts</span>
          </div>
        </div>
      </footer>
    </div>
  );
}