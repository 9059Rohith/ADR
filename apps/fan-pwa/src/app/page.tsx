"use client";

import { useState, useRef, useEffect, useCallback } from "react";

/**
 * SentinelArena — Fan PWA
 *
 * Mobile-first conversational AI assistant for venue fans:
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

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: string[];
  routeData?: Record<string, unknown>;
  timestamp: Date;
}

export default function FanPWA() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "assistant",
      content:
        "👋 Welcome to SentinelArena! I'm your AI venue assistant.\n\nI can help you with:\n• 🗺️ **Navigation** — Find your way around\n• 👥 **Crowd info** — Check density & wait times\n• 🌐 **Multiple languages** — Select your language above\n• 🎤 **Voice input** — Tap the mic to speak\n\nHow can I help you today?",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState("");
  const [locale, setLocale] = useState("en");
  const [isLoading, setIsLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

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
        const res = await fetch(`${API_URL}/api/v1/chat`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
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
            // Only speak if user has interacted with voice
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
    [isLoading, locale, isListening]
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

  return (
    <div className="app-shell">
      {/* ── Header ── */}
      <header className="app-header" role="banner">
        <div className="app-logo">
          <div className="app-logo-icon" aria-hidden="true">SA</div>
          <span className="app-logo-text">SentinelArena</span>
        </div>
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
