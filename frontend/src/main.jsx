import { useState, useRef, useEffect } from "react";
import "./styles.css";

const API = "";

function VaderFace({ size = 120 }) {
  return (
    <svg viewBox="0 0 120 120" width={size} height={size}>
      <defs>
        <radialGradient id="helmet" cx="50%" cy="35%" r="60%">
          <stop offset="0%" stopColor="#2a2a3e"/>
          <stop offset="100%" stopColor="#111120"/>
        </radialGradient>
        <radialGradient id="eyeGlow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#7B68EE" stopOpacity="0.8"/>
          <stop offset="100%" stopColor="#7B68EE" stopOpacity="0"/>
        </radialGradient>
        <linearGradient id="mouthGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#181828"/>
          <stop offset="100%" stopColor="#0a0a15"/>
        </linearGradient>
      </defs>
      <path d="M60 8 C28 8 12 28 12 52 C12 68 18 82 30 92 Q44 104 60 106 Q76 104 90 92 C102 82 108 68 108 52 C108 28 92 8 60 8Z" fill="url(#helmet)" stroke="#333348" strokeWidth="0.8"/>
      <path d="M60 8 C60 8 60 10 60 42" stroke="#333348" strokeWidth="1.2" opacity="0.6"/>
      <path d="M18 48 Q60 32 102 48" fill="none" stroke="#333348" strokeWidth="1.5"/>
      <path d="M16 52 Q14 68 22 85" fill="none" stroke="#333348" strokeWidth="1" opacity="0.5"/>
      <path d="M104 52 Q106 68 98 85" fill="none" stroke="#333348" strokeWidth="1" opacity="0.5"/>
      <path d="M22 50 L22 72 L30 78" fill="none" stroke="#333348" strokeWidth="0.7" opacity="0.4"/>
      <path d="M98 50 L98 72 L90 78" fill="none" stroke="#333348" strokeWidth="0.7" opacity="0.4"/>
      <ellipse cx="46" cy="22" rx="18" ry="8" fill="white" opacity="0.06"/>
      <path d="M26 52 L42 46 L60 50 L78 46 L94 52" fill="none" stroke="#3d3d55" strokeWidth="1.8" strokeLinejoin="round"/>
      <path d="M30 56 L44 50 L50 58 L48 64 L32 64Z" fill="#0a0a15" stroke="#333348" strokeWidth="0.8" strokeLinejoin="round"/>
      <path d="M90 56 L76 50 L70 58 L72 64 L88 64Z" fill="#0a0a15" stroke="#333348" strokeWidth="0.8" strokeLinejoin="round"/>
      <circle cx="40" cy="57" r="8" fill="url(#eyeGlow)" className="eye-glow"/>
      <circle cx="80" cy="57" r="8" fill="url(#eyeGlow)" className="eye-glow"/>
      <ellipse cx="40" cy="57" rx="4" ry="3" fill="#7B68EE" opacity="0.5"/>
      <ellipse cx="80" cy="57" rx="4" ry="3" fill="#7B68EE" opacity="0.5"/>
      <circle cx="36" cy="54" r="2.5" fill="white" opacity="0.3"/>
      <circle cx="76" cy="54" r="2.5" fill="white" opacity="0.3"/>
      <circle cx="43" cy="59" r="1.2" fill="white" opacity="0.15"/>
      <circle cx="83" cy="59" r="1.2" fill="white" opacity="0.15"/>
      <path d="M56 66 L60 74 L64 66Z" fill="#0a0a15" stroke="#333348" strokeWidth="0.7"/>
      <line x1="60" y1="66" x2="60" y2="73" stroke="#333348" strokeWidth="0.4" opacity="0.5"/>
      <path d="M34 78 Q38 74 60 74 Q82 74 86 78 L88 88 Q86 98 60 100 Q34 98 32 88Z" fill="url(#mouthGrad)" stroke="#333348" strokeWidth="0.8"/>
      <line x1="40" y1="80" x2="80" y2="80" stroke="#333348" strokeWidth="0.7"/>
      <line x1="38" y1="85" x2="82" y2="85" stroke="#333348" strokeWidth="0.7"/>
      <line x1="39" y1="90" x2="81" y2="90" stroke="#333348" strokeWidth="0.7"/>
      <line x1="42" y1="95" x2="78" y2="95" stroke="#333348" strokeWidth="0.6" opacity="0.5"/>
      <circle cx="36" cy="82" r="1.5" fill="#333348" opacity="0.4"/>
      <circle cx="84" cy="82" r="1.5" fill="#333348" opacity="0.4"/>
      <ellipse cx="60" cy="102" rx="12" ry="3" fill="white" opacity="0.03"/>
    </svg>
  );
}

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState(null);
  const chatEnd = useRef(null);

  useEffect(() => {
    fetch(API + "/api/status").then(r => r.json()).then(setStatus).catch(() => {});
  }, []);

  useEffect(() => {
    chatEnd.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = async () => {
    const text = input.trim();
    if (!text || loading) return;
    setInput("");
    setMessages(prev => [...prev, { role: "user", text }]);
    setLoading(true);
    try {
      const res = await fetch(API + "/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });
      const data = await res.json();
      setMessages(prev => [...prev, { role: "assistant", text: data.response }]);
      if (data.status) setStatus(data.status);
    } catch (e) {
      setMessages(prev => [...prev, { role: "assistant", text: "Error de conexion con el servidor." }]);
    }
    setLoading(false);
  };

  const hasMessages = messages.length > 0 || loading;

  return (
    <div className="app">
      <header className="header">
        <div className="logo">
          <div className="logo-vader">
            <VaderFace size={34} />
          </div>
          <div>
            <div className="header-title">ILLO</div>
            <span className="subtitle">
              {status ? status.name + " v" + (status.version || "2.0") + " | " + (status.skills_registered || 0) + " skills" : "Conectando..."}
            </span>
          </div>
        </div>
        <div className={"status-badge" + (status ? "" : " offline")}>
          {status ? "EN LINEA" : "OFFLINE"}
        </div>
      </header>

      <div className="main">
        <section className="chat-section">
          <div className="chat-messages">
            {!hasMessages && (
              <div className="empty-chat">
                <div className="empty-vader">
                  <VaderFace size={110} />
                </div>
                <div className="empty-text">
                  <p>Hola, soy <strong>ILLO</strong></p>
                  <p className="empty-hint">Tu asistente personal. Preguntame lo que necesites.</p>
                </div>
              </div>
            )}
            {hasMessages && (
              <div className="top-vader">
                <div className="top-vader-circle">
                  <VaderFace size={50} />
                </div>
                <span className="top-vader-name">ILLO</span>
              </div>
            )}
            {messages.map((m, i) => (
              <div key={i} className={"msg " + m.role}>
                <div className="msg-label">
                  {m.role === "assistant" && (
                    <span className="msg-avatar"><VaderFace size={12} /></span>
                  )}
                  {m.role === "user" ? "TU" : "ILLO"}
                </div>
                <div className="msg-bubble">{m.text}</div>
              </div>
            ))}
            {loading && (
              <div className="msg assistant">
                <div className="msg-label">
                  <span className="msg-avatar"><VaderFace size={12} /></span>
                  ILLO
                </div>
                <div className="msg-bubble typing">Pensando<span className="dots">...</span></div>
              </div>
            )}
            <div ref={chatEnd} />
          </div>
          <div className="chat-input">
            <input
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === "Enter" && send()}
              placeholder="Escribele a Illo..."
              disabled={loading}
            />
            <button onClick={send} disabled={loading || !input.trim()}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/>
              </svg>
            </button>
          </div>
        </section>
      </div>
    </div>
  );
}

import { createRoot } from "react-dom/client";
createRoot(document.getElementById("root")).render(<App />);
