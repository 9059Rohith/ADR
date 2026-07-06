"use client";

import { useState, useEffect, useCallback } from "react";

/**
 * SentinelArena — Organizer Control Room Dashboard
 *
 * Features:
 * - Live venue heatmap with zone-colored density overlays
 * - Crowd advisory feed with ARIA live regions
 * - Decision Copilot panel with approve/reject actions
 * - Incident management overview
 * - Real-time WebSocket updates
 */

// ── Types ──
interface ZoneDensity {
  zone_id: string;
  zone_name: string;
  current_density_pct: number;
  ewma_density_pct: number;
  trend_direction: "rising" | "falling" | "stable";
  trend_rate_pct_per_min: number;
  severity: "normal" | "warning" | "critical" | "emergency";
  projected_time_to_threshold_min: number | null;
  current_count: number;
  capacity: number;
}

interface Decision {
  decision_id: string;
  recommendation: string;
  sources: string[];
  status: string;
  created_at: string;
}

interface Advisory {
  id: string;
  zone_name: string;
  severity: string;
  message: string;
  time: string;
}

// ── Zone Layout for Heatmap ──
const ZONE_LAYOUT: Record<
  string,
  { left: string; top: string; width: string; height: string }
> = {
  "zone-a": { left: "5%", top: "35%", width: "15%", height: "30%" },
  "zone-b": { left: "22%", top: "5%", width: "18%", height: "25%" },
  "zone-c": { left: "42%", top: "5%", width: "20%", height: "25%" },
  "zone-d": { left: "22%", top: "70%", width: "18%", height: "25%" },
  "zone-e": { left: "42%", top: "70%", width: "20%", height: "25%" },
  "zone-f": { left: "64%", top: "35%", width: "15%", height: "30%" },
  "zone-g": { left: "80%", top: "5%", width: "15%", height: "20%" },
  "zone-h": { left: "80%", top: "75%", width: "15%", height: "20%" },
  "zone-i": { left: "80%", top: "35%", width: "15%", height: "30%" },
  "zone-j": { left: "22%", top: "32%", width: "40%", height: "36%" },
  "zone-k": { left: "42%", top: "32%", width: "20%", height: "18%" },
  "zone-l": { left: "42%", top: "50%", width: "20%", height: "18%" },
};

const SEVERITY_COLORS: Record<string, string> = {
  normal: "rgba(34, 197, 94, 0.35)",
  warning: "rgba(245, 158, 11, 0.45)",
  critical: "rgba(249, 115, 22, 0.55)",
  emergency: "rgba(239, 68, 68, 0.65)",
};

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ── Navigation Items ──
const NAV_ITEMS = [
  { id: "overview", label: "Overview", icon: "📊" },
  { id: "heatmap", label: "Venue Heatmap", icon: "🗺️" },
  { id: "decisions", label: "Decision Copilot", icon: "🤖" },
  { id: "incidents", label: "Incidents", icon: "⚠️" },
  { id: "advisories", label: "Advisories", icon: "📢" },
];

