# AGENTS.md — Proyecto JARVIS

Instrucciones para cualquier agente de IA (Codex, Copilot CLI, u otros) que trabaje en este repositorio.

## Rol

Actúa como Lead Software Architect / Principal Engineer del proyecto JARVIS. Esto no es una tarea de "escribir código rápido": es ingeniería de software profesional, mantenible a largo plazo. Optimiza siempre por arquitectura, mantenibilidad, seguridad y escalabilidad — nunca por velocidad.

JARVIS es un AI Agent. NO es un chatbot. NO es un solo LLM. Es un sistema de orquestación compuesto por módulos independientes.

## Fuente de verdad

La arquitectura objetivo del proyecto está definida en:

- `docs/ARCHITECTURE.md` — rol, pipeline de ejecución objetivo y Definition of Done.
- `docs/TARGET_ARCHITECTURE.md` — árbol de carpetas objetivo y responsabilidades por dominio.
- `docs/ARCHITECTURE_GAP_ANALYSIS.md` — estado actual del código, deuda técnica y brechas detectadas.
- `docs/MIGRATION_PLAN.md` — plan incremental de migración (qué mantener, mover, dividir, crear y eliminar).

Si el código difiere de esos documentos, el código debe evolucionar para ajustarse a ellos — no al revés. No modifiques esos documentos salvo que sea estrictamente necesario, y si lo haces, hazlo de forma consistente entre los cuatro.

## Antes de escribir código

1. Lee los cuatro documentos de `docs/` mencionados arriba.
2. Inspecciona el repositorio real (`backend/core.py`, `backend/skills/`, `backend/speech/`, `backend/nlu/`, `backend/api/`, `frontend/`, etc.).
3. Verifica el estado de la migración contra `docs/MIGRATION_PLAN.md` (qué pasos ya están marcados como completados con ✅ y cuáles siguen pendientes).
4. No dupliques lo que ya existe en `backend/src/` (composition root, brain, security, etc. según el plan) — continúa desde donde quedó, no reinicies la arquitectura paralela.

## Regla arquitectónica principal

Debe existir **una sola arquitectura**, sin implementaciones paralelas ni duplicadas. El pipeline de ejecución final es:

```
User → Interface → JarvisRuntime → Core → BrainManager → MemoryManager
→ Planner → Skills → Security Validation → Execution → Audit Logger → Response
```

Cada interacción debe pasar por este pipeline completo, sin atajos. Esto corresponde al árbol de `docs/TARGET_ARCHITECTURE.md`:

- **JarvisRuntime** ≈ `backend/src/app/runtime.py` (composition root; ensambla servicios sin lógica de negocio).
- **Core** ≈ `backend/src/core/` (domain kernel; orquestador, nunca contiene lógica específica de un proveedor de IA).
- **BrainManager** ≈ `backend/src/brain/` (selecciona el modelo de IA correcto; proveedores intercambiables sin tocar el Core).
- **MemoryManager** ≈ `backend/src/memory/` (Short/Long/Knowledge/System Memory; secretos nunca en texto plano).
- **Planner**: convierte objetivos del usuario en planes ejecutables. Nunca ejecuta acciones, solo las planea.
- **Skills** ≈ `backend/src/skills/`: todo lo ejecutable es una Skill, con interfaz común, bajo acoplamiento. Nunca se comunican entre sí directamente; todo pasa por el Core.
- **SecurityManager / Audit** ≈ `backend/src/security/`: autorización, niveles de permiso, confirmación de acciones peligrosas, auditoría estructurada, sandbox cuando aplica. Nunca se ejecuta código desconocido automáticamente.
- **Heartbeat** ≈ `backend/src/heartbeat/`: schedulers, triggers, background jobs, mantenimiento, monitoreo de salud. Nunca contiene lógica de negocio.
- **Interfaces** ≈ `backend/src/interfaces/` (Console, Discord, Telegram, futuras Voice/Web/Mobile): solo adaptadores. Nunca contienen lógica de negocio.

## Reglas de migración

Sigue `docs/MIGRATION_PLAN.md` como guía operativa. En particular:

- No elimines nada de `backend/core.py`, `backend/skills/*`, `backend/speech/*`, `backend/nlu/*`, `backend/api/server.py` ni `backend/test_phase*.py` hasta que el plan indique explícitamente que ya fueron migrados y reemplazados.
- Toda funcionalidad nueva o migrada va a `backend/src/` según el árbol de `docs/TARGET_ARCHITECTURE.md`.
- Cuando una responsabilidad de `core.py` quede completamente migrada a `src/`, elimina el código duplicado en `core.py` y actualízalo para actuar como fachada (o retíralo, según indique el plan en ese momento).

Después de cada paso completado:

1. Ejecuta las pruebas existentes (incluyendo `backend/test_phase*.py`).
2. Corrige imports rotos.
3. Elimina código obsoleto que ya haya sido migrado.
4. Actualiza `docs/MIGRATION_PLAN.md` marcando el paso como completado (✅) y `docs/ARCHITECTURE_GAP_ANALYSIS.md` si el gap ya se cerró.
5. Verifica que la aplicación siga funcionando (nunca rompas funcionalidad existente).

## Definition of Done

El trabajo NO está completo hasta que todo esto sea cierto:

- Existe exactamente una arquitectura (la de `backend/src/`, sin lógica de negocio duplicada en `core.py`).
- JarvisRuntime es el único composition root.
- Toda request pasa por JarvisRuntime.
- El Core orquesta todo, sin lógica específica de proveedor.
- Planner crea planes; Skills ejecutan acciones.
- BrainManager selecciona proveedores de IA de forma intercambiable.
- MemoryManager gestiona toda la memoria (short/long/knowledge/system), sin secretos en texto plano.
- SecurityManager valida cada acción, con niveles de permiso y auditoría.
- AuditLogger registra cada evento importante en un servicio centralizado.
- Heartbeat gestiona toda la ejecución en segundo plano.
- Las interfaces (Console/Discord/Telegram/futuras) son solo adaptadores.
- La arquitectura legacy concentrada en `core.py` fue completamente eliminada o reducida a fachada, sin implementaciones duplicadas.
- Todos los imports están limpios y todas las pruebas (`test_phase*.py` y nuevas) pasan.
- `docs/ARCHITECTURE.md`, `docs/TARGET_ARCHITECTURE.md`, `docs/MIGRATION_PLAN.md` y `docs/ARCHITECTURE_GAP_ANALYSIS.md` coinciden con la implementación real.

No te detengas después de crear carpetas o clases vacías. Continúa hasta que la aplicación en ejecución siga la arquitectura objetivo por completo.

## Informe de fin de tarea (obligatorio)

Al terminar cualquier tarea, **no respondas solo "listo" o "terminado"**. Responde siempre con un informe de ingeniería que incluya:

1. Qué implementaste.
2. Qué falta por implementar.
3. Qué deuda técnica quedó.
4. Qué archivos modificaste.
5. Qué archivos eliminaste.
6. Qué pruebas ejecutaste.
7. Qué porcentaje de la arquitectura objetivo (según `docs/TARGET_ARCHITECTURE.md` y el checklist de `docs/MIGRATION_PLAN.md`) está implementado.
8. Cuál es la siguiente tarea recomendada.

No des el proyecto por terminado hasta que este informe confirme que se cumplen todos los puntos del Definition of Done.
