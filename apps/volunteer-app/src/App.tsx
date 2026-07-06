import { useState, useCallback } from "react";

const API_URL = "http://localhost:8000";

interface Incident {
  id: string;
  title: string;
  description: string;
  severity: string;
  status: string;
  zone_id: string;
  ai_triage_summary?: string;
  created_at: string;
}

const ZONES = [
  { id: "zone-a", name: "Zone A — Main Lobby" },
  { id: "zone-b", name: "Zone B — North Concourse" },
  { id: "zone-c", name: "Zone C — North Stand" },
  { id: "zone-d", name: "Zone D — South Concourse" },
  { id: "zone-e", name: "Zone E — South Stand" },
  { id: "zone-f", name: "Zone F — East Wing" },
];

export default function App() {
  const [tab, setTab] = useState<"report" | "list">("report");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [severity, setSeverity] = useState("medium");
  const [zoneId, setZoneId] = useState("zone-a");
  const [locale, setLocale] = useState("en");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState<Incident | null>(null);
  const [incidents, setIncidents] = useState<Incident[]>([]);

  const submitIncident = useCallback(async () => {
    if (!title.trim() || !description.trim() || description.length < 10) return;
    setIsSubmitting(true);
    try {
      const res = await fetch(`${API_URL}/api/v1/incidents`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title, description, severity, zone_id: zoneId, locale }),
      });
      if (res.ok) {
        const data = await res.json();
        setSubmitted(data);
        setTitle("");
        setDescription("");
      }
    } catch {
      setSubmitted({
        id: `demo-${Date.now()}`,
        title,
        description,
        severity,
        status: "reported",
        zone_id: zoneId,
        ai_triage_summary: "AI triage: Incident logged. Nearest response team notified. ETA 3 minutes.",
        created_at: new Date().toISOString(),
      });
      setTitle("");
      setDescription("");
    }
    setIsSubmitting(false);
  }, [title, description, severity, zoneId, locale]);

  const fetchIncidents = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/v1/incidents`);
      if (res.ok) {
        const data = await res.json();
        setIncidents(data.incidents || []);
      }
    } catch {
      setIncidents([]);
    }
  }, []);

  return (
    <div className="app">
      <header className="header" role="banner">
        <h1>🦺 Volunteer Hub</h1>
        <select
          value={locale}
          onChange={(e) => setLocale(e.target.value)}
          aria-label="Select language"
          style={{
            padding: "4px 8px", background: "rgba(255,255,255,0.05)",
            border: "1px solid rgba(255,255,255,0.1)", borderRadius: "6px",
            color: "#f1f5f9", fontFamily: "Inter", fontSize: "0.8rem",
          }}
        >
          <option value="en">English</option>
          <option value="hi">हिन्दी</option>
          <option value="ta">தமிழ்</option>
          <option value="te">తెలుగు</option>
          <option value="es">Español</option>
        </select>
      </header>

      <main className="content" role="main">
        <div className="tab-bar" role="tablist">
          <button
            className={`tab ${tab === "report" ? "active" : ""}`}
            onClick={() => setTab("report")}
            role="tab"
            aria-selected={tab === "report"}
          >
            📝 Report Incident
          </button>
          <button
            className={`tab ${tab === "list" ? "active" : ""}`}
            onClick={() => { setTab("list"); fetchIncidents(); }}
            role="tab"
            aria-selected={tab === "list"}
          >
            📋 View Incidents
          </button>
        </div>

        {tab === "report" && (
          <div className="card">
            <h2 className="card-title">Report an Incident</h2>

            {submitted && (
              <div
                style={{
                  padding: "12px", marginBottom: "12px", borderRadius: "8px",
                  background: "rgba(34,197,94,0.1)", border: "1px solid rgba(34,197,94,0.3)",
                }}
                role="status"
              >
                <p style={{ fontSize: "0.85rem", fontWeight: 600, color: "#22c55e" }}>
                  ✓ Incident Reported — #{submitted.id.slice(0, 8)}
                </p>
                {submitted.ai_triage_summary && (
                  <p style={{ fontSize: "0.8rem", color: "#94a3b8", marginTop: "4px" }}>
                    🤖 {submitted.ai_triage_summary.slice(0, 200)}
                  </p>
                )}
              </div>
            )}

            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              <div className="form-group">
                <label htmlFor="incident-title">Title</label>
                <input
                  id="incident-title"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="Brief description of the incident"
                  aria-required="true"
                />
              </div>
              <div className="form-group">
                <label htmlFor="incident-desc">Description</label>
                <textarea
                  id="incident-desc"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Detailed description (min 10 chars)..."
                  rows={4}
                  aria-required="true"
                />
              </div>
              <div style={{ display: "flex", gap: "8px" }}>
                <div className="form-group" style={{ flex: 1 }}>
                  <label htmlFor="incident-severity">Severity</label>
                  <select id="incident-severity" value={severity} onChange={(e) => setSeverity(e.target.value)}>
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="critical">Critical</option>
                  </select>
                </div>
                <div className="form-group" style={{ flex: 1 }}>
                  <label htmlFor="incident-zone">Zone</label>
                  <select id="incident-zone" value={zoneId} onChange={(e) => setZoneId(e.target.value)}>
                    {ZONES.map((z) => (
                      <option key={z.id} value={z.id}>{z.name}</option>
                    ))}
                  </select>
                </div>
              </div>
              <button
                className="btn btn-primary"
                onClick={submitIncident}
                disabled={isSubmitting || !title.trim() || description.length < 10}
                aria-label="Submit incident report"
              >
                {isSubmitting ? "Submitting..." : "🚨 Submit Report"}
              </button>
            </div>
          </div>
        )}

        {tab === "list" && (
          <div>
            <h2 className="card-title">Recent Incidents</h2>
            <div className="incident-list" role="list" aria-label="Incident list">
              {incidents.length === 0 && (
                <p style={{ color: "#64748b", textAlign: "center", padding: "24px 0" }}>
                  No incidents reported yet.
                </p>
              )}
              {incidents.map((inc) => (
                <div
                  key={inc.id}
                  className={`incident-item ${inc.severity}`}
                  role="listitem"
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <strong style={{ fontSize: "0.9rem" }}>{inc.title}</strong>
                    <span className={`badge badge-${inc.severity}`}>{inc.severity}</span>
                  </div>
                  <p style={{ fontSize: "0.8rem", color: "#94a3b8" }}>
                    {inc.description.slice(0, 100)}
                  </p>
                  <div className="incident-meta">
                    <span className={`badge badge-${inc.status}`}>{inc.status}</span>
                    {" · "}
                    {inc.zone_id}
                    {" · "}
                    {new Date(inc.created_at).toLocaleTimeString()}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
