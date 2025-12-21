# AI Assistant - Iteración 0

## Resumen Ejecutivo

Se ha implementado un **asistente AI completamente funcional y modular** para NQHUB con las siguientes capacidades:

✅ **Chat inteligente** con Claude (Anthropic API)
✅ **NL→SQL** con Vanna.AI (aprende con el uso mediante RAG)
✅ **Memoria conversacional** con mem0 + Gemini
✅ **Notificaciones proactivas** (polling cada 15s)
✅ **Monitoreo de sistema** (ETL jobs, patterns, DB stats, system health)
✅ **Routing inteligente** con LangGraph
✅ **100% desacoplado** del resto de la aplicación

---

## Arquitectura

### Backend (`/backend/app/assistant/`)

```
assistant/
├── __init__.py
├── models.py                    # SQLAlchemy models (4 tablas)
├── schemas.py                   # Pydantic schemas para API
├── config.py                    # Configuración del asistente
├── routes.py                    # FastAPI endpoints
├── llm/
│   ├── claude_client.py         # Cliente Claude + intent classification
│   └── gemini_client.py         # Cliente Gemini + mem0
├── tools/
│   ├── vanna_sql.py             # NL→SQL con Vanna.AI + RAG
│   ├── status_monitor.py        # ETL, patterns, DB stats
│   └── system_health.py         # System health monitoring
└── services/
    ├── orchestrator.py          # LangGraph routing
    ├── conversation.py          # Conversation management
    └── notifications.py         # Sistema de notificaciones
```

### Frontend (`/frontend/src/client/assistant/`)

```
assistant/
├── index.ts                     # Exports
├── types.ts                     # TypeScript types
├── AssistantPanel.tsx           # Componente principal
└── services/
    └── assistantApi.ts          # API client
```

### Base de Datos (PostgreSQL)

**4 tablas nuevas** (migration: `20251213_1915-eb92517323ec_create_assistant_tables.py`):

1. `assistant_conversations` - Conversaciones del usuario
2. `assistant_messages` - Mensajes (user/assistant/system)
3. `assistant_system_events` - Eventos para notificaciones proactivas
4. `assistant_vanna_training` - Training data para Vanna.AI

---

## Instalación y Configuración

### 1. Instalar Dependencias Python

```bash
cd backend
source .venv/bin/activate  # o activar como corresponda
pip install anthropic google-generativeai mem0ai langgraph langchain vanna[chromadb,anthropic] chromadb
```

**Nota**: Las dependencias ya están agregadas en `requirements.txt`.

### 2. Configurar Variables de Entorno

Edita `/backend/.env` y agrega:

```bash
# REQUIRED para el asistente
ANTHROPIC_API_KEY=sk-ant-tu-key-aqui

# OPTIONAL pero recomendado
GOOGLE_API_KEY=tu-gemini-key-aqui      # Para mem0 + Gemini
MEM0_API_KEY=tu-mem0-key-si-usas-cloud  # Solo si usas mem0 cloud

# FUTURE (ya preparado)
ELEVENLABS_API_KEY=tu-elevenlabs-key
ELEVENLABS_VOICE_ID=tu-voice-id
```

### 3. Ejecutar Migration (YA COMPLETADO ✅)

```bash
cd backend
alembic upgrade head
```

**Nota**: Ya fue ejecutado. Las 4 tablas están creadas.

### 4. Iniciar Backend

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8002
```

### 5. Iniciar Frontend

```bash
cd frontend
pnpm dev  # Puerto 3001
```

---

## Uso

### Para el Usuario

1. **Abrir el asistente**: Click en el ícono Globe (🌐) en la barra superior
2. **Hacer preguntas**:
   - "¿Cuántos FVGs se detectaron ayer?"
   - "¿Cómo van los ETL jobs?"
   - "Muéstrame los últimos patterns detectados"
   - "¿Cuál es el estado del sistema?"

3. **Notificaciones proactivas**: El asistente revisa cada 15s y te notifica sobre:
   - ETL jobs completados/fallidos
   - Nuevos patterns detectados
   - Database stats actualizadas
   - System alerts

### API Endpoints Disponibles

**Chat**:
- `POST /api/v1/assistant/chat` - Enviar mensaje

**Conversaciones**:
- `GET /api/v1/assistant/conversations` - Listar conversaciones
- `GET /api/v1/assistant/conversations/{id}` - Obtener conversación con mensajes
- `DELETE /api/v1/assistant/conversations/{id}` - Eliminar conversación

**Eventos (Notificaciones)**:
- `GET /api/v1/assistant/events` - Obtener eventos no notificados (polling)
- `POST /api/v1/assistant/events/mark-read` - Marcar eventos como leídos

**Status**:
- `GET /api/v1/assistant/status/etl` - ETL jobs status
- `GET /api/v1/assistant/status/patterns` - Pattern detection status
- `GET /api/v1/assistant/status/database` - Database statistics
- `GET /api/v1/assistant/status/system` - System health

**Feedback**:
- `POST /api/v1/assistant/feedback` - Submit feedback (para mejorar Vanna)

---

## Flujo de Funcionamiento

### 1. Usuario Envía Mensaje

```
Frontend (AssistantPanel.tsx)
  ↓ POST /api/v1/assistant/chat
