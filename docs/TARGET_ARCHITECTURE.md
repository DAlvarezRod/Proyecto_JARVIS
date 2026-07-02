# JARVIS — Fase 2: Arquitectura objetivo

## Árbol objetivo

```text
backend/
  src/
    app/            # Composition root / runtime
    core/           # Domain kernel (futuro)
    brain/          # Brain manager + providers
    memory/         # Short/Long/Knowledge/System memory
    skills/         # Skills desacopladas
    interfaces/     # Console/Mic/Discord/Telegram adapters
    heartbeat/      # Event bus + scheduler
    automation/     # Reglas, jobs, orchestrations
    security/       # Authorization, permissions, audit
    config/         # Config loaders, schema, validation
    database/       # Persistence adapters
  api/              # HTTP/WebSocket adapters (integration layer)
  tests/            # Pruebas unitarias e integración
docs/               # Arquitectura, decisiones, guías
```

## Responsabilidades por carpeta

- `src/app`: ensambla servicios y dependencias (sin lógica de negocio).
- `src/brain`: decide proveedor/modelo por tipo de tarea; proveedores reemplazables.
- `src/security`: políticas de autorización, validación y auditoría estructurada.
- `src/interfaces`: contratos comunes de entrada/salida por canal.
- `src/heartbeat`: eventos del sistema, tareas periódicas y programadas.
- `src/memory`: separación explícita de memorias (short/long/knowledge/system).
- `src/skills`: capacidades independientes con bajo acoplamiento.
- `src/automation`: workflows declarativos y ejecución segura.
- `src/config`: lectura/validación de configuración y defaults.
- `src/database`: acceso a persistencia con puertos/adaptadores.

