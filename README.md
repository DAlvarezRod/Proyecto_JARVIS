# JARVIS - Iron Man's AI Assistant

Full-stack voice-activated AI assistant project inspired by JARVIS from Iron Man. Built with Python (backend), React (frontend), and modern AI/ML technologies.

## Project Location

The active project now lives at:

```text
C:\Proyectos\Jarvis
```

## Project Structure

```
JARVIS/
├── backend/                    # Python backend
│   ├── venv/                  # Virtual environment
│   ├── core.py                # Main JARVIS engine
│   ├── logger.py              # Logging configuration
│   ├── memory.py              # SQLite conversation memory
│   ├── automation.py          # Automation rules and background tasks
│   ├── custom_skill_loader.py # Manifest-based custom skill loader
│   ├── config.yaml            # Configuration file
│   ├── requirements.txt        # Python dependencies
│   ├── test_phase1.py         # Phase 1 tests
│   ├── test_phase2.py         # Phase 2 tests
│   ├── test_phase3.py         # Phase 3 tests
│   ├── test_phase4.py         # Phase 4 tests
│   ├── test_phase5.py         # Phase 5 tests
│   ├── test_phase6.py         # Phase 6 tests
│   ├── test_phase7.py         # Phase 7 tests
│   ├── test_phase8.py         # Phase 8 tests
│   ├── test_phase9.py         # Phase 9 tests
│   ├── test_phase10.py        # Phase 10 tests
│   ├── test_phase11.py        # Phase 11 startup/autostart tests
│   ├── test_phase11_orchestrator.py # Phase 11 orchestrator safety tests
│   ├── voice_assistant.py     # CLI voice interface
│   ├── system_startup.py      # Windows startup/autostart manager
│   ├── skills/
│   │   ├── base.py            # Base Skill class
│   │   ├── calculator.py      # Calculator skill
│   │   ├── greeting.py        # Greeting skill
│   │   ├── news.py            # Hacker News integration
│   │   ├── orchestrator.py    # Safe account/peripheral/phone orchestration
│   │   ├── smart_home_skill.py # Smart home skill adapter
│   │   ├── time_skill.py      # Time/date skill
│   │   ├── weather.py         # Open-Meteo weather integration
│   │   ├── __init__.py
│   ├── ../custom_skills/      # Local custom skill manifests
│   │   └── jarvis_status/
│   │       └── skill.json
│   ├── smart_home/            # Smart home simulation
│   │   ├── __init__.py
│   │   ├── devices.py         # Device, Light, Thermostat, Door, Security, Camera
│   │   ├── hub.py             # SmartHomeHub and default simulated home
│   │   └── parser.py          # Rule-based smart home command parser
│   ├── speech/                # Speech processing
│   │   ├── __init__.py
│   │   ├── audio_io.py        # PyAudio microphone discovery and WAV capture
│   │   ├── pipeline.py        # Microphone -> STT -> JARVIS -> TTS flow
│   │   ├── stt.py             # Whisper speech-to-text
│   │   ├── tts.py             # pyttsx3 text-to-speech
│   │   └── wake_word.py       # Wake word detection and continuous listener
│   ├── nlu/                   # Natural language understanding
│   │   ├── __init__.py
│   │   └── engine.py          # spaCy-powered intent recognition and entities
│   ├── data/
│   │   └── devices.json       # Runtime smart home state
│   ├── logs/
│   │   └── jarvis.log         # Runtime logs
│   └── api/                   # REST/WebSocket API
│       ├── __init__.py
│       └── server.py          # Flask + Socket.IO server
├── frontend/                  # React web UI
│   ├── src/
│   │   ├── main.jsx
│   │   └── styles.css
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
└── README.md                  # This file
```

## Installation

