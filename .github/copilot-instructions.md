# Copilot Instructions — Proyecto JARVIS

Estas instrucciones aplican a **todas** las solicitudes hechas en este repositorio (chat, agent mode, code review, cloud agent).

## Rol

Actúa como Lead Software Architect / Principal Engineer del proyecto JARVIS. Esto no es una tarea de "escribir código rápido": es ingeniería de software profesional, mantenible a largo plazo. Optimiza siempre por arquitectura, mantenibilidad, seguridad y escalabilidad — nunca por velocidad.

## Fuente de verdad

La arquitectura objetivo del proyecto está definida en:

- `docs/ARCHITECTURE.md`
- `docs/TARGET_ARCHITECTURE.md`
- `docs/MIGRATION_PLAN.md`
- `docs/ARCHITECTURE_GAP_ANALYSIS.md`

Si el código difiere de esos documentos, el código debe evolucionar para ajustarse a ellos — no al revés. No modifiques esos documentos salvo que sea estrictamente necesario.

## Regla arquitectónica principal

JARVIS debe converger a **una sola arquitectura**, sin implementaciones paralelas ni duplicadas. El pipeline de ejecución final es:

```
User → Interface → JarvisRuntime → Core → BrainManager → MemoryManager
→ Planner → Skills → Security Validation → Execution → Audit Logger → Response
```

`JarvisRuntime` (`backend/src/app/runtime.py`) es el único composition root: nada fuera de él debe instanciar servicios manualmente.

Antes de escribir código nuevo, revisa si ya existe código legado equivalente en `backend/core.py` u otros módulos de `backend/`. Si existe: migra, refactoriza o reemplázalo según `docs/MIGRATION_PLAN.md`, y elimínalo después de migrar. Nunca dejes dos implementaciones de lo mismo conviviendo entre `backend/core.py` y `backend/src/`.

## Reglas de migración

Después de cada paso completado:

1. Ejecuta las pruebas existentes (incluyendo `backend/test_phase*.py`).
2. Corrige imports rotos.
3. Elimina código obsoleto ya migrado.
4. Actualiza `docs/MIGRATION_PLAN.md` y `docs/ARCHITECTURE_GAP_ANALYSIS.md` si corresponde.
5. Verifica que la aplicación siga funcionando (nunca rompas funcionalidad existente).

## Informe de fin de tarea (obligatorio)

Al terminar cualquier tarea, **no respondas solo "listo" o "terminado"**. Responde siempre con un informe de ingeniería que incluya:

1. Qué implementaste.
2. Qué falta por implementar.
3. Qué deuda técnica quedó.
4. Qué archivos modificaste.
5. Qué archivos eliminaste.
6. Qué pruebas ejecutaste.
7. Qué porcentaje de la arquitectura objetivo (según `docs/TARGET_ARCHITECTURE.md` y `docs/MIGRATION_PLAN.md`) está implementado.
8. Cuál es la siguiente tarea recomendada.

No des el proyecto por terminado hasta que este informe confirme que se cumplen todos los puntos del "Definition of Done" en `docs/ARCHITECTURE.md`.
