import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { io } from "socket.io-client";
import {
  Activity,
  Bot,
  Camera,
  Gauge,
  DoorClosed,
  Lightbulb,
  Lock,
  Database,
  Mic,
  Power,
  Send,
  Shield,
  Thermometer,
  Wifi,
  WifiOff,
  Zap,
} from "lucide-react";
import "./styles.css";

const API_BASE = "";

function deviceIcon(type) {
  const props = { size: 18, strokeWidth: 2 };
  if (type === "light") return <Lightbulb {...props} />;
  if (type === "thermostat") return <Thermometer {...props} />;
  if (type === "door") return <DoorClosed {...props} />;
  if (type === "security") return <Shield {...props} />;
  if (type === "camera") return <Camera {...props} />;
  return <Power {...props} />;
}

function describeDevice(device) {
  if (device.device_type === "light") {
    return `${device.is_on ? "On" : "Off"} · ${device.brightness}% · ${device.color}`;
  }
  if (device.device_type === "thermostat") {
    return `${device.target_temperature}C target · ${device.mode}`;
  }
  if (device.device_type === "door") {
    return `${device.is_open ? "Open" : "Closed"} · ${device.is_locked ? "Locked" : "Unlocked"}`;
  }
  if (device.device_type === "security") {
    return `${device.mode}${device.alarm_triggered ? " · alarm" : ""}`;
  }
  if (device.device_type === "camera") {
    return device.is_recording ? "Recording" : "Idle";
  }
  return device.is_on ? "On" : "Off";
}

function App() {
  const [connected, setConnected] = useState(false);
  const [status, setStatus] = useState(null);
  const [devices, setDevices] = useState([]);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);

  const socket = useMemo(() => io("/", { transports: ["websocket", "polling"] }), []);

  useEffect(() => {
    socket.on("connect", () => setConnected(true));
    socket.on("disconnect", () => setConnected(false));
    socket.on("status:update", setStatus);
    socket.on("devices:update", setDevices);
    socket.on("history:update", (history) => setMessages(history || []));
    socket.on("chat:message", (payload) => {
      setStatus(payload.status);
      setDevices(payload.devices || []);
      setMessages(payload.history || []);
      setBusy(false);
    });
    socket.on("chat:error", () => setBusy(false));

    fetch(`${API_BASE}/api/status`).then((res) => res.json()).then(setStatus).catch(() => {});
    fetch(`${API_BASE}/api/devices`).then((res) => res.json()).then(setDevices).catch(() => {});
    fetch(`${API_BASE}/api/history`).then((res) => res.json()).then(setMessages).catch(() => {});

    return () => socket.disconnect();
  }, [socket]);

  function sendMessage(event) {
    event.preventDefault();
    const message = input.trim();
    if (!message || busy) return;
    setBusy(true);
    setInput("");
    socket.emit("chat:send", { message });
  }

  async function commandDevice(device, action, value) {
    const response = await fetch(`${API_BASE}/api/devices/command`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ device_id: device.device_id, action, value }),
    });
    const payload = await response.json();
    setDevices(payload.devices || devices);
  }

  return (
    <main className="shell">
      <header className="topbar">
        <div className="brand">
          <div className="brand-mark"><Bot size={22} /></div>
          <div>
            <h1>JARVIS Console</h1>
            <p>{status?.status || "initializing"} · {status?.smart_home_devices ?? 0} devices</p>
          </div>
        </div>
        <div className={`connection ${connected ? "online" : "offline"}`}>
          {connected ? <Wifi size={18} /> : <WifiOff size={18} />}
          {connected ? "Live" : "Offline"}
        </div>
      </header>

      <section className="status-strip">
        <div><Activity size={18} /><span>Skills</span><strong>{status?.skills_registered ?? 0}</strong></div>
        <div><Bot size={18} /><span>Custom</span><strong>{status?.custom_skills ?? 0}</strong></div>
        <div><Shield size={18} /><span>NLU</span><strong>{status?.nlu_model || "none"}</strong></div>
        <div><Database size={18} /><span>Memory</span><strong>{status?.memory_messages ?? 0}</strong></div>
        <div><Gauge size={18} /><span>Latency</span><strong>{status?.performance?.last_response_ms ? `${status.performance.last_response_ms}ms` : "idle"}</strong></div>
        <div><Mic size={18} /><span>Wake</span><strong>{status?.wake_word || "jarvis"}</strong></div>
        <div><Zap size={18} /><span>Rules</span><strong>{status?.automation?.enabled_rules ?? 0}</strong></div>
      </section>

      <section className="workspace">
        <section className="chat-panel">
          <div className="panel-head">
            <h2>Conversation</h2>
          </div>
          <div className="messages">
            {messages.length === 0 && <div className="empty">Send a command to JARVIS.</div>}
            {messages.map((message, index) => (
              <div className={`message ${message.speaker}`} key={`${message.timestamp}-${index}`}>
                <span>{message.speaker}</span>
                <p>{message.text}</p>
              </div>
            ))}
          </div>
          <form className="composer" onSubmit={sendMessage}>
            <input
              value={input}
              onChange={(event) => setInput(event.target.value)}
              placeholder="Turn on the kitchen light"
              aria-label="Message JARVIS"
            />
            <button type="submit" disabled={busy || !input.trim()} title="Send command">
              <Send size={18} />
            </button>
          </form>
        </section>

        <section className="device-panel">
          <div className="panel-head">
            <h2>Smart Home</h2>
          </div>
          <div className="device-grid">
            {devices.map((device) => (
              <article className="device-card" key={device.device_id}>
                <div className="device-title">
                  <div className={`device-icon ${device.is_on ? "active" : ""}`}>
                    {deviceIcon(device.device_type)}
                  </div>
                  <div>
                    <h3>{device.name}</h3>
                    <p>{device.location}</p>
                  </div>
                </div>
                <div className="device-state">{describeDevice(device)}</div>
                <div className="device-actions">
                  {device.device_type === "door" ? (
                    <>
                      <button title="Lock" onClick={() => commandDevice(device, "lock")}><Lock size={16} /></button>
                      <button onClick={() => commandDevice(device, "unlock")}>Unlock</button>
                    </>
                  ) : device.device_type === "security" ? (
                    <>
                      <button onClick={() => commandDevice(device, "arm", "away")}>Arm</button>
                      <button onClick={() => commandDevice(device, "disarm")}>Disarm</button>
                    </>
                  ) : (
                    <>
                      <button onClick={() => commandDevice(device, "turn_on")}>On</button>
                      <button onClick={() => commandDevice(device, "turn_off")}>Off</button>
                    </>
                  )}
                </div>
              </article>
            ))}
          </div>
        </section>
      </section>
    </main>
  );
}

createRoot(document.getElementById("root")).render(<App />);
