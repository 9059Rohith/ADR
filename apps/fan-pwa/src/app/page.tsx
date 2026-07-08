"use client";

import { useState, useRef, useEffect, useCallback } from "react";

/**
 * SentinelArena — Fan PWA
 *
 * Mobile-first conversational AI assistant for venue fans:
 * - JWT Authentication with demo login (pre-filled credentials)
 * - Natural language chat with streaming responses
 * - Indoor navigation with route visualization
 * - Voice input/output (Web Speech API, progressive enhancement)
 * - Multi-language support (EN, HI, TA, TE, ES)
 * - Crowd density information
 * - Accessible: keyboard nav, ARIA live regions, screen reader support
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const LOCALE_LABELS: Record<string, string> = {
  en: "English",
  hi: "हिन्दी",
  ta: "தமிழ்",
  te: "తెలుగు",
  es: "Español",
};

const QUICK_ACTIONS = [
  { label: "🚻 Nearest restroom", query: "Where is the nearest restroom?" },
  { label: "🍔 Food court", query: "How do I get to the food court?" },
  { label: "🚪 Gate 3", query: "Navigate to Gate 3 avoiding stairs" },
  { label: "👥 Crowd info", query: "How busy is the venue right now?" },
  { label: "🏥 Medical", query: "Where is the nearest medical station?" },
  { label: "♿ Accessible route", query: "Find me an accessible route to the seating area" },
];

const DEMO_ACCOUNTS = [
  { email: "fan@sentinelarena.com", password: "SentinelFan2026!", role: "Fan", icon: "🎉" },
  { email: "volunteer@sentinelarena.com", password: "SentinelVol2026!", role: "Volunteer", icon: "🦺" },
  { email: "admin@sentinelarena.com", password: "SentinelAdmin2026!", role: "Admin", icon: "👑" },
];

interface AuthUser {
  user_id: string;
  email: string;
  display_name: string;
  role: string;
  access_token: string;
}

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: string[];
  routeData?: Record<string, unknown>;
  timestamp: Date;
}

// ============================================================
// Login Screen
// ============================================================
function LoginScreen({ onLogin }: { onLogin: (user: AuthUser) => void }) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("fan@sentinelarena.com");
  const [password, setPassword] = useState("SentinelFan2026!");
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
        : { email, password, display_name: displayName || email.split("@")[0], role: "fan" };

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
        localStorage.setItem("sentinel_fan_user", JSON.stringify(user));
        onLogin(user);
      } else {
        const errData = await res.json().catch(() => ({ detail: "Server error" }));
        setError(errData.detail || "Authentication failed");
      }
    } catch {
      // Offline demo fallback
      const demoUser: AuthUser = {
        user_id: "demo-fan",
        email: email || "",
        display_name: (email || "demo").split("@")[0],
        role: "fan",
        access_token: "demo-token",
      };
      localStorage.setItem("sentinel_fan_user", JSON.stringify(demoUser));
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
    <div className="login-screen" role="main">
      <div className="login-container">
        <div className="login-brand">
          <div className="login-logo" aria-hidden="true">SA</div>
          <h1 className="login-title">SentinelArena</h1>
          <p className="login-subtitle">AI Venue Assistant</p>
        </div>

        <div className="login-card">
          <div className="login-tabs" role="tablist">
            <button
              className={`login-tab ${mode === "login" ? "active" : ""}`}
              onClick={() => { setMode("login"); setError(""); }}
              role="tab"
              aria-selected={mode === "login"}
            >
              Sign In
            </button>
            <button
              className={`login-tab ${mode === "register" ? "active" : ""}`}
              onClick={() => { setMode("register"); setError(""); }}
              role="tab"
              aria-selected={mode === "register"}
            >
              Register
            </button>
          </div>

          <form onSubmit={handleSubmit} aria-label="Login form">
            {error && (
              <div className="login-error" role="alert">{error}</div>
            )}

            <div className="login-field">
              <label htmlFor="fan-email">Email</label>
              <input
                id="fan-email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="email"
              />
            </div>

            <div className="login-field">
              <label htmlFor="fan-password">Password</label>
              <input
                id="fan-password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={8}
                autoComplete={mode === "login" ? "current-password" : "new-password"}
              />
            </div>

            {mode === "register" && (
              <div className="login-field">
                <label htmlFor="fan-name">Display Name</label>
                <input
                  id="fan-name"
                  type="text"
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  required
                  minLength={2}
                />
              </div>
            )}

            <button
              type="submit"
              className="login-submit"
              disabled={isLoading}
              aria-busy={isLoading}
            >
              {isLoading ? "Loading..." : mode === "login" ? "Sign In" : "Create Account"}
            </button>
          </form>

          <div className="login-demos">
            <p className="login-demos-label">Quick Demo Access</p>
            {DEMO_ACCOUNTS.map((acc) => (
              <button
                key={acc.email}
                className="login-demo-btn"
                onClick={() => selectDemo(acc)}
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
// Main Fan PWA Component
// ============================================================
export default function FanPWA() {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [authChecked, setAuthChecked] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [locale, setLocale] = useState("en");
  const [isLoading, setIsLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // ── Restore session ──
  useEffect(() => {
    try {
      const stored = localStorage.getItem("sentinel_fan_user");
      if (stored) setUser(JSON.parse(stored));
    } catch {
      localStorage.removeItem("sentinel_fan_user");
    }
    setAuthChecked(true);
  }, []);

  // ── Initialize welcome message ──
  useEffect(() => {
    if (user && messages.length === 0) {
      setMessages([
        {
          id: "welcome",
          role: "assistant",
          content:
            `👋 Welcome, ${user.display_name}! I'm your AI venue assistant.\n\nI can help you with:\n• 🗺️ **Navigation** — Find your way around\n• 👥 **Crowd info** — Check density & wait times\n• 🌐 **Multiple languages** — Select your language above\n• 🎤 **Voice input** — Tap the mic to speak\n\nHow can I help you today?`,
          timestamp: new Date(),
        },
      ]);
    }
  }, [user, messages.length]);

  // Auto-scroll to bottom
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // ── Send message ──
  const sendMessage = useCallback(
    async (text: string) => {
      if (!text.trim() || isLoading) return;

      const userMsg: Message = {
        id: `user-${Date.now()}`,
        role: "user",
        content: text,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, userMsg]);
      setInput("");
      setIsLoading(true);

      try {
        const headers: Record<string, string> = { "Content-Type": "application/json" };
        if (user?.access_token && user.access_token !== "demo-token") {
          headers["Authorization"] = `Bearer ${user.access_token}`;
        }
        const res = await fetch(`${API_URL}/api/v1/chat`, {
          method: "POST",
          headers,
          body: JSON.stringify({
            message: text,
            locale,
            user_location_id: "lobby-main",
          }),
        });

        if (res.ok) {
          const data = await res.json();
          const assistantMsg: Message = {
            id: `assistant-${Date.now()}`,
            role: "assistant",
            content: data.response,
            sources: data.sources,
            routeData: data.route_data,
            timestamp: new Date(),
          };
          setMessages((prev) => [...prev, assistantMsg]);

          // TTS output (progressive enhancement)
          if ("speechSynthesis" in window && locale === "en") {
            const utterance = new SpeechSynthesisUtterance(
              data.response.replace(/[*#_\[\]]/g, "").slice(0, 200)
            );
            utterance.rate = 0.9;
            utterance.lang = locale;
            if (isListening) {
              speechSynthesis.speak(utterance);
            }
          }
        } else {
          throw new Error("API error");
        }
      } catch {
        // Offline fallback
        const fallbackMsg: Message = {
          id: `assistant-${Date.now()}`,
          role: "assistant",
          content:
            "I'm currently running in offline mode. Here's what I can tell you:\n\n" +
            "🗺️ The **Main Lobby** is straight ahead from Gate 1.\n" +
            "🚻 **Restrooms** are in the North and South Concourses.\n" +
            "🍔 **Food Court** is on the Ground Floor (Zone A) and Level 1.\n\n" +
            "Connect to the venue Wi-Fi for real-time AI assistance!",
          sources: ["[Offline Cache]"],
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, fallbackMsg]);
      }
      setIsLoading(false);
    },
    [isLoading, locale, isListening, user]
  );

  // ── Voice Input (Web Speech API — Progressive Enhancement) ──
  const startVoiceInput = useCallback(() => {
    if (!("webkitSpeechRecognition" in window) && !("SpeechRecognition" in window)) {
      alert("Voice input is only supported in Chrome and Edge browsers.");
      return;
    }

    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.lang = locale === "en" ? "en-US" : locale === "hi" ? "hi-IN" : locale === "ta" ? "ta-IN" : locale === "te" ? "te-IN" : "es-ES";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onstart = () => setIsListening(true);
    recognition.onend = () => setIsListening(false);
    recognition.onresult = (event: any) => {
      const transcript = event.results[0][0].transcript;
      setInput(transcript);
      sendMessage(transcript);
    };
    recognition.onerror = () => setIsListening(false);

    recognition.start();
  }, [locale, sendMessage]);

  // ── Logout ──
  const handleLogout = () => {
    localStorage.removeItem("sentinel_fan_user");
    setUser(null);
    setMessages([]);
  };

  if (!authChecked) {
    return (
      <div className="login-screen" role="status">
        <div className="login-container">
          <div className="login-brand">
            <div className="login-logo" aria-hidden="true">SA</div>
            <p className="login-subtitle">Loading...</p>
          </div>
        </div>
      </div>
    );
  }

  if (!user) {
    return <LoginScreen onLogin={setUser} />;
  }

  return (
    <div className="app-shell">
      {/* ── Header ── */}
      <header className="app-header" role="banner">
        <div className="app-logo">
          <div className="app-logo-icon" aria-hidden="true">SA</div>
          <span className="app-logo-text">SentinelArena</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <select
            className="lang-select"
            value={locale}
            onChange={(e) => setLocale(e.target.value)}
            aria-label="Select language"
          >
            {Object.entries(LOCALE_LABELS).map(([code, label]) => (
              <option key={code} value={code}>
                {label}
              </option>
            ))}
          </select>
          <button
            className="btn-icon btn-logout"
            onClick={handleLogout}
            aria-label="Sign out"
            title="Sign out"
            style={{
              width: "32px", height: "32px", fontSize: "0.8rem",
              background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.2)",
              borderRadius: "8px", cursor: "pointer", color: "#ef4444",
            }}
          >
            ↩
          </button>
        </div>
      </header>

      {/* ── Chat Area ── */}
      <main
        className="chat-area"
        role="log"
        aria-label="Chat messages"
        aria-live="polite"
      >
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`chat-message ${msg.role}`}
            role={msg.role === "assistant" ? "status" : undefined}
          >
            <div style={{ whiteSpace: "pre-wrap" }}>{msg.content}</div>
            {msg.sources && msg.sources.length > 0 && (
              <div className="chat-sources">{msg.sources.join(" • ")}</div>
            )}
            {msg.routeData && (
              <div className="route-map">
                <div className="route-info">
                  <span>
                    📏 <strong>{(msg.routeData as any).total_distance_display || "—"}</strong>
                  </span>
                  <span>
                    ⏱️ <strong>{(msg.routeData as any).estimated_time_display || "—"}</strong>
                  </span>
                  <span>
                    ♿ {(msg.routeData as any).is_accessible ? "✓ Accessible" : "⚠ Has stairs"}
                  </span>
                </div>
                <svg
                  viewBox="0 0 1000 600"
                  style={{ width: "100%", height: "auto" }}
                  role="img"
                  aria-label="Route map showing your path through the venue"
                >
                  {/* Background */}
                  <rect width="1000" height="600" fill="#111827" rx="8" />
                  <text x="500" y="30" textAnchor="middle" fill="#64748b" fontSize="14">
                    Indoor Venue Map
                  </text>
                  {/* Route nodes */}
                  {((msg.routeData as any).nodes || []).map(
                    (node: any, i: number) => (
                      <g key={node.id}>
                        <circle
                          cx={node.x}
                          cy={node.y}
                          r={i === 0 ? 10 : i === ((msg.routeData as any).nodes?.length || 0) - 1 ? 10 : 6}
                          fill={i === 0 ? "#22c55e" : i === ((msg.routeData as any).nodes?.length || 0) - 1 ? "#3b82f6" : "#8b5cf6"}
                          stroke="white"
                          strokeWidth="2"
                        />
                        <text
                          x={node.x}
                          y={node.y - 14}
                          textAnchor="middle"
                          fill="#94a3b8"
                          fontSize="10"
                        >
                          {node.name.length > 15 ? node.name.slice(0, 15) + "…" : node.name}
                        </text>
                      </g>
                    )
                  )}
                  {/* Route lines */}
                  {((msg.routeData as any).nodes || []).slice(0, -1).map(
                    (node: any, i: number) => {
                      const next = ((msg.routeData as any).nodes || [])[i + 1];
                      if (!next) return null;
                      return (
                        <line
                          key={`line-${i}`}
                          x1={node.x}
                          y1={node.y}
                          x2={next.x}
                          y2={next.y}
                          stroke="#3b82f6"
                          strokeWidth="3"
                          strokeDasharray="8,4"
                          opacity="0.8"
                        />
                      );
                    }
                  )}
                </svg>
              </div>
            )}
          </div>
        ))}
        {isLoading && (
          <div className="chat-message assistant" role="status" aria-label="Loading response">
            <div style={{ display: "flex", gap: "4px" }}>
              <span style={{ animation: "pulse 1s infinite", animationDelay: "0ms" }}>●</span>
              <span style={{ animation: "pulse 1s infinite", animationDelay: "200ms" }}>●</span>
              <span style={{ animation: "pulse 1s infinite", animationDelay: "400ms" }}>●</span>
            </div>
          </div>
        )}
        <div ref={chatEndRef} />
      </main>

      {/* ── Input Area ── */}
      <footer className="input-area" role="contentinfo">
        {/* Quick Actions */}
        <div className="quick-actions" role="toolbar" aria-label="Quick action suggestions">
          {QUICK_ACTIONS.map((action) => (
            <button
              key={action.query}
              className="quick-btn"
              onClick={() => sendMessage(action.query)}
              disabled={isLoading}
              aria-label={action.label}
            >
              {action.label}
            </button>
          ))}
        </div>

        {/* Input Row */}
        <div className="input-row">
          <button
            className={`btn-icon btn-voice ${isListening ? "listening" : ""}`}
            onClick={startVoiceInput}
            aria-label={isListening ? "Listening... tap to stop" : "Start voice input"}
            title="Voice input (Chrome/Edge)"
          >
            🎤
          </button>
          <input
            className="chat-input"
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && sendMessage(input)}
            placeholder={
              locale === "hi" ? "अपना सवाल पूछें..." :
              locale === "es" ? "Escribe tu pregunta..." :
              "Ask me anything..."
            }
            disabled={isLoading}
            aria-label="Type your message"
          />
          <button
            className="btn-icon btn-send"
            onClick={() => sendMessage(input)}
            disabled={isLoading || !input.trim()}
            aria-label="Send message"
          >
            ➤
          </button>
        </div>
      </footer>
    </div>
  );
}
