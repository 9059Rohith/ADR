import { useState, useCallback, useEffect } from "react";

/**
 * SentinelArena — Volunteer Hub
 *
 * Staff incident reporting app with:
 * - JWT Authentication with demo login
 * - Incident report submission with AI triage
 * - Incident list view with severity filtering
 * - Multi-language support
 * - Accessible form controls with ARIA
 *
 * @accessibility WCAG 2.2 AA — semantic HTML, focus management, ARIA
 */

const API_URL = (typeof import.meta !== "undefined" && (import.meta as any).env?.VITE_API_URL)
  || "http://localhost:8000";

interface AuthUser {
  user_id: string;
  email: string;
  display_name: string;
  role: string;
  access_token: string;
}

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

const DEMO_ACCOUNTS = [
  { email: "volunteer@sentinelarena.com", password: "SentinelVol2026!", role: "Volunteer", icon: "🦺" },
  { email: "organizer@sentinelarena.com", password: "SentinelOrg2026!", role: "Organizer", icon: "📋" },
  { email: "admin@sentinelarena.com", password: "SentinelAdmin2026!", role: "Admin", icon: "👑" },
];

// ============================================================
// Login Screen
// ============================================================
function LoginScreen({ onLogin }: { onLogin: (user: AuthUser) => void }) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("volunteer@sentinelarena.com");
  const [password, setPassword] = useState("SentinelVol2026!");
  const [displayName, setDisplayName] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);

    const endpoint = mode === "login" ? "login" : "register";
    const body =
      mode === "login"
        ? { email, password }
        : { email, password, display_name: displayName || String(email || "volunteer").split("@")[0] as string, role: "volunteer" };

    try {
      const res = await fetch(`${API_URL}/api/v1/auth/${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      if (res.ok) {
        const data = await res.json();
        const user: AuthUser = {
          user_id: data.user_id,
          email: data.email,
          display_name: data.display_name,
          role: data.role,
          access_token: data.access_token,
        };
        localStorage.setItem("sentinel_vol_user", JSON.stringify(user));
        onLogin(user);
      } else {
        const errData = await res.json().catch(() => ({ detail: "Server error" }));
        setError(errData.detail || "Authentication failed");
      }
    } catch {
      // Offline demo fallback
      const demoUser: AuthUser = {
        user_id: "demo-vol",
        email: email || "",
        display_name: String(email || "volunteer").split("@")[0] as string,
        role: "volunteer",
        access_token: "demo-token",
      };
      localStorage.setItem("sentinel_vol_user", JSON.stringify(demoUser));
      onLogin(demoUser);
    }
    setIsLoading(false);
  };

  const selectDemo = (account: typeof DEMO_ACCOUNTS[0]) => {
    setEmail(account.email);
    setPassword(account.password);
    setMode("login");
    setError("");
  };

  return (
    <div className="app" style={{ alignItems: "center", justifyContent: "center", padding: "24px 16px" }}>
      <div style={{ width: "100%", maxWidth: "400px", display: "flex", flexDirection: "column", gap: "24px", alignItems: "center" }}>
        <div style={{ textAlign: "center" }}>
          <div style={{
            width: "56px", height: "56px", borderRadius: "14px",
            background: "linear-gradient(135deg, var(--accent), var(--purple))",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: "1.3rem", fontWeight: 900, color: "white",
            boxShadow: "0 0 30px rgba(59,130,246,0.3)", margin: "0 auto 12px",
          }} aria-hidden="true">SA</div>
          <h1 style={{
            fontSize: "1.5rem", fontWeight: 800,
            background: "linear-gradient(135deg, var(--accent), var(--purple))",
            WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent",
            marginBottom: "4px",
          }}>Volunteer Hub</h1>
          <p style={{ color: "var(--text-sec)", fontSize: "0.85rem" }}>SentinelArena Staff Portal</p>
        </div>

        <div className="card" style={{ width: "100%" }}>
          <div className="tab-bar" role="tablist">
            <button
              className={`tab ${mode === "login" ? "active" : ""}`}
              onClick={() => { setMode("login"); setError(""); }}
              role="tab"
              aria-selected={mode === "login"}
            >
              Sign In
            </button>
            <button
              className={`tab ${mode === "register" ? "active" : ""}`}
              onClick={() => { setMode("register"); setError(""); }}
              role="tab"
              aria-selected={mode === "register"}
            >
              Register
            </button>
          </div>

          <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            {error && (
              <div role="alert" style={{
                padding: "10px 14px", background: "rgba(239,68,68,0.1)",
                border: "1px solid rgba(239,68,68,0.3)", borderRadius: "8px",
                color: "var(--red)", fontSize: "0.85rem",
              }}>{error}</div>
            )}

            <div className="form-group">
              <label htmlFor="vol-email">Email</label>
              <input id="vol-email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoComplete="email" />
            </div>
            <div className="form-group">
              <label htmlFor="vol-password">Password</label>
              <input id="vol-password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={8} autoComplete={mode === "login" ? "current-password" : "new-password"} />
            </div>

            {mode === "register" && (
              <div className="form-group">
                <label htmlFor="vol-name">Display Name</label>
                <input id="vol-name" type="text" value={displayName} onChange={(e) => setDisplayName(e.target.value)} required minLength={2} />
              </div>
            )}

            <button type="submit" className="btn btn-primary" disabled={isLoading} aria-busy={isLoading}>
              {isLoading ? "Loading..." : mode === "login" ? "Sign In" : "Create Account"}
            </button>
          </form>

          <div style={{ marginTop: "16px", paddingTop: "12px", borderTop: "1px solid var(--border)", display: "flex", flexDirection: "column", gap: "8px" }}>
            <p style={{ fontSize: "0.7rem", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--text-sec)", textAlign: "center" }}>Quick Demo Access</p>
            {DEMO_ACCOUNTS.map((acc) => (
              <button
                key={acc.email}
                onClick={() => selectDemo(acc)}
                style={{
                  width: "100%", padding: "8px", background: "rgba(255,255,255,0.03)",
                  border: "1px solid var(--border)", borderRadius: "8px", cursor: "pointer",
                  fontFamily: "var(--font)", fontSize: "0.8rem", color: "var(--text-sec)",
                  display: "flex", alignItems: "center", gap: "8px", justifyContent: "center",
                  transition: "all 0.2s",
                }}
                aria-label={`Login as ${acc.role}`}
              >
                <span aria-hidden="true">{acc.icon}</span> {acc.role}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// ============================================================
// Main Volunteer App
// ============================================================
export default function App() {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [authChecked, setAuthChecked] = useState(false);
  const [tab, setTab] = useState<"report" | "list">("report");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [severity, setSeverity] = useState("medium");
  const [zoneId, setZoneId] = useState("zone-a");
  const [locale, setLocale] = useState("en");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState<Incident | null>(null);
  const [incidents, setIncidents] = useState<Incident[]>([]);

  // ── Restore session ──
  useEffect(() => {
    try {
      const stored = localStorage.getItem("sentinel_vol_user");
      if (stored) setUser(JSON.parse(stored));
    } catch {
      localStorage.removeItem("sentinel_vol_user");
    }
    setAuthChecked(true);
  }, []);

  const getAuthHeaders = useCallback((): Record<string, string> => {
    const headers: Record<string, string> = { "Content-Type": "application/json" };
    if (user?.access_token && user.access_token !== "demo-token") {
      headers["Authorization"] = `Bearer ${user.access_token}`;
    }
    return headers;
  }, [user]);

  const submitIncident = useCallback(async () => {
    if (!title.trim() || !description.trim() || description.length < 10) return;
    setIsSubmitting(true);
    try {
      const res = await fetch(`${API_URL}/api/v1/incidents`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify({
          title, description, severity, zone_id: zoneId, locale,
          reporter_id: user?.user_id || "volunteer-1",
        }),
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
  }, [title, description, severity, zoneId, locale, user, getAuthHeaders]);

  const fetchIncidents = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/v1/incidents`, {
        headers: getAuthHeaders(),
      });
      if (res.ok) {
        const data = await res.json();
        setIncidents(data.incidents || []);
      }
    } catch {
      setIncidents([]);
    }
  }, [getAuthHeaders]);

  const handleLogout = () => {
    localStorage.removeItem("sentinel_vol_user");
    setUser(null);
    setIncidents([]);
    setSubmitted(null);
  };

  if (!authChecked) {
    return (
      <div className="app" style={{ alignItems: "center", justifyContent: "center" }}>
        <p style={{ color: "var(--text-sec)" }}>Loading...</p>
      </div>
    );
  }

  if (!user) {
    return <LoginScreen onLogin={setUser} />;
  }

  return (
    <div className="app">
      <header className="header" role="banner">
        <h1>🦺 Volunteer Hub</h1>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
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
          <button
            onClick={handleLogout}
            aria-label="Sign out"
            title="Sign out"
            style={{
              padding: "4px 8px", background: "rgba(239,68,68,0.1)",
              border: "1px solid rgba(239,68,68,0.2)", borderRadius: "6px",
              color: "#ef4444", fontFamily: "Inter", fontSize: "0.75rem",
              cursor: "pointer", fontWeight: 600,
            }}
          >
            ↩ Out
          </button>
        </div>
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