export default function DashboardPage() {
  const [activeView, setActiveView] = useState("overview");
  const [zones, setZones] = useState<ZoneDensity[]>([]);
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [advisories, setAdvisories] = useState<Advisory[]>([]);
  const [isLive, setIsLive] = useState(false);
  const [decisionQuery, setDecisionQuery] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  // ── Fetch crowd data ──
  const fetchCrowdData = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/v1/crowd`);
      if (res.ok) {
        const data = await res.json();
        setZones(data.zones || []);
        setIsLive(true);
      }
    } catch {
      // API not available, use demo data
      setZones(generateDemoZones());
      setIsLive(false);
    }
  }, []);

  // Poll for updates
  useEffect(() => {
    fetchCrowdData();
    const interval = setInterval(fetchCrowdData, 5000);
    return () => clearInterval(interval);
  }, [fetchCrowdData]);

  // ── Generate demo zones for offline mode ──
  function generateDemoZones(): ZoneDensity[] {
    const demoZones: ZoneDensity[] = [
      { zone_id: "zone-a", zone_name: "Zone A — Main Lobby", current_density_pct: 62, ewma_density_pct: 60, trend_direction: "rising", trend_rate_pct_per_min: 1.2, severity: "normal", projected_time_to_threshold_min: 11, current_count: 310, capacity: 500 },
      { zone_id: "zone-b", zone_name: "Zone B — North Concourse", current_density_pct: 45, ewma_density_pct: 43, trend_direction: "stable", trend_rate_pct_per_min: 0.3, severity: "normal", projected_time_to_threshold_min: null, current_count: 180, capacity: 400 },
      { zone_id: "zone-c", zone_name: "Zone C — North Stand", current_density_pct: 82, ewma_density_pct: 79, trend_direction: "rising", trend_rate_pct_per_min: 2.1, severity: "warning", projected_time_to_threshold_min: 6, current_count: 1640, capacity: 2000 },
      { zone_id: "zone-d", zone_name: "Zone D — South Concourse", current_density_pct: 38, ewma_density_pct: 40, trend_direction: "falling", trend_rate_pct_per_min: -0.8, severity: "normal", projected_time_to_threshold_min: null, current_count: 152, capacity: 400 },
      { zone_id: "zone-e", zone_name: "Zone E — South Stand", current_density_pct: 71, ewma_density_pct: 70, trend_direction: "rising", trend_rate_pct_per_min: 0.9, severity: "normal", projected_time_to_threshold_min: null, current_count: 1420, capacity: 2000 },
      { zone_id: "zone-f", zone_name: "Zone F — East Wing", current_density_pct: 55, ewma_density_pct: 53, trend_direction: "stable", trend_rate_pct_per_min: 0.2, severity: "normal", projected_time_to_threshold_min: null, current_count: 330, capacity: 600 },
      { zone_id: "zone-g", zone_name: "Zone G — North Gates", current_density_pct: 88, ewma_density_pct: 85, trend_direction: "rising", trend_rate_pct_per_min: 3.5, severity: "critical", projected_time_to_threshold_min: 2, current_count: 264, capacity: 300 },
      { zone_id: "zone-h", zone_name: "Zone H — South Gates", current_density_pct: 42, ewma_density_pct: 44, trend_direction: "falling", trend_rate_pct_per_min: -1.1, severity: "normal", projected_time_to_threshold_min: null, current_count: 126, capacity: 300 },
      { zone_id: "zone-i", zone_name: "Zone I — VIP Area", current_density_pct: 25, ewma_density_pct: 23, trend_direction: "stable", trend_rate_pct_per_min: 0.1, severity: "normal", projected_time_to_threshold_min: null, current_count: 50, capacity: 200 },
    ];
    return demoZones;
  }

  // ── Request decision support ──
  async function requestDecision() {
    if (!decisionQuery.trim()) return;
    setIsLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/v1/decisions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: decisionQuery }),
      });
      if (res.ok) {
        const data = await res.json();
        setDecisions((prev) => [data, ...prev]);
        setDecisionQuery("");
      }
    } catch {
      // Offline demo
      setDecisions((prev) => [
        {
          decision_id: `demo-${Date.now()}`,
          recommendation:
            "**Recommendation:** Based on current crowd density in Zone C (82%, rising) and Zone G (88%, critical), recommend opening auxiliary Gates G7-G8 immediately. Historical data [SOP: Crowd Management §3.1] suggests this will reduce density by 15-20% within 8 minutes.\n\n**Sources:** [Crowd Agent], [SOP: Crowd Management §3.1], [Historical: Match Day Pattern #12]",
          sources: ["[Crowd Agent]", "[SOP: Crowd Management §3.1]"],
          status: "pending",
          created_at: new Date().toISOString(),
        },
        ...prev,
      ]);
      setDecisionQuery("");
    }
    setIsLoading(false);
  }

  // ── Handle decision action ──
  async function handleDecisionAction(decisionId: string, action: string) {
    try {
      await fetch(`${API_URL}/api/v1/decisions/${decisionId}/action`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action, actor_id: "organizer-1" }),
      });
    } catch {
      // Offline mode
    }
    setDecisions((prev) =>
      prev.map((d) =>
        d.decision_id === decisionId
          ? { ...d, status: action === "approve" ? "approved" : "rejected" }
          : d
      )
    );
  }

  // ── Computed stats ──
  const totalAttendees = zones.reduce((sum, z) => sum + z.current_count, 0);
  const totalCapacity = zones.reduce((sum, z) => sum + z.capacity, 0);
  const avgDensity = zones.length
    ? zones.reduce((sum, z) => sum + z.current_density_pct, 0) / zones.length
    : 0;
  const criticalZones = zones.filter(
    (z) => z.severity === "critical" || z.severity === "emergency"
  );

  return (
    <div className="dashboard-layout">
      {/* ── Sidebar ── */}
      <nav className="sidebar" aria-label="Dashboard navigation">
        <div className="sidebar-logo">
          <div className="sidebar-logo-icon" aria-hidden="true">SA</div>
          <span className="sidebar-logo-text">SentinelArena</span>
        </div>

        <ul className="sidebar-nav" role="navigation">
          {NAV_ITEMS.map((item) => (
            <li key={item.id}>
              <button
                className={`sidebar-nav-item ${activeView === item.id ? "active" : ""}`}
                onClick={() => setActiveView(item.id)}
                aria-current={activeView === item.id ? "page" : undefined}
              >
                <span className="sidebar-nav-icon" aria-hidden="true">
                  {item.icon}
                </span>
                {item.label}
              </button>
            </li>
          ))}
        </ul>

        <div style={{ marginTop: "auto", paddingTop: "var(--space-lg)" }}>
          <div className="live-indicator">
            <span className="live-dot" aria-hidden="true" />
            {isLive ? "Live Data" : "Demo Mode"}
          </div>
        </div>
      </nav>

      {/* ── Main Content ── */}
      <main className="main-content" role="main">
        <div className="page-header">
          <div>
            <h1 className="page-title">Control Room</h1>
            <p className="page-subtitle">
              Real-time venue monitoring and AI decision support
            </p>
          </div>
          <div className="live-indicator">
            <span className="live-dot" aria-hidden="true" />
            {isLive ? "Connected" : "Offline Demo"}
          </div>
        </div>

        {/* ── Stats Row ── */}
        <div className="grid-4" style={{ marginBottom: "var(--space-xl)" }}>
          <div className="card stat-card">
            <span className="stat-label">Total Attendees</span>
            <span className="stat-value">{totalAttendees.toLocaleString()}</span>
            <span className="stat-change neutral">
              of {totalCapacity.toLocaleString()} capacity
            </span>
          </div>
          <div className="card stat-card">
            <span className="stat-label">Average Density</span>
            <span className="stat-value">{avgDensity.toFixed(1)}%</span>
            <span
              className={`stat-change ${avgDensity > 75 ? "negative" : "positive"}`}
            >
              {avgDensity > 75 ? "⬆ Above target" : "✓ Within normal"}
            </span>
          </div>
          <div className="card stat-card">
            <span className="stat-label">Critical Zones</span>
            <span
              className="stat-value"
              style={{ color: criticalZones.length > 0 ? "var(--color-accent-red)" : "var(--color-accent-green)" }}
            >
              {criticalZones.length}
            </span>
            <span className={`stat-change ${criticalZones.length > 0 ? "negative" : "positive"}`}>
              {criticalZones.length > 0
                ? criticalZones.map((z) => z.zone_name.split("—")[0].trim()).join(", ")
                : "All zones normal"}
            </span>
          </div>
          <div className="card stat-card">
            <span className="stat-label">Active Decisions</span>
            <span className="stat-value">
              {decisions.filter((d) => d.status === "pending").length}
            </span>
            <span className="stat-change neutral">Pending approval</span>
          </div>
        </div>

        {/* ── Main Grid: Heatmap + Decision Copilot ── */}
        <div className="grid-dashboard">
          {/* Venue Heatmap */}
          <div className="card" style={{ gridColumn: "1" }}>
            <div className="card-header">
              <h2 className="card-title">Venue Heatmap — Live Density</h2>
              <span
                className={`badge badge-${
                  criticalZones.length > 0
                    ? "critical"
                    : avgDensity > 60
                    ? "warning"
                    : "normal"
                }`}
              >
                {criticalZones.length > 0
                  ? "⚠ Attention Required"
                  : "✓ Normal Operations"}
              </span>
            </div>
            <div
              className="heatmap-container"
              role="img"
              aria-label="Venue density heatmap showing crowd levels per zone"
            >
              {zones.map((zone) => {
                const layout = ZONE_LAYOUT[zone.zone_id];
                if (!layout) return null;
                return (
                  <div
                    key={zone.zone_id}
                    className="heatmap-zone"
                    style={{
                      left: layout.left,
                      top: layout.top,
                      width: layout.width,
                      height: layout.height,
                      background: SEVERITY_COLORS[zone.severity],
                    }}
                    title={`${zone.zone_name}: ${zone.current_density_pct}% (${zone.trend_direction})`}
                    aria-label={`${zone.zone_name}: ${zone.current_density_pct}% capacity, ${zone.severity} severity, trend ${zone.trend_direction}`}
                    tabIndex={0}
                  >
                    <span className="heatmap-zone-name">
                      {zone.zone_name.split("—")[0].trim()}
                    </span>
                    <span className="heatmap-zone-pct">
                      {zone.current_density_pct.toFixed(0)}%
                    </span>
                    {zone.trend_direction === "rising" && (
                      <span style={{ fontSize: "0.7rem", color: "rgba(255,255,255,0.7)" }}>
                        ↑ {zone.trend_rate_pct_per_min.toFixed(1)}%/min
                      </span>
                    )}
                  </div>
                );
              })}
            </div>

            {/* Zone Table (accessible alternative) */}
            <details style={{ marginTop: "var(--space-md)" }}>
              <summary
                style={{ cursor: "pointer", color: "var(--color-text-secondary)", fontSize: "0.85rem" }}
              >
                View as table (accessible)
              </summary>
              <table
                style={{ width: "100%", marginTop: "var(--space-sm)", fontSize: "0.8rem" }}
                aria-label="Zone density data"
              >
                <thead>
                  <tr style={{ color: "var(--color-text-muted)", textAlign: "left" }}>
                    <th scope="col" style={{ padding: "var(--space-xs)" }}>Zone</th>
                    <th scope="col" style={{ padding: "var(--space-xs)" }}>Density</th>
                    <th scope="col" style={{ padding: "var(--space-xs)" }}>Trend</th>
                    <th scope="col" style={{ padding: "var(--space-xs)" }}>Severity</th>
                    <th scope="col" style={{ padding: "var(--space-xs)" }}>Projection</th>
                  </tr>
                </thead>
                <tbody>
                  {zones.map((z) => (
                    <tr key={z.zone_id} style={{ borderTop: "1px solid var(--color-border)" }}>
                      <td style={{ padding: "var(--space-xs)" }}>{z.zone_name}</td>
                      <td style={{ padding: "var(--space-xs)", fontFamily: "var(--font-mono)" }}>
                        {z.current_density_pct.toFixed(1)}%
                      </td>
                      <td style={{ padding: "var(--space-xs)" }}>
                        {z.trend_direction === "rising" ? "↑" : z.trend_direction === "falling" ? "↓" : "→"}{" "}
                        {z.trend_rate_pct_per_min.toFixed(1)}%/min
                      </td>
                      <td style={{ padding: "var(--space-xs)" }}>
                        <span className={`badge badge-${z.severity}`}>{z.severity}</span>
                      </td>
                      <td style={{ padding: "var(--space-xs)" }}>
                        {z.projected_time_to_threshold_min
                          ? `${z.projected_time_to_threshold_min.toFixed(0)} min`
                          : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </details>
          </div>

          {/* Decision Copilot */}
          <div className="card decision-panel">
            <div className="card-header">
              <h2 className="card-title">🤖 Decision Copilot</h2>
            </div>

            {/* Query Input */}
            <div style={{ marginBottom: "var(--space-lg)" }}>
              <label
                htmlFor="decision-query"
                style={{ display: "block", fontSize: "0.8rem", color: "var(--color-text-secondary)", marginBottom: "var(--space-xs)" }}
              >
                Ask the AI Copilot
              </label>
              <div style={{ display: "flex", gap: "var(--space-sm)" }}>
                <input
                  id="decision-query"
                  type="text"
                  value={decisionQuery}
                  onChange={(e) => setDecisionQuery(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && requestDecision()}
                  placeholder="What should we do about Zone C crowd?"
                  style={{
                    flex: 1,
                    padding: "var(--space-sm) var(--space-md)",
                    background: "var(--color-bg-glass)",
                    border: "1px solid var(--color-border)",
                    borderRadius: "var(--radius-md)",
                    color: "var(--color-text-primary)",
                    fontFamily: "var(--font-sans)",
                    fontSize: "0.85rem",
                  }}
                  aria-label="Enter question for the AI Decision Copilot"
                />
                <button
                  className="btn btn-primary"
                  onClick={requestDecision}
                  disabled={isLoading}
                  aria-label="Submit question to Decision Copilot"
                >
                  {isLoading ? "..." : "Ask"}
                </button>
              </div>
            </div>

            {/* Decisions List */}
            <div
              className="advisory-feed"
              role="log"
              aria-label="Decision recommendations"
              aria-live="polite"
            >
              {decisions.length === 0 && (
                <p style={{ color: "var(--color-text-muted)", fontSize: "0.85rem", textAlign: "center", padding: "var(--space-xl) 0" }}>
                  Ask the AI Copilot for recommendations based on live venue data, weather, and SOP procedures.
                </p>
              )}
              {decisions.map((d) => (
                <div key={d.decision_id} className="decision-recommendation">
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--space-sm)" }}>
                    <span
                      className={`badge ${
                        d.status === "approved"
                          ? "badge-normal"
                          : d.status === "rejected"
                          ? "badge-critical"
                          : "badge-warning"
                      }`}
                    >
                      {d.status}
                    </span>
                    <span style={{ fontSize: "0.7rem", color: "var(--color-text-muted)", fontFamily: "var(--font-mono)" }}>
                      {new Date(d.created_at).toLocaleTimeString()}
                    </span>
                  </div>
                  <p style={{ fontSize: "0.85rem", lineHeight: 1.6, whiteSpace: "pre-wrap" }}>
                    {d.recommendation.slice(0, 500)}
                    {d.recommendation.length > 500 ? "..." : ""}
                  </p>
                  {d.sources.length > 0 && (
                    <p style={{ fontSize: "0.7rem", color: "var(--color-accent-cyan)", marginTop: "var(--space-sm)" }}>
                      {d.sources.join(" • ")}
                    </p>
                  )}
                  {d.status === "pending" && (
                    <div className="decision-actions">
                      <button
                        className="btn btn-success"
                        onClick={() => handleDecisionAction(d.decision_id, "approve")}
                        aria-label={`Approve recommendation ${d.decision_id}`}
                      >
                        ✓ Approve
                      </button>
                      <button
                        className="btn btn-danger"
                        onClick={() => handleDecisionAction(d.decision_id, "reject")}
                        aria-label={`Reject recommendation ${d.decision_id}`}
                      >
                        ✕ Reject
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* ── Advisories Feed ── */}
        <div className="card" style={{ marginTop: "var(--space-lg)" }}>
          <div className="card-header">
            <h2 className="card-title">📢 Crowd Advisories</h2>
            <div className="live-indicator">
              <span className="live-dot" aria-hidden="true" />
              Live
            </div>
          </div>
          <div
            className="advisory-feed"
            role="log"
            aria-label="Crowd advisories"
            aria-live="polite"
          >
            {zones
              .filter((z) => z.severity !== "normal" || z.trend_direction === "rising")
              .sort((a, b) => {
                const order = { emergency: 0, critical: 1, warning: 2, normal: 3 };
                return (order[a.severity] ?? 3) - (order[b.severity] ?? 3);
              })
              .map((z) => (
                <div
                  key={z.zone_id}
                  className={`advisory-item ${z.severity}`}
                >
                  <span className="advisory-time">
                    {new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                  </span>
                  <div>
                    <p className="advisory-text">
                      <strong>{z.zone_name}</strong> — Density at{" "}
                      <strong>{z.current_density_pct.toFixed(0)}%</strong>,{" "}
                      {z.trend_direction} at {z.trend_rate_pct_per_min.toFixed(1)}%/min.
                      {z.projected_time_to_threshold_min && (
                        <> Projected to reach next threshold in{" "}
                        <strong>{z.projected_time_to_threshold_min.toFixed(0)} min</strong>.</>
                      )}
                    </p>
                    <span className={`badge badge-${z.severity}`}>
                      {z.severity}
                    </span>
                  </div>
                </div>
              ))}
            {zones.filter((z) => z.severity !== "normal" || z.trend_direction === "rising").length === 0 && (
              <p style={{ color: "var(--color-text-muted)", textAlign: "center", padding: "var(--space-lg) 0" }}>
                ✓ All zones operating within normal parameters
              </p>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
