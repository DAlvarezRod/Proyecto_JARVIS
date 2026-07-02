import { useState, useRef, useEffect } from "react";
import "./styles.css";

const API = "";

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState(null);
  const chatEnd = useRef(null);

  useEffect(() => {
    fetch(`${API}/api/status`).then(r => r.json()).then(setStatus).catch(() => {});
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
      const res = await fetch(`${API}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });
      const data = await res.json();
      setMessages(prev => [...prev, { role: "assistant", text: data.response }]);
      if (data.status) setStatus(data.status);
    } catch (e) {
      setMessages(prev => [...prev, { role: "assistant", text: "Error de conexión con el servidor." }]);
    }
    setLoading(false);
  };

  return (
    <div className="app">
      <header className="header">
        <div className="logo">
          <div className="logo-icon">I</div>
          <div>
            <h1>Illo</h1>
            <span className="subtitle">
              {status ? `${status.name} · v${status.version || "2.0"} · ${status.skills_loaded || 0} skills` : "Conectando..."}
            </span>
          </div>
        </div>
        <div className="status-badge">{status ? "En línea" : "Offline"}</div>
      </header>

      <div className="main chat-only">
        <section className="chat-section">
          <div className="chat-messages">
            {messages.length === 0 && (
              <div className="empty-chat">
                <div className="empty-icon">I</div>
                <p>Hola, soy <strong>Illo</strong>. ¿En qué te puedo ayudar?</p>
              </div>
            )}
            {messages.map((m, i) => (
              <div key={i} className={`msg ${m.role}`}>
                <div className="msg-label">{m.role === "user" ? "Tú" : "Illo"}</div>
                <div className="msg-bubble">{m.text}</div>
              </div>
            ))}
            {loading && (
              <div className="msg assistant">
                <div className="msg-label">Illo</div>
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
              placeholder="Escríbele a Illo..."
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