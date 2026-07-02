# JARVIS — Fase 3/4: Comparación y plan de migración incremental

## ✅ Mantener
- `backend/core.py` (temporalmente como núcleo operativo).
- `backend/skills/*`, `backend/speech/*`, `backend/nlu/*`, `backend/api/server.py`.
- `backend/test_phase*.py` (cobertura histórica por hitos).

## 📦 Mover (gradual)
- Responsabilidades de orquestación de `core.py` hacia `src/app`, `src/brain`, `src/security`, `src/heartbeat`.

## ✏️ Renombrar (futuro)
- Unificar nomenclatura en inglés por dominio para módulos nuevos.

## ✂️ Dividir (futuro)
- `core.py` en componentes de composición, routing, status, telemetry y bridges.

## 🆕 Crear
- `backend/src/brain/*`
- `backend/src/security/*`
- `backend/src/interfaces/*`
- `backend/src/heartbeat/*`
- `backend/src/app/runtime.py`
- Documentación de análisis/arquitectura/migración en `docs/`.

## 🗑️ Eliminar (aún no)
- No se elimina nada en esta iteración para evitar pérdida de información o regresiones.

---

## Plan incremental

1. Crear arquitectura paralela (`backend/src`) sin romper imports actuales. ✅
2. Introducir `JarvisRuntime` como composition root con bridge al core actual. ✅
3. Centralizar autorización y auditoría en servicios dedicados. ✅ (fundación)
4. Introducir `BrainManager` con proveedores reemplazables. ✅ (fundación)
5. Migrar gradualmente endpoints/canales a `JarvisRuntime` en siguientes iteraciones.
6. Mover memoria y skills a contratos de puertos/adaptadores por dominio.
7. Desacoplar definitivamente `core.py` y mantenerlo como fachada o retirarlo.