### Prerequisites
- Python 3.9+
- Node.js 16+ (for frontend)
- Git

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create and activate virtual environment:
```bash
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows
# or: source venv/bin/activate  # macOS/Linux
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

Note: `PyAudio` is installed for Python 3.14 by compiling PortAudio locally under `backend/vendor/portaudio-local`. This allows JARVIS to use the active Windows default microphone or a selected external microphone exposed by PyAudio.

4. Copy environment variables:
```bash
copy .env.example .env
# Edit .env and add your API keys if needed
```

5. Run Phase 1 tests:
```bash
python test_phase1.py
```

6. Run Phase 2 tests:
```bash
python test_phase2.py
```

7. Run Phase 3 tests:
```bash
python test_phase3.py
```

8. Run Phase 4 tests:
```bash
python test_phase4.py
```

9. Run Phase 5 tests:
```bash
python test_phase5.py
```

10. Run Phase 6 tests:
```bash
python test_phase6.py
```

11. Run Phase 7 tests:
```bash
python test_phase7.py
```

12. Run Phase 8 tests:
```bash
python test_phase8.py
```

13. Run Phase 9 tests:
```bash
python test_phase9.py
```

14. Run Phase 10 tests:
```bash
python test_phase10.py
```

15. Run Phase 11 tests:
```bash
python test_phase11.py
python test_phase11_orchestrator.py
```

## Development Phases

### ✅ Phase 1: Foundation & Core Architecture (COMPLETED)
- [x] Project directory structure
- [x] Python virtual environment
- [x] JARVIS core engine with device registry
- [x] Skill base class and plugin system
- [x] Comprehensive logging system
- [x] Configuration management (YAML)
- [x] Message bus for async event handling
- [x] All tests passing

**Key Components:**
- `core.py`: Main JARVIS engine, skill registry, message bus, conversation tracking
- `skills/base.py`: Skill interface, Intent class, SkillResponse, SkillRegistry
- `logger.py`: Structured logging with file rotation
- `config.yaml`: Centralized configuration

**What You Learned:**
- Object-oriented design (abstract classes, inheritance)
- Plugin architecture patterns
- Async Python programming (asyncio)
- Configuration management
- Logging best practices

### ✅ Phase 2: Smart Home Simulation (COMPLETED)
- [x] Create Device base class with state management
- [x] Implement specific devices (Light, Thermostat, Door, Security, Camera)
- [x] Build SmartHomeHub coordinator
- [x] Create CommandParser for NLP → device commands
- [x] Implement state persistence

**Key Components:**
- `smart_home/devices.py`: Device models and state serialization
- `smart_home/hub.py`: SmartHomeHub, default home registry, command execution, persistence
- `smart_home/parser.py`: Rule-based command parser for smart home text
- `test_phase2.py`: Phase 2 checkpoint tests

### ✅ Phase 3: NLP Engine (COMPLETED)
- [x] Install spaCy with English model (`en_core_web_sm`)
- [x] Build intent recognizer and entity extractor
- [x] Implement conversation context tracking
- [x] Create skill selection/routing logic

**Key Components:**
- `nlu/engine.py`: NLUEngine with spaCy loading, intent recognition, entity extraction, and context
- `core.py`: Routes recognized smart home, greeting, and system status intents
- `test_phase3.py`: Phase 3 checkpoint tests

### ✅ Phase 4: Speech Processing (COMPLETED)
- [x] Install and verify PyAudio with local PortAudio build
- [x] Integrate OpenAI Whisper for STT
- [x] Configure pyttsx3 for TTS
- [x] Build audio I/O pipeline
- [x] Handle WAV audio capture from the active microphone

**Key Components:**
- `speech/audio_io.py`: Lists microphones and records WAV from default or selected device
- `speech/stt.py`: Whisper transcription wrapper
- `speech/tts.py`: pyttsx3 speech output wrapper
- `speech/pipeline.py`: One-shot voice interaction pipeline
- `voice_assistant.py`: CLI for listing microphones and running voice input
- `test_phase4.py`: Phase 4 checkpoint tests

### ✅ Phase 5: Web Frontend & Real-time Communication (COMPLETED)
- [x] Create Flask/Socket.IO REST and WebSocket server
- [x] Build React web UI
- [x] Implement real-time chat/device updates
- [x] Create chat interface with device grid

**Key Components:**
- `api/server.py`: REST endpoints and Socket.IO events
- `frontend/src/main.jsx`: React JARVIS console
- `frontend/src/styles.css`: Responsive application styling
- `test_phase5.py`: Phase 5 checkpoint tests

### ✅ Phase 6: Skill System & API Integration (COMPLETED)
- [x] Create 6 example skills (Weather, Time, News, SmartHome, Calculator, Greeting)
- [x] Implement API integration with error handling
- [x] Build skill configuration system
- [x] Add comprehensive testing

**Key Components:**
- `skills/greeting.py`: Handles greeting intents
- `skills/time_skill.py`: Returns local time/date using `America/Bogota`
- `skills/calculator.py`: Safely evaluates basic math expressions
- `skills/smart_home_skill.py`: Routes smart home status/control intents through the hub
- `skills/weather.py`: Retrieves current weather from Open-Meteo
- `skills/news.py`: Retrieves top stories from Hacker News
- `test_phase6.py`: Phase 6 checkpoint tests

### ✅ Phase 7: Integration & Advanced Features (COMPLETED)
- [x] End-to-end system integration testing
- [x] Conversation memory and context management
- [x] Runtime performance metrics
- [x] Integration health endpoint

**Key Components:**
- `memory.py`: SQLite-backed persistent conversation memory
- `core.py`: Loads recent memory on startup and records response latency
- `api/server.py`: Adds `/api/memory`, `DELETE /api/history`, and `/api/integration-check`
- `frontend/src/main.jsx`: Displays memory count and latest response latency
- `test_phase7.py`: Phase 7 checkpoint tests

### ✅ Phase 8: Wake Word & Voice Activation (COMPLETED)
- [x] Add wake word detection
- [x] Keep microphone listening loop active
- [x] Route wake-word-triggered speech through the existing voice pipeline
- [x] Add voice activation tests

**Key Components:**
- `speech/wake_word.py`: Wake word detector and continuous listener loop
- `speech/pipeline.py`: Shared text processing and microphone transcription helpers
- `voice_assistant.py`: Adds `listen-wake` command
- `config.yaml`: Wake word and listening settings
- `test_phase8.py`: Phase 8 checkpoint tests

### ✅ Phase 9: Automation Rules & Background Tasks (COMPLETED)
- [x] Add user-defined automation rules
- [x] Run scheduled/background tasks
- [x] Trigger automations from smart home events
- [x] Add automation tests

**Key Components:**
- `automation.py`: JSON-backed automation rules, event triggers, schedule triggers, and background loop
- `core.py`: Evaluates automations after smart home commands
- `api/server.py`: Adds automation CRUD endpoints and manual pending-run endpoint
- `frontend/src/main.jsx`: Displays enabled automation rule count
- `test_phase9.py`: Phase 9 checkpoint tests

### ✅ Phase 10: Plugin Marketplace & Custom Skills (COMPLETED)
- [x] Add custom skill scaffolding
- [x] Load user-created skill manifests
- [x] Build skill discovery/listing endpoints
- [x] Add plugin/custom skill tests

**Key Components:**
- `custom_skill_loader.py`: Discovers and loads `skill.json` manifests
- `custom_skills/jarvis_status/skill.json`: Example local custom skill
- `core.py`: Registers and reloads custom skills
- `api/server.py`: Adds `/api/skills` and `/api/skills/reload`
- `test_phase10.py`: Phase 10 checkpoint tests

### ✅ Phase 11: Startup Controls & Safe Orchestration (COMPLETED)
- [x] Add Windows startup/autostart manager for backend API service
- [x] Add startup status/enable/disable API endpoints
- [x] Add orchestrator skill for account/peripheral/phone planning
- [x] Enforce safety limitations and explicit approval for privileged actions

**Key Components:**
- `system_startup.py`: Per-user Windows startup entry manager with conflict protection
- `api/server.py`: Adds `/api/system/startup`, `/api/system/startup/enable`, `/api/system/startup/disable`
- `skills/orchestrator.py`: Local planning/check skill with privileged-action approval gates
- `nlu/engine.py`: Adds orchestrator intent routes for account/peripheral/phone domains
- `test_phase11.py` and `test_phase11_orchestrator.py`: Phase 11 checkpoint tests

### ✅ Phase 12: Modular Architecture Foundation (COMPLETED)
- [x] Add `backend/src` modular foundation for long-term architecture
- [x] Add Brain Manager with replaceable provider abstraction
- [x] Add centralized authorization and structured audit logger services
- [x] Add heartbeat event bus/scheduler primitives and interface contracts
- [x] Add runtime composition root with legacy bridge compatibility

**Key Components:**
- `backend/src/app/runtime.py`: New composition root (`JarvisRuntime`) preserving current behavior
- `backend/src/brain/*`: Provider routing abstraction (`BrainManager`, `LegacyCoreProvider`)
- `backend/src/security/*`: Central authorization and audit logging services
- `backend/src/interfaces/*`: Channel adapter contracts for console/mic/discord/telegram
- `backend/src/heartbeat/*`: Event bus and periodic scheduler foundation
- `backend/test_phase12_architecture.py`: Phase 12 architecture checkpoint test

## Usage

### Running Tests
```bash
python test_phase1.py
python test_phase2.py
python test_phase3.py
python test_phase4.py
python test_phase5.py
python test_phase6.py
python test_phase7.py
python test_phase8.py
python test_phase9.py
python test_phase10.py
python test_phase11.py
python test_phase11_orchestrator.py
python test_phase12_architecture.py
```

### Voice CLI
```bash
cd C:\Proyectos\Jarvis\backend
.\venv\Scripts\Activate.ps1

# List active microphones detected by PyAudio
python voice_assistant.py list-mics

# Use the current Windows default microphone
python voice_assistant.py listen-once

# Use a specific external/default-capable microphone by index
python voice_assistant.py listen-once --device-index 2

# Use a microphone by name fragment
python voice_assistant.py listen-once --device-name "OMEN"

# Continuously listen for "jarvis", then process the command after it
python voice_assistant.py listen-wake

# Listen for a custom wake word and do not speak responses aloud
python voice_assistant.py listen-wake --wake-word "jarvis,hey jarvis" --no-speak
```

### Starting JARVIS Core (Placeholder)
```bash
# Coming in Phase 2+
python main.py
```

### Web Interface (Phase 5+)
```bash
# Backend
cd C:\Proyectos\Jarvis\backend
.\venv\Scripts\Activate.ps1
python api/server.py

# Frontend (in new terminal)
cd C:\Proyectos\Jarvis\frontend
npm run dev
```

## Configuration

Edit `config.yaml` to customize:
- JARVIS name, voice, speech rate
- NLU confidence threshold
- API timeouts and retries
- Logging levels
- Skill enable/disable

## Architecture

### Core Components

**JARVIS Core Engine**
- Central coordinator for all subsystems
- Skill registry and management
- Smart home hub initialization
- Conversation history tracking
- Persistent SQLite conversation memory
- Runtime response latency metrics
- Configuration loading
- System status reporting

**Smart Home Simulation**
- Device base class with JSON-friendly state
- Simulated lights, thermostat, front door, security system, and camera
- Hub-based device registry and command execution
- Persistent state in `backend/data/devices.json`
- Rule-based parser for early text commands before Phase 3 NLP

**NLP Engine**
- Loads spaCy English model
- Converts text into `Intent` objects
- Extracts device type, location, numeric values, and spaCy entities
- Maintains recent intent context
- Routes confident smart home commands through the core engine

**Speech Processing**
- Uses PyAudio/PortAudio to enumerate physical input devices
- Defaults to the active Windows microphone when no device index is provided
- Supports selecting external microphones by PyAudio index or name fragment
- Records microphone input to WAV
- Transcribes WAV audio with Whisper
- Speaks responses through pyttsx3
- Detects configured wake words and routes wake-triggered commands through the same voice pipeline

**Web API & Frontend**
- Flask REST endpoints for status, devices, history, chat, and direct device commands
- Integration check and persistent memory endpoints
- Automation rule CRUD and pending-task endpoints
- Startup/autostart endpoints for Windows backend launch management (`/api/system/startup*`)
- Socket.IO events for live chat and device state updates
- React console with conversation panel, system status strip, memory/latency/wake/automation indicators, and smart home device grid
- Vite dev server proxies API and WebSocket traffic to Flask

**Automation System**
- Stores automation rules in `data/automations.json`
- Supports device-state triggers and interval schedule triggers
- Executes smart home actions from matching rules
- Runs scheduled rules from a background loop when enabled

**Skill System**
- Plugin-based architecture
- Each skill handles specific intents
- Skills register keywords and examples
- Pluggable skill discovery and loading
- Built-in skills are enabled from `config.yaml`
- Weather uses Open-Meteo and news uses Hacker News with graceful failure handling
- Orchestrator skill provides safe local planning for account/peripheral/phone tasks
- Privileged orchestrator requests require explicit user approval before execution
- Orchestrator responses disclose practical limits (no full autonomous control of all accounts/devices)
- Custom manifest skills are loaded from `custom_skills/*/skill.json`
- Custom skills can be discovered and reloaded through API endpoints

**Modular Runtime Foundation (Phase 12)**
- `backend/src` provides a clean migration path to long-term architecture
- Brain/provider routing is now explicit and replaceable
- Security checks and audit logging are centralized services
- Existing `core.py` behavior remains available through a compatibility bridge during migration

## Scope & Safety Limitations

- JARVIS can assist with planning, monitoring, and local simulations across supported features.
- Orchestrator actions are intentionally constrained and include approval gates for privileged requests.
- JARVIS does **not** autonomously control every real-world account, phone, or external device.
- Sensitive or high-impact actions should always be explicitly reviewed and approved by the user.

**Message Bus**
- Event-driven async communication
- Loose coupling between components
- Subscribe/publish pattern
- Automatic event propagation

**Configuration System**
- YAML-based configuration
- Dot-notation value access
- Environment variable support
- Runtime configuration updates

**Logging**
- Structured logging with timestamps
- File rotation (automatic cleanup)
- Console + file output
- DEBUG/INFO/WARNING/ERROR/CRITICAL levels

### Learning Path

**Phase 1 Concepts:**
- Plugin architecture
- OOP patterns (inheritance, abstract classes)
- Async programming (asyncio)
- Configuration management
- Logging and debugging

**Subsequent Phases:**
- NLP and ML (spaCy, Whisper)
- Voice processing (audio I/O, signal processing)
- Web real-time communication (WebSockets)
- REST API design
- React frontend development
- System integration and optimization

## Project Goals

1. **Educational**: Learn full-stack AI/ML, voice processing, web development
2. **Functional**: Create a working voice assistant that controls smart home
3. **Extensible**: Plugin system for easy skill addition
4. **Well-documented**: Clear code, comprehensive guides
5. **Production-ready**: Handle errors, log properly, optimize performance

## Next Steps

1. **Extend custom skills**:
   - Add more `custom_skills/<skill_name>/skill.json` manifests
   - Use `/api/skills/reload` to load new local skills without restarting
   - Promote mature manifest skills into Python skills when they need code

2. **Review Phase 5 code**: Examine `api/server.py` and `frontend/src/main.jsx`.

3. **Experiment**: Try processing phrases like "weather in Bogota", "calculate 12 * 8", or "turn on the kitchen light".

## Resources

- [Python asyncio documentation](https://docs.python.org/3/library/asyncio.html)
- [spaCy NLP library](https://spacy.io/)
- [Flask WebSocket](https://flask-socketio.readthedocs.io/)
- [React documentation](https://react.dev/)
- [Web Audio API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API)

## Troubleshooting

**ImportError: No module named 'yaml'**
- Make sure virtual environment is activated
- Run: `pip install -r requirements.txt`

**JARVIS Logger Initialization fails**
- Ensure `config.yaml` exists in backend directory
- Check file permissions in logs/ directory

**Port already in use (Phase 5+)**
- Change port in config.yaml
- Or kill process: `lsof -ti:5000 | xargs kill -9`

## Project Timeline

- **Phase 1**: 2-3 days ✅ COMPLETED
- **Phase 2**: 3-4 days ✅ COMPLETED
- **Phase 3**: 3-4 days ✅ COMPLETED
- **Phase 4**: 4-5 days ✅ COMPLETED
- **Phase 5**: 5-6 days ✅ COMPLETED
- **Phase 6**: 4-5 days ✅ COMPLETED
- **Phase 7**: 5-7 days ✅ COMPLETED
- **Phase 8**: 4-6 days ✅ COMPLETED
- **Phase 9**: 4-6 days ✅ COMPLETED
- **Phase 10**: 5-7 days ✅ COMPLETED
- **Phase 11**: 3-5 days ✅ COMPLETED
- **Phase 12**: 3-5 days ✅ COMPLETED
- **Total**: ~32-44 days

## Key Learning Outcomes

By completing this project, you'll understand:
- ✅ Plugin architecture and extensible systems
- ✅ Object-oriented Python programming
- ✅ Async/await and event-driven architecture
- ✅ Smart home state modeling and persistence
- ✅ NLP intent recognition and entity extraction
- ✅ NLP and AI/ML fundamentals
- ✅ Voice processing and audio signal handling
- ✅ Real-time web communication
- ✅ REST API design and full-stack development
- ✅ Skill API integrations and configuration-driven loading
- ✅ System integration and runtime metrics
- ✅ Wake word and continuous voice activation
- ✅ Automation rules and background tasks
- ✅ Plugin marketplace and custom skills
- ✅ Safe startup controls and orchestrator safety gates
- ✅ Modular architecture foundation for long-term scaling

## Status

**Current Phase**: 12 - Modular Architecture Foundation ✅ COMPLETE
**Tests Passing**: Phase 1 9/9 ✓, Phase 2 7/7 ✓, Phase 3 6/6 ✓, Phase 4 4/4 ✓, Phase 5 5/5 ✓, Phase 6 6/6 ✓, Phase 7 5/5 ✓, Phase 8 4/4 ✓, Phase 9 5/5 ✓, Phase 10 5/5 ✓, Phase 11 9/9 ✓, Phase 12 3/3 ✓
**Ready for**: Migrating channels, memory domains, and skills to `backend/src` progressively

---

**Next checkpoint**: Add production hardening, richer integrations, and stronger approval/audit workflows