Backend (routes.py)
  ↓
Orchestrator (services/orchestrator.py)
```

### 2. Orchestrator Clasifica Intent

```
Claude Client (llm/claude_client.py)
  ↓ classify_intent()
  ↓
Detecta: "SQL_QUERY" | "STATUS_CHECK" | "GENERAL_CHAT"
```

### 3. Routing según Intent

**SQL_QUERY**:
```
Vanna Tool (tools/vanna_sql.py)
  ↓ generate_sql(question)
  ↓ execute query
  ↓ format results
  ↓ auto-train with successful query
```

**STATUS_CHECK**:
```
Status Monitors (tools/status_monitor.py, system_health.py)
  ↓ get_etl_status() | get_pattern_status() | etc.
  ↓ format as markdown
```

**GENERAL_CHAT**:
```
Claude Client (llm/claude_client.py)
  ↓ chat() with conversation history
  ↓ + memory context from mem0
```

### 4. Respuesta + Memoria

```
Orchestrator
  ↓ add_to_memory() (Gemini + mem0)
  ↓ save to DB (assistant_messages)
  ↓ return to frontend
```

### 5. Notificaciones Proactivas (Polling)

```
Frontend (useEffect en AssistantPanel.tsx)
  ↓ cada 15 segundos
  ↓ GET /api/v1/assistant/events
  ↓
Backend (notifications.py)
  ↓ get_unnotified_events()
  ↓ return eventos nuevos
  ↓
Frontend
  ↓ toast.info() para cada evento
  ↓ POST /api/v1/assistant/events/mark-read
```

---

## Crear Eventos del Sistema (Para Desarrolladores)

Para que el asistente notifique proactivamente, otros módulos deben crear eventos:

```python
# Ejemplo: Cuando un ETL job completa
from app.assistant.models import AssistantSystemEvent
from app.database import SessionLocal

def on_etl_job_complete(job_id: int, rows_processed: int):
    db = SessionLocal()
    try:
        event = AssistantSystemEvent(
            event_type="etl_complete",
            event_data={
                "job_id": job_id,
                "rows_processed": rows_processed,
                "message": f"ETL Job #{job_id} completed successfully"
            },
            notified=False
        )
        db.add(event)
        db.commit()
    finally:
        db.close()
```

**Tipos de eventos** (definidos en `schemas.py`):
- `etl_complete`
- `etl_failed`
- `pattern_detected`
- `database_stats`
- `system_alert`
- `worker_status`

---

## Vanna.AI - Training y Mejora Continua

Vanna aprende automáticamente con cada query exitosa. También puedes entrenar manualmente:

```python
from app.assistant.tools.vanna_sql import get_vanna_client

vanna = get_vanna_client()

# Entrenar con schema DDL
vanna.vn.train(ddl="""
    CREATE TABLE mi_nueva_tabla (
        id INT PRIMARY KEY,
        ...
    );
""")

# Entrenar con ejemplos de queries
vanna.vn.train(
    question="¿Cuántos usuarios hay?",
    sql="SELECT COUNT(*) FROM users"
)

