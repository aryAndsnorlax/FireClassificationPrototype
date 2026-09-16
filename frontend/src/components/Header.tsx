import { useEffect, useState } from "react";
import { Radio, ShieldAlert, Activity, Server } from "lucide-react";
import { checkBackendHealth } from "../services/api";

interface HeaderProps {
  activeCount: number;
  criticalCount: number;
}

export default function Header({ activeCount, criticalCount }: HeaderProps) {
  const [timeStr, setTimeStr] = useState<string>("");
  const [backendOnline, setBackendOnline] = useState<boolean>(false);

  useEffect(() => {
    // Check backend health periodically
    async function verifyBackend() {
      const res = await checkBackendHealth();
      setBackendOnline(res.isOnline);
    }
    verifyBackend();
    const healthTimer = setInterval(verifyBackend, 15000);
    return () => clearInterval(healthTimer);
  }, []);

  useEffect(() => {
    function updateClock() {
      const now = new Date();
      // Display IST (Indian Standard Time, UTC+5:30)
      const options: Intl.DateTimeFormatOptions = {
        timeZone: "Asia/Kolkata",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
        hour12: false,
      };
      const istTime = new Intl.DateTimeFormat("en-GB", options).format(now);
      const dateStr = now.toLocaleDateString("en-GB", {
        day: "2-digit",
        month: "short",
        year: "numeric",
      });
      setTimeStr(`${dateStr} | ${istTime} IST`);
    }

    updateClock();
    const timer = setInterval(updateClock, 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <header className="institutional-header">
      {/* Subtle Tricolour Institutional Stripe */}
      <div className="tricolour-stripe" aria-hidden="true">
        <span className="stripe-saffron" />
        <span className="stripe-white" />
        <span className="stripe-green" />
      </div>

      <div className="header-main-bar">
        {/* Brand Area */}
        <div className="header-brand">
          <div className="brand-emblem" aria-label="AgniNetra Emblem">
            <svg
              width="40"
              height="40"
              viewBox="0 0 40 40"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
              className="emblem-svg"
            >
              {/* Outer Navy Ring */}
              <circle
                cx="20"
                cy="20"
                r="18"
                stroke="#000080"
                strokeWidth="2"
                fill="#FFFFFF"
              />
              {/* Inner geometric spokes representing monitoring radar / chakra */}
              <circle
                cx="20"
                cy="20"
                r="14"
                stroke="#000080"
                strokeWidth="0.75"
                strokeDasharray="2 2"
              />
              {/* Saffron fire crown top curve */}
              <path
                d="M20 7C21.5 11 25.5 13 25.5 17C25.5 21 22 23 20 23C18 23 14.5 21 14.5 17C14.5 13 18.5 11 20 7Z"
                fill="#FF9933"
              />
              {/* Inner core flame - white & navy */}
              <path
                d="M20 12C20.8 14.5 22.8 16 22.8 18.5C22.8 20.8 21.2 22 20 22C18.8 22 17.2 20.8 17.2 18.5C17.2 16 19.2 14.5 20 12Z"
                fill="#000080"
              />
              {/* Base Green arc representing terrestrial terrain */}
              <path
                d="M10 27C13 30 17 32 20 32C23 32 27 30 30 27"
                stroke="#138808"
                strokeWidth="2.5"
                strokeLinecap="round"
              />
            </svg>
          </div>

          <div className="brand-text">
            <div className="brand-title-wrap">
              <span className="brand-title">AGNINETRA</span>
              <span className="brand-demo-tag">DEMO PORTAL</span>
            </div>
            <div className="brand-subtitle">
              Industrial Fire Detection &amp; Monitoring System
            </div>
          </div>
        </div>

        {/* Right Status & Meta Area */}
        <div className="header-meta">
          <div
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "6px",
              padding: "4px 10px",
              borderRadius: "4px",
              fontSize: "11px",
              fontWeight: 700,
              backgroundColor: backendOnline ? "#ECFDF5" : "#EFF6FF",
              color: backendOnline ? "#065F46" : "#1E40AF",
              border: `1px solid ${backendOnline ? "#A7F3D0" : "#BFDBFE"}`,
            }}
          >
            {backendOnline ? (
              <>
                <span
                  style={{
                    width: "7px",
                    height: "7px",
                    borderRadius: "50%",
                    backgroundColor: "#10B981",
                  }}
                />
                <Server size={12} />
                <span>FASTAPI BACKEND: ONLINE (8000)</span>
              </>
            ) : (
              <>
                <span
                  style={{
                    width: "7px",
                    height: "7px",
                    borderRadius: "50%",
                    backgroundColor: "#3B82F6",
                  }}
                />
                <Activity size={12} />
                <span>DYNAMIC TELEMETRY ENGINE: ACTIVE</span>
              </>
            )}
          </div>

          {criticalCount > 0 && (
            <div className="meta-alert-pill">
              <ShieldAlert size={14} />
              <span>
                {criticalCount} Critical Alert{criticalCount > 1 ? "s" : ""}
              </span>
            </div>
          )}

          <div className="meta-sync-box">
            <div className="meta-sync-line">
              <Radio size={13} className="sync-icon active-spin" />
              <span>
                Satellite Sync: <strong>NASA FIRMS &bull; INSAT-3D</strong>
              </span>
            </div>
            <div className="meta-clock-line">
              <span className="target-count-badge">
                {activeCount} Active Detections
              </span>
              <span className="divider">&bull;</span>
              <span className="time-display">{timeStr || "IST"}</span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}