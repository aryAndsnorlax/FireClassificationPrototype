import {
  LayoutDashboard,
  Map,
  BellRing,
  Crosshair,
  Activity,
  Info,
} from "lucide-react";

export type NavTabId =
  | "dashboard"
  | "map"
  | "alerts"
  | "analysis"
  | "activity"
  | "about";

interface NavigationProps {
  activeTab: NavTabId;
  onTabChange: (tab: NavTabId) => void;
  alertCount?: number;
  criticalCount?: number;
}

interface TabItem {
  id: NavTabId;
  label: string;
  icon: typeof LayoutDashboard;
  badge?: number;
}

export default function Navigation({
  activeTab,
  onTabChange,
  alertCount = 0,
  criticalCount = 0,
}: NavigationProps) {
  const tabs: TabItem[] = [
    { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
    { id: "map", label: "Fire Map", icon: Map },
    {
      id: "alerts",
      label: "Alerts",
      icon: BellRing,
      badge: alertCount > 0 ? alertCount : undefined,
    },
    { id: "analysis", label: "Hotspot Analysis", icon: Crosshair },
    { id: "activity", label: "Activity / Monitoring", icon: Activity },
    { id: "about", label: "About System", icon: Info },
  ];

  return (
    <nav className="portal-navigation" aria-label="Portal Navigation Bar">
      <div className="portal-nav-container">
        <ul className="portal-nav-list" role="tablist">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;

            return (
              <li key={tab.id} role="presentation" className="portal-nav-item">
                <button
                  type="button"
                  role="tab"
                  aria-selected={isActive}
                  className={`portal-nav-btn ${isActive ? "active" : ""}`}
                  onClick={() => onTabChange(tab.id)}
                >
                  <Icon size={16} className="nav-icon" />
                  <span>{tab.label}</span>
                  {tab.badge !== undefined && (
                    <span
                      className={`nav-badge ${
                        criticalCount > 0 && tab.id === "alerts"
                          ? "critical-badge"
                          : ""
                      }`}
                    >
                      {tab.badge}
                    </span>
                  )}
                </button>
              </li>
            );
          })}
        </ul>
      </div>
    </nav>
  );
}