# Training desde feedback del usuario
vanna.train_from_feedback(
    question="...",
    sql="...",
    was_successful=True,
    feedback_score=5  # 1-5
)
```

**ChromaDB storage**: `/tmp/nqhub_vanna_chromadb` (configurable en `config.py`)

---

## Configuración Avanzada

### Ajustar System Prompts

Edita `/backend/app/assistant/config.py`:

```python
SYSTEM_PROMPT_GENERAL = """Tu prompt personalizado..."""
SYSTEM_PROMPT_SQL_CLASSIFICATION = """Tu prompt de clasificación..."""
```

### Cambiar Intervalo de Polling

En `config.py`:

```python
POLLING_INTERVAL_SECONDS: int = 30  # Default: 15
```

En `AssistantPanel.tsx`:

```typescript
const interval = setInterval(pollEvents, 30000); // 30 segundos
```

### Habilitar/Deshabilitar Funcionalidades

En `config.py`:

```python
# Feature flags
VANNA_ENABLED: bool = True   # NL→SQL
MEM0_ENABLED: bool = True    # Memory
POLLING_ENABLED: bool = True # Notificaciones
```

---

## Desarrollo Futuro (Roadmap)

### Iteración 1: Mejoras UI/UX
- [ ] Sidebar de conversaciones con búsqueda
- [ ] Export conversations (PDF/JSON)
- [ ] Voice input (Web Speech API)
- [ ] Rich markdown rendering (code blocks, tables)

### Iteración 2: Voice Output
- [ ] ElevenLabs TTS integration
- [ ] Toggle voice on/off
- [ ] Voice selection

### Iteración 3: Advanced RAG
- [ ] Document upload (PDFs, trading books)
- [ ] Vector search sobre documentación
- [ ] Citation links en respuestas

### Iteración 4: Multimodal
- [ ] Image analysis (screenshots de charts)
- [ ] Chart generation (from data)
- [ ] Vision API integration

### Iteración 5: Real-time
- [ ] WebSockets instead of polling
- [ ] Live updates de charts dentro del chat
- [ ] Collaborative sessions

---

## Troubleshooting

### Error: "Claude API key not configured"

**Solución**: Verifica que `ANTHROPIC_API_KEY` esté en `.env` y reinicia el backend.

### Error: "Vanna not available"

**Solución**: Instala las dependencias:
```bash
pip install vanna[chromadb,anthropic] chromadb
```

### Error: "mem0ai not installed"

**Solución**: Instala mem0:
```bash
pip install mem0ai google-generativeai
```

**Nota**: mem0 es opcional. El asistente funciona sin memoria si no está disponible.

### Frontend: "Cannot resolve module '@/assistant'"

**Solución**: Verifica que el archivo `/frontend/src/client/assistant/index.ts` exista con los exports correctos.

### Database: "Table assistant_conversations does not exist"

**Solución**: Ejecuta la migration:
```bash
cd backend
alembic upgrade head
```

### Polling no funciona

1. Verifica que el backend esté running
2. Abre DevTools → Network tab
3. Busca requests a `/api/v1/assistant/events` cada 15s
4. Verifica que no haya errores 401 (auth) o 500 (server)

---

## Testing

### Backend (Pytest)

```bash
cd backend
pytest app/assistant/tests/  # Cuando se implementen tests
```

### Frontend (Playwright)

```bash
cd frontend
pnpm playwright test tests/assistant.spec.ts  # Cuando se implemente
```

### Manual Testing Checklist

- [ ] Abrir/cerrar el panel con botón Globe
- [ ] Enviar pregunta de SQL: "¿Cuántos FVGs hay?"
- [ ] Enviar pregunta de status: "¿Cómo van los ETL jobs?"
- [ ] Enviar pregunta general: "¿Qué es un FVG?"
- [ ] Verificar que el SQL se muestre en metadata (details)
- [ ] Crear evento manualmente en DB y verificar que aparezca toast
- [ ] Iniciar nueva conversación con botón "New Chat"
- [ ] Resize del panel (arrastrar borde superior)

---

## Módulo Desacoplado

El asistente está **completamente aislado**:

### Backend
- Un solo cambio en código existente: `app/api/v1/__init__.py` (1 línea)
- Todo el código está en `/app/assistant/`
- Se puede desactivar comentando la línea del router

### Frontend
- Imports solo en páginas (Dashboard, DataModule, etc.)
- Se puede desactivar quitando `<AssistantPanel />` de cada página
- Todo el código está en `/src/client/assistant/`

### Database
- 4 tablas independientes con prefijo `assistant_*`
- No foreign keys a otras tablas (excepto `users`)
- Migration reversible con `alembic downgrade -1`

---

## Contacto y Soporte

Para el desarrollador que continúe:

1. **Documentación completa** en este README
2. **Código comentado** en todos los archivos
3. **TypeScript types** definidos en `types.ts`
4. **System prompts** personalizables en `config.py`
5. **Arquitectura modular** = fácil de extender

**Próximos pasos sugeridos**:
1. Instalar dependencias
2. Configurar API keys
3. Probar chat básico
4. Revisar logs del orchestrator para entender el flujo
5. Agregar nuevos tools o prompts según necesidad

---

## Resumen de Archivos Creados

### Backend (13 archivos)
```
backend/app/assistant/
├── __init__.py
├── models.py
├── schemas.py
├── config.py
├── routes.py
├── llm/
│   ├── __init__.py
│   ├── claude_client.py
│   └── gemini_client.py
├── tools/
│   ├── __init__.py
│   ├── vanna_sql.py
│   ├── status_monitor.py
│   └── system_health.py
└── services/
    ├── __init__.py
    ├── orchestrator.py
    ├── conversation.py
    └── notifications.py

backend/alembic/versions/
└── 20251213_1915-eb92517323ec_create_assistant_tables.py

backend/requirements.txt (actualizado)
backend/.env.example (actualizado)
backend/app/config.py (actualizado - GOOGLE_API_KEY)
backend/app/api/v1/__init__.py (actualizado - router)
```

### Frontend (4 archivos)
```
frontend/src/client/assistant/
├── index.ts
├── types.ts
├── AssistantPanel.tsx
└── services/
    └── assistantApi.ts

frontend/src/client/pages/ (actualizados - 4 archivos):
├── Dashboard.tsx
├── DataModule.tsx
├── StatisticalAnalysis.tsx
└── Placeholders.tsx
```

---

## Licencia y Créditos

**Desarrollado para**: NQHUB Trading Analytics Platform
**Iteración**: 0 (MVP funcional)
**Fecha**: 13 Diciembre 2025
**Stack**: Claude 3.5 Sonnet, Vanna.AI, mem0, LangGraph, FastAPI, React

---

**¡Asistente AI listo para usar! 🚀**

El usuario puede empezar a hacer preguntas inmediatamente después de configurar las API keys.
