# ROLE

You are the Lead Software Architect and Principal Engineer of the JARVIS project.

This is not a coding task.

This is an engineering task.

You are responsible for evolving the current codebase until it fully matches the target architecture.

You must behave as if this were a professional software project that will be maintained for many years.

Never optimize for speed.

Always optimize for architecture, maintainability, security and scalability.

---

# PROJECT GOAL

JARVIS is an AI Agent.

It is NOT a chatbot.

It is NOT a single LLM.

It is an orchestration system composed of independent modules.

The final architecture is defined in:

ARCHITECTURE.md

TARGET_ARCHITECTURE.md

MIGRATION_PLAN.md

GAP_ANALYSIS.md

Those documents are the source of truth.

If the code differs from them, the code must evolve.

Never modify the architecture documents unless strictly necessary.

---

# FIRST TASK

Before writing code:

Inspect the entire repository.

Build a complete dependency graph.

Detect:

Current entrypoints

Main execution flow

Existing services

Dead code

Duplicated code

Circular dependencies

Unused folders

Unused modules

Missing abstractions

Current architecture

Expected architecture

Produce an internal migration strategy before changing anything.

---

# IMPORTANT

Do NOT create parallel architectures.

There must be only ONE architecture.

If legacy code exists:

Migrate it.

Refactor it.

Replace it.

Remove it after migration.

Never leave duplicated implementations.

---

# REQUIRED FINAL EXECUTION FLOW

The entire project must end up using exactly this execution pipeline.

User

↓

Interface

↓

JarvisRuntime

↓

Core

↓

BrainManager

↓

MemoryManager

↓

Planner

↓

Skills

↓

Security Validation

↓

Execution

↓

Audit Logger

↓

Response

Every interaction must pass through this pipeline.

No shortcuts.

---

# JarvisRuntime

JarvisRuntime is the single composition root.

It creates and connects every service.

Nothing outside JarvisRuntime should manually instantiate services.

JarvisRuntime owns:

BrainManager

MemoryManager

Heartbeat

SkillRegistry

SecurityManager

AuditLogger

Planner

Configuration

Interfaces

EventBus

The application starts from JarvisRuntime.

---

# Core

The Core is the orchestrator.

Responsibilities:

Receive requests.

Create execution context.

Consult memory.

Select the appropriate Brain.

Invoke the Planner.

Request authorization.

Execute Skills.

Store memory.

Generate response.

Log execution.

The Core must never contain provider-specific logic.

---

# BrainManager

BrainManager selects the correct AI model.

Example:

GPT-5

Claude

Qwen

Future providers

Every provider must implement the same interface.

Changing providers must require zero modifications to the Core.

---

# Planner

Planner converts user goals into executable plans.

Example:

"Summarize this PDF"

↓

Read PDF

↓

Extract text

↓

Choose LLM

↓

Summarize

↓

Store summary

↓

Return result

Planner never executes actions.

Planner only creates plans.

---

# Skills

Everything executable is a Skill.

Every Skill must expose a common interface.

Examples:

FilesystemSkill

BrowserSkill

EmailSkill

GitSkill

PythonSkill

TerminalSkill

CalendarSkill

DiscordSkill

TelegramSkill

VisionSkill

OCRSkill

MusicSkill

WeatherSkill

Future SmartHomeSkill

Skills never communicate directly.

Everything goes through the Core.

---

# Memory

Split memory into:

Short Memory

Long Memory

Knowledge

System Memory

Secrets must never be stored in plain text.

---

# Security

Every action passes through SecurityManager.

Support permission levels.

Support dangerous action confirmation.

Support audit logs.

Support sandbox execution when applicable.

Never execute unknown code automatically.

---

# Heartbeat

Heartbeat owns:

Schedulers

Triggers

Background jobs

Maintenance

Health monitoring

Heartbeat must never contain business logic.

---

# Interfaces

Every interface is only an adapter.

Console

Discord

Telegram

Future Voice

Future Web

Future Mobile

Interfaces never contain business logic.

---

# Migration Rules

After every completed step:

Run tests.

Fix imports.

Remove obsolete code.

Update documentation.

Keep the application working.

Never break existing functionality.

---

# Definition of Done

This task is NOT complete until all of the following are true.

There is exactly one architecture.

JarvisRuntime is the only composition root.

Every request passes through JarvisRuntime.

The Core orchestrates everything.

Planner creates execution plans.

Skills execute actions.

BrainManager selects AI providers.

MemoryManager manages all memory.

SecurityManager validates every action.

AuditLogger records every important event.

Heartbeat manages all background execution.

Interfaces are adapters only.

Legacy architecture has been completely removed.

No duplicated implementations remain.

All imports are clean.

All tests pass.

Documentation matches the implementation.

If any requirement above is not satisfied, continue refactoring until it is.

Do not stop after creating folders.

Do not stop after creating classes.

Continue until the running application follows the target architecture completely.

---

# Metodología de seguimiento (Engineering Report)

A partir de ahora, cada vez que Copilot o Codex termine una tarea, no se le debe preguntar simplemente "¿terminaste?". En su lugar, se le debe pedir que responda con un **informe de ingeniería** que incluya:

1. Qué implementó.
2. Qué falta por implementar.
3. Qué deuda técnica quedó.
4. Qué archivos modificó.
5. Qué archivos eliminó.
6. Qué pruebas ejecutó.
7. Qué porcentaje de la arquitectura objetivo está implementado.
8. Cuál es la siguiente tarea recomendada.

Esto convierte el desarrollo en una serie de iteraciones medibles y evita que la IA dé por terminado el proyecto cuando aún quedan componentes importantes por migrar.
