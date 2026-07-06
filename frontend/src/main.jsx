import { useState, useRef, useEffect } from "react";
import "./styles.css";

const API = "";

function VaderFace({ size = 120, audioLevel = 0, listening = false }) {
  const scale = listening ? 1 + audioLevel * 0.15 : 1;
  const glow = listening ? 4 + audioLevel * 25 : 0;
  const eyeBright = 0.5 + audioLevel * 0.5;
  const droolLen = 8 + (listening ? audioLevel * 15 : 0);
  const mouthH = 8 + (listening ? audioLevel * 5 : 0);

  return (
    <svg viewBox="0 0 120 120" width={size} height={size}
      style={{
        transform: `scale(${scale})`,
        transition: "transform 0.1s ease-out",
        filter: glow > 0 ? `drop-shadow(0 0 ${glow}px #87CEEB)` : "none",
      }}
    >
      <defs>
        <radialGradient id="catHead" cx="50%" cy="40%" r="55%">
          <stop offset="0%" stopColor="#132d3e"/>
          <stop offset="100%" stopColor="#081820"/>
        </radialGradient>
        <radialGradient id="eyeGlow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#87CEEB" stopOpacity="0.9"/>
          <stop offset="100%" stopColor="#87CEEB" stopOpacity="0"/>
        </radialGradient>
      </defs>

      <path d="M28 30 L20 6 L48 24Z" fill="url(#catHead)" stroke="#87CEEB" strokeWidth="1" strokeOpacity="0.4"/>
      <path d="M92 30 L100 6 L72 24Z" fill="url(#catHead)" stroke="#87CEEB" strokeWidth="1" strokeOpacity="0.4"/>
      <path d="M30 28 L24 12 L44 24Z" fill="#87CEEB" opacity="0.06"/>
      <path d="M90 28 L96 12 L76 24Z" fill="#87CEEB" opacity="0.06"/>

      <ellipse cx="60" cy="52" rx="40" ry="38" fill="url(#catHead)" stroke="#87CEEB" strokeWidth="1.2" strokeOpacity="0.4"/>

      <circle cx="42" cy="44" r="14" fill="#0a1822" stroke="#87CEEB" strokeWidth="0.8" strokeOpacity="0.25"/>
      <circle cx="42" cy="44" r="10" fill="url(#eyeGlow)"
        style={listening ? { opacity: eyeBright } : undefined} className="eye-glow"/>
      <circle cx="44" cy="42" r="3.5" fill="#87CEEB"
        style={listening ? { opacity: eyeBright } : undefined}
        className={listening ? "" : "eye-glow"}/>
      <circle cx="42" cy="40" r="1.8" fill="white" opacity="0.25"/>

      <circle cx="78" cy="44" r="14" fill="#0a1822" stroke="#87CEEB" strokeWidth="0.8" strokeOpacity="0.25"/>
      <circle cx="78" cy="44" r="10" fill="url(#eyeGlow)"
        style={listening ? { opacity: eyeBright } : undefined} className="eye-glow"/>
      <circle cx="76" cy="42" r="3.5" fill="#87CEEB"
        style={listening ? { opacity: eyeBright } : undefined}
        className={listening ? "" : "eye-glow"}/>
      <circle cx="74" cy="40" r="1.8" fill="white" opacity="0.25"/>

      <path d="M57 58 L60 55 L63 58Z" fill="#87CEEB" opacity="0.3"/>

      <line x1="18" y1="55" x2="36" y2="58" stroke="#87CEEB" strokeWidth="0.8" opacity="0.2"/>
      <line x1="16" y1="62" x2="35" y2="62" stroke="#87CEEB" strokeWidth="0.8" opacity="0.15"/>
      <line x1="18" y1="69" x2="36" y2="66" stroke="#87CEEB" strokeWidth="0.8" opacity="0.2"/>
      <line x1="102" y1="55" x2="84" y2="58" stroke="#87CEEB" strokeWidth="0.8" opacity="0.2"/>
      <line x1="104" y1="62" x2="85" y2="62" stroke="#87CEEB" strokeWidth="0.8" opacity="0.15"/>
      <line x1="102" y1="69" x2="84" y2="66" stroke="#87CEEB" strokeWidth="0.8" opacity="0.2"/>

      <ellipse cx="60" cy={68} rx="12" ry={mouthH} fill="#040c12" stroke="#87CEEB" strokeWidth="1" strokeOpacity="0.3"/>

      <path d={`M54 ${66 + mouthH} Q52 ${66 + mouthH + droolLen * 0.5} 55 ${66 + mouthH + droolLen}`}
        fill="none" stroke="#87CEEB" strokeWidth="2.5" strokeLinecap="round" opacity="0.55"/>
      <ellipse cx="55" cy={66 + mouthH + droolLen} rx="2.5" ry="2" fill="#87CEEB" opacity="0.35"/>
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
  const [ttsEnabled, setTtsEnabled] = useState(false);
  const [speaking, setSpeaking] = useState(false);
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
      if (ttsEnabled && data.response) {
        setSpeaking(true);
        try {
          const audioRes = await fetch(API + "/api/tts", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text: data.response }),
          });
          if (audioRes.ok) {
            const blob = await audioRes.blob();
            const audioUrl = URL.createObjectURL(blob);
            const audio = new Audio(audioUrl);
            audio.onended = () => { URL.revokeObjectURL(audioUrl); setSpeaking(false); };
            audio.play();
          } else { setSpeaking(false); }
        } catch (e) { setSpeaking(false); }
      }
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
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <button
            className={"tts-btn" + (ttsEnabled ? " active" : "") + (speaking ? " speaking" : "")}
            onClick={() => setTtsEnabled(!ttsEnabled)}
            title={ttsEnabled ? "Desactivar voz" : "Activar voz"}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
              {ttsEnabled ? (
                <>
                  <path d="M19.07 4.93a10 10 0 0 1 0 14.14"/>
                  <path d="M15.54 8.46a5 5 0 0 1 0 7.07"/>
                </>
              ) : (
                <>
                  <line x1="23" y1="9" x2="17" y2="15"/>
                  <line x1="17" y1="9" x2="23" y2="15"/>
                </>
              )}
            </svg>
          </button>
          <div className={"status-badge" + (status ? "" : " offline")}>
            {status ? "EN LINEA" : "OFFLINE"}
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