import { useState, useRef, useEffect } from "react";
import "./styles.css";

const API = "";

function VaderFace({ size = 120, audioLevel = 0, listening = false }) {
  const scale = listening ? 1 + audioLevel * 0.15 : 1;
  const glow = listening ? 4 + audioLevel * 25 : 0;
  const eyeBright = 0.5 + audioLevel * 0.5;

  return (
    <svg viewBox="0 0 120 120" width={size} height={size}
      style={{
        transform: `scale(${scale})`,
        transition: "transform 0.1s ease-out",
        filter: glow > 0 ? `drop-shadow(0 0 ${glow}px #87CEEB)` : "none",
      }}
    >
      <defs>
        <radialGradient id="helmet" cx="50%" cy="35%" r="60%">
          <stop offset="0%" stopColor="#132d3e"/>
          <stop offset="100%" stopColor="#081820"/>
        </radialGradient>
        <radialGradient id="eyeGlow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#87CEEB" stopOpacity="0.9"/>
          <stop offset="100%" stopColor="#87CEEB" stopOpacity="0"/>
        </radialGradient>
        <linearGradient id="mouthGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#0d1f2d"/>
          <stop offset="100%" stopColor="#061018"/>
        </linearGradient>
      </defs>
      <path d="M60 8 C28 8 12 28 12 52 C12 68 18 82 30 92 Q44 104 60 106 Q76 104 90 92 C102 82 108 68 108 52 C108 28 92 8 60 8Z" fill="url(#helmet)" stroke="#87CEEB" strokeWidth="0.8" strokeOpacity="0.4"/>
      <path d="M60 8 C60 8 60 10 60 42" stroke="#87CEEB" strokeWidth="1.2" opacity="0.3"/>
      <path d="M18 48 Q60 32 102 48" fill="none" stroke="#87CEEB" strokeWidth="1.5" opacity="0.3"/>
      <path d="M16 52 Q14 68 22 85" fill="none" stroke="#87CEEB" strokeWidth="1" opacity="0.2"/>
      <path d="M104 52 Q106 68 98 85" fill="none" stroke="#87CEEB" strokeWidth="1" opacity="0.2"/>
      <path d="M22 50 L22 72 L30 78" fill="none" stroke="#87CEEB" strokeWidth="0.7" opacity="0.15"/>
      <path d="M98 50 L98 72 L90 78" fill="none" stroke="#87CEEB" strokeWidth="0.7" opacity="0.15"/>
      <ellipse cx="46" cy="22" rx="18" ry="8" fill="#87CEEB" opacity="0.04"/>
      <path d="M26 52 L42 46 L60 50 L78 46 L94 52" fill="none" stroke="#87CEEB" strokeWidth="1.8" strokeLinejoin="round" opacity="0.5"/>
      <path d="M30 56 L44 50 L50 58 L48 64 L32 64Z" fill="#061018" stroke="#87CEEB" strokeWidth="0.8" strokeLinejoin="round" strokeOpacity="0.3"/>
      <path d="M90 56 L76 50 L70 58 L72 64 L88 64Z" fill="#061018" stroke="#87CEEB" strokeWidth="0.8" strokeLinejoin="round" strokeOpacity="0.3"/>
      <circle cx="40" cy="57" r="8" fill="url(#eyeGlow)" style={listening ? { opacity: eyeBright } : undefined} className="eye-glow"/>
      <circle cx="80" cy="57" r="8" fill="url(#eyeGlow)" style={listening ? { opacity: eyeBright } : undefined} className="eye-glow"/>
      <ellipse cx="40" cy="57" rx="4" ry="3" fill="#87CEEB" style={listening ? { opacity: eyeBright } : undefined} className={listening ? "" : "eye-glow"}/>
      <ellipse cx="80" cy="57" rx="4" ry="3" fill="#87CEEB" style={listening ? { opacity: eyeBright } : undefined} className={listening ? "" : "eye-glow"}/>
      <circle cx="36" cy="54" r="2.5" fill="white" opacity="0.2"/>
      <circle cx="76" cy="54" r="2.5" fill="white" opacity="0.2"/>
      <circle cx="43" cy="59" r="1.2" fill="white" opacity="0.1"/>
      <circle cx="83" cy="59" r="1.2" fill="white" opacity="0.1"/>
      <path d="M56 66 L60 74 L64 66Z" fill="#061018" stroke="#87CEEB" strokeWidth="0.7" strokeOpacity="0.3"/>
      <line x1="60" y1="66" x2="60" y2="73" stroke="#87CEEB" strokeWidth="0.4" opacity="0.2"/>
      <path d="M34 78 Q38 74 60 74 Q82 74 86 78 L88 88 Q86 98 60 100 Q34 98 32 88Z" fill="url(#mouthGrad)" stroke="#87CEEB" strokeWidth="0.8" strokeOpacity="0.3"/>
      <line x1="40" y1="80" x2="80" y2="80" stroke="#87CEEB" strokeWidth="0.7" opacity="0.25"/>
      <line x1="38" y1="85" x2="82" y2="85" stroke="#87CEEB" strokeWidth="0.7" opacity="0.25"/>
      <line x1="39" y1="90" x2="81" y2="90" stroke="#87CEEB" strokeWidth="0.7" opacity="0.25"/>
      <line x1="42" y1="95" x2="78" y2="95" stroke="#87CEEB" strokeWidth="0.6" opacity="0.15"/>
      <circle cx="36" cy="82" r="1.5" fill="#87CEEB" opacity="0.15"/>
      <circle cx="84" cy="82" r="1.5" fill="#87CEEB" opacity="0.15"/>
      <ellipse cx="60" cy="102" rx="12" ry="3" fill="#87CEEB" opacity="0.02"/>
    </svg>
  );
}

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState(null);
  const [isListening, setIsListening] = useState(false);
  const [transcribing, setTranscribing] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
  const chatEnd = useRef(null);
  const audioCtxRef = useRef(null);
  const streamRef = useRef(null);
  const animRef = useRef(null);
  const recorderRef = useRef(null);
  const chunksRef = useRef([]);

  useEffect(() => {
    fetch(API + "/api/status").then(r => r.json()).then(setStatus).catch(() => {});
  }, []);

  useEffect(() => {
    chatEnd.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    return () => {
      if (animRef.current) cancelAnimationFrame(animRef.current);
      if (audioCtxRef.current) audioCtxRef.current.close().catch(() => {});
      if (streamRef.current) streamRef.current.getTracks().forEach(t => t.stop());
    };
  }, []);

  const send = async (overrideText) => {
    const text = (overrideText || input).trim();
    if (!text) return;
    if (!overrideText && loading) return;
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

  const startListening = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 256;
      ctx.createMediaStreamSource(stream).connect(analyser);
      audioCtxRef.current = ctx;
      const buf = new Uint8Array(analyser.frequencyBinCount);

      const tick = () => {
        analyser.getByteFrequencyData(buf);
        let sum = 0;
        for (let i = 1; i < 25; i++) sum += buf[i];
        setAudioLevel(Math.min(1, (sum / 24 / 255) * 3));
        animRef.current = requestAnimationFrame(tick);
      };
      tick();

      const recorder = new MediaRecorder(stream);
      chunksRef.current = [];
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };
      recorder.onstop = async () => {
        if (streamRef.current) {
          streamRef.current.getTracks().forEach(t => t.stop());
          streamRef.current = null;
        }
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        chunksRef.current = [];
        if (blob.size < 500) return;

        setTranscribing(true);
        try {
          const form = new FormData();
          form.append("audio", blob, "recording.webm");
          const res = await fetch(API + "/api/transcribe", { method: "POST", body: form });
          const data = await res.json();
          setTranscribing(false);
          if (data.text && data.text.trim()) {
            send(data.text.trim());
          } else if (data.error) {
            setMessages(prev => [...prev, { role: "assistant", text: "Error STT: " + data.error }]);
          }
        } catch (e) {
          setTranscribing(false);
          setMessages(prev => [...prev, { role: "assistant", text: "Error de transcripcion." }]);
        }
      };
      recorder.start();
      recorderRef.current = recorder;
      setIsListening(true);
    } catch (e) {
      setMessages(prev => [...prev, { role: "assistant", text: "No se pudo acceder al microfono." }]);
    }
  };

  const stopListening = () => {
    if (animRef.current) cancelAnimationFrame(animRef.current);
    if (audioCtxRef.current) {
      audioCtxRef.current.close().catch(() => {});
      audioCtxRef.current = null;
    }
    setAudioLevel(0);
    if (recorderRef.current && recorderRef.current.state === "recording") {
      recorderRef.current.stop();
    }
    recorderRef.current = null;
    setIsListening(false);
  };

  const toggleMic = () => {
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
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
              <div className={"empty-chat" + (isListening ? " listening" : "")}>
                <div className={"empty-vader" + (isListening ? " listening" : "")}>
                  <VaderFace size={110} audioLevel={audioLevel} listening={isListening} />
                </div>
                <div className="empty-text">
                  <p>Hola, soy <strong>ILLO</strong></p>
                  <p className="empty-hint">
                    {isListening ? "Te escucho..." : "Tu asistente personal. Preguntame lo que necesites."}
                  </p>
                </div>
              </div>
            )}
            {hasMessages && (
              <div className="top-vader">
                <div className={"top-vader-circle" + (isListening ? " listening" : "")}>
                  <VaderFace size={50} audioLevel={audioLevel} listening={isListening} />
                </div>
                <span className="top-vader-name">
                  {isListening ? "ESCUCHANDO..." : "ILLO"}
                </span>
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
            {transcribing && (
              <div className="msg assistant">
                <div className="msg-label">
                  <span className="msg-avatar"><VaderFace size={12} /></span>
                  ILLO
                </div>
                <div className="msg-bubble typing">Transcribiendo<span className="dots">...</span></div>
              </div>
            )}
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
              disabled={loading || transcribing}
            />
            <button
              className={"mic-btn" + (isListening ? " listening" : "")}
              onClick={toggleMic}
              disabled={loading || transcribing}
              title={isListening ? "Detener" : "Hablar"}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
                <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
                <line x1="12" y1="19" x2="12" y2="23"/>
                <line x1="8" y1="23" x2="16" y2="23"/>
              </svg>
            </button>
            <button onClick={() => send()} disabled={loading || transcribing || !input.trim()}>
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