# AI Assistant - Lista de Pendientes

**Fecha**: 2025-12-13
**Estado Actual**: ✅ Funcional para testing local (sin autenticación real)

---

## 🎯 Iteración 0 - Completado ✅

### Backend
- ✅ Estructura de módulo `/app/assistant/` creada
- ✅ 4 tablas en base de datos (migration ejecutada)
  - `assistant_conversations`
  - `assistant_messages`
  - `assistant_system_events`
  - `assistant_vanna_training`
- ✅ Modelos SQLAlchemy con fix de `metadata` → `msg_metadata`
- ✅ Schemas Pydantic con alias correcto
- ✅ Rutas FastAPI funcionando (sync temporal con mock user)
- ✅ Cliente Claude con graceful degradation
- ✅ Cliente Gemini + mem0 con graceful degradation
- ✅ Vanna.AI wrapper con ChromaDB
- ✅ Status monitors (ETL, patterns, database, system)
- ✅ Orchestrator con LangGraph routing
- ✅ Servicios de conversación (CRUD básico)
- ✅ Servicios de notificaciones

### Frontend
- ✅ Módulo `/src/client/assistant/` creado
- ✅ Tipos TypeScript definidos
- ✅ API client (assistantApi.ts)
- ✅ Componente `AssistantPanel.tsx` con:
  - Chat interface
  - Polling cada 15 segundos
  - Toast notifications
  - Panel redimensionable
- ✅ Integrado en 4 páginas:
  - Dashboard
  - DataModule
  - StatisticalAnalysis
  - Placeholders

### Documentación
- ✅ `README_ASSISTANT.md` - Guía completa de instalación y uso
- ✅ `ASSISTANT_STATUS.md` - Estado actual y bugs resueltos
- ✅ `ASSISTANT_TODO.md` - Este archivo

---

## 🔴 PENDIENTES CRÍTICOS (Para Producción)

### 1. **Migrar a Autenticación Async Real** 🔐
**Prioridad**: ALTA (antes de producción)
**Tiempo estimado**: 45-60 minutos
**Estado**: ⏸️ En espera (usando mock user para testing local)

**Tareas**:
- [ ] Migrar todas las rutas de `def` → `async def`
- [ ] Cambiar `Session` → `AsyncSession` en todas las dependencias
- [ ] Migrar servicios de conversación a async:
  - [ ] `create_conversation` → `create_conversation_async`
  - [ ] `get_user_conversations` → `get_user_conversations_async`
  - [ ] `get_conversation` → `get_conversation_async`
  - [ ] `add_message` → `add_message_async`
  - [ ] `delete_conversation` → `delete_conversation_async`
- [ ] Reemplazar `get_mock_user()` con `get_current_user` real
- [ ] Eliminar `get_db_sync` dependency
- [ ] Agregar `await` a todas las llamadas de DB
- [ ] Probar con JWT tokens reales
- [ ] Verificar permisos por rol (admin, trader, etc.)

**Archivos a modificar**:
```
app/assistant/routes.py
app/assistant/services/conversation.py
app/assistant/services/notifications.py
```

**Código a eliminar**:
```python
# ELIMINAR esta función:
def get_mock_user() -> User:
    user = User()
    user.id = 1
    user.email = "test@nqhub.com"
    user.full_name = "Test User"
    return user

# ELIMINAR todos los "TODO: Use get_current_user when auth is fixed"
```

---

### 2. **Instalar Dependencias de Python** 📦
**Prioridad**: ALTA (para funcionalidad completa)
**Tiempo estimado**: 5-10 minutos
**Estado**: ⏸️ Pendiente

**Comandos**:
```bash
cd backend
source .venv/bin/activate

# Dependencias principales
pip install anthropic==0.39.0
pip install google-generativeai==0.8.3
pip install mem0ai==0.1.24
pip install langgraph==0.2.45
pip install langchain==0.3.7

# Vanna.AI con ChromaDB
pip install vanna[chromadb,anthropic]==0.8.7
pip install chromadb==0.5.18
```

**Verificación**:
```bash
python -c "import anthropic; print('✅ Anthropic OK')"
python -c "import google.generativeai; print('✅ Gemini OK')"
python -c "import mem0; print('✅ mem0 OK')"
python -c "import vanna; print('✅ Vanna OK')"
```

---

### 3. **Configurar API Keys** 🔑
**Prioridad**: ALTA (para funcionalidad completa)
**Tiempo estimado**: 5 minutos
**Estado**: ⏸️ Pendiente

**Archivo**: `/backend/.env`

```bash
# ============== AI Assistant ==============

# Claude (Anthropic) - REQUERIDO para chat
ANTHROPIC_API_KEY=sk-ant-api03-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# Gemini (Google) - OPCIONAL para memoria conversacional
GOOGLE_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# mem0 - OPCIONAL para memoria mejorada
MEM0_ENABLED=True
MEM0_API_KEY=your-mem0-key-here  # Solo si usas mem0 cloud

# Vanna.AI - OPCIONAL para NL→SQL
VANNA_ENABLED=True
VANNA_CHROMA_PATH=/tmp/nqhub_vanna_chromadb  # Path para ChromaDB local
```

**Obtener las keys**:
- **Claude**: https://console.anthropic.com/settings/keys
- **Gemini**: https://makersuite.google.com/app/apikey
- **mem0**: https://app.mem0.ai/ (opcional, puede usarse local)

**Verificar configuración**:
```bash
# Reiniciar backend después de agregar keys
pkill -f "uvicorn app.main:app"
source .venv/bin/activate
python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8002

# Probar chat
curl -X POST http://localhost:8002/api/v1/assistant/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello! Can you help me?","conversation_id":null}'
```

---

## 🟡 PENDIENTES IMPORTANTES (Mejoras)

### 4. **Hacer Orchestrator Async** ⚡
**Prioridad**: MEDIA (después de auth async)
**Tiempo estimado**: 30 minutos
**Estado**: ⏸️ Pendiente

**Problema actual**: El orchestrator procesa mensajes de forma síncrona, bloqueando el thread.

**Tareas**:
- [ ] Convertir `process_message()` → `process_message_async()`
- [ ] Hacer async los handlers:
  - [ ] `_handle_sql_query()` → async
  - [ ] `_handle_status_check()` → async (ya consultan DB sync)
  - [ ] `_handle_general_chat()` → async
- [ ] Usar `await` para llamadas a Claude, Gemini, Vanna
- [ ] Actualizar `routes.py` para usar versión async

**Beneficio**: No bloquea el servidor mientras el LLM procesa respuestas largas.

---

### 5. **Mejorar Sistema de Notificaciones Proactivas** 🔔
**Prioridad**: MEDIA
**Tiempo estimado**: 1-2 horas
**Estado**: ⏸️ Pendiente

**Estado actual**: Frontend hace polling cada 15 segundos.

**Mejoras**:
- [ ] Implementar WebSockets para notificaciones en tiempo real
- [ ] Crear background tasks para detectar eventos:
  - [ ] ETL jobs completados/fallidos
  - [ ] Nuevos patrones detectados (FVG, LP, OB)
  - [ ] Alertas de sistema (workers caídos, memoria alta)
- [ ] Agregar configuración de preferencias de notificación por usuario
- [ ] Implementar rate limiting para evitar spam

**Archivos nuevos**:
```
app/assistant/websocket.py
app/assistant/background_tasks.py
frontend/src/client/assistant/websocket.ts
```

---

### 6. **Mejorar Entrenamiento de Vanna.AI** 📚
**Prioridad**: MEDIA
**Tiempo estimado**: 2-3 horas
**Estado**: ⏸️ Pendiente

**Estado actual**: Schema DDL básico y 3 queries de ejemplo.

**Mejoras**:
- [ ] Entrenar con queries SQL comunes de usuarios reales
- [ ] Agregar documentación de tablas (comentarios, ejemplos)
- [ ] Implementar feedback loop:
  - Usuario marca query como "útil" o "no útil"
  - Auto-entrenar con queries exitosas
- [ ] Agregar más ejemplos de patrones ICT:
  ```sql
  -- FVGs no mitigados en las últimas 24h
  -- Liquidity Pools swept hoy
  -- Order Blocks de alta calidad cerca del precio actual
  ```
- [ ] Validar SQL generado antes de ejecutar (sanitización)

**Archivo**: `app/assistant/tools/vanna_sql.py`

---

### 7. **Implementar Sistema de Memoria Avanzado** 🧠
**Prioridad**: BAJA
**Tiempo estimado**: 3-4 horas
**Estado**: ⏸️ Pendiente

**Estado actual**: mem0 configurado pero no usa memoria a largo plazo.

**Mejoras**:
- [ ] Guardar preferencias de usuario:
  - Timeframes favoritos
  - Patrones que monitorea
  - Estilo de respuestas (técnico vs casual)
- [ ] Memoria contextual de trading:
  - Recordar análisis previos de un activo
  - Patrones que el usuario marcó como importantes
- [ ] Integrar con `AssistantVannaTraining` para mejorar NL→SQL
- [ ] Implementar olvido selectivo (limpiar memoria vieja)

---

### 8. **Agregar Voice (ElevenLabs)** 🎤
**Prioridad**: BAJA
**Tiempo estimado**: 4-6 horas
**Estado**: ⏸️ Pendiente (Iteración 1+)

**Planeado para futuras iteraciones**:
- [ ] Integrar ElevenLabs API
- [ ] Text-to-Speech para respuestas del asistente
- [ ] Speech-to-Text para input del usuario (opcional)
- [ ] Configurar voces y idiomas
- [ ] Control de velocidad y tono

**Requerimientos**:
```bash
pip install elevenlabs
```

**Archivo nuevo**:
```
app/assistant/tts/elevenlabs_client.py
frontend/src/client/assistant/VoiceControls.tsx
```

---

## 🟢 TAREAS DE TESTING

### 9. **Testing del Chat Endpoint** ✅
**Prioridad**: MEDIA
**Tiempo estimado**: 1 hora
**Estado**: ⏸️ Pendiente

**Tests a crear**:
```bash
# Crear: backend/tests/assistant/test_chat.py
```

**Casos de prueba**:
- [ ] Chat sin conversation_id crea nueva conversación
- [ ] Chat con conversation_id usa conversación existente
- [ ] Mensaje vacío retorna error 400
- [ ] Mensaje muy largo (>5000 chars) retorna error 400
- [ ] Usuario no autenticado retorna error 401
- [ ] Conversación de otro usuario retorna error 404
- [ ] Intent classification funciona correctamente:
  - [ ] "How many FVGs?" → SQL_QUERY
  - [ ] "What's the ETL status?" → STATUS_CHECK
  - [ ] "Hello!" → GENERAL_CHAT

**Comandos**:
```bash
cd backend
pytest tests/assistant/test_chat.py -v
```

---

### 10. **Testing E2E del Frontend** 🎭
**Prioridad**: MEDIA
**Tiempo estimado**: 2 horas
**Estado**: ⏸️ Pendiente

**Tests a crear**:
```bash
# Crear: frontend/e2e/assistant.spec.ts
```

**Casos de prueba con Playwright**:
- [ ] Abrir panel del asistente desde Dashboard
- [ ] Enviar mensaje y recibir respuesta
- [ ] Polling de notificaciones funciona cada 15s
- [ ] Toast notification aparece cuando hay evento
- [ ] Redimensionar panel funciona
- [ ] Historial de conversaciones se carga
- [ ] Cambiar entre conversaciones funciona
- [ ] SQL query muestra metadata expandible

**Comando**:
```bash
cd frontend
pnpm playwright test e2e/assistant.spec.ts
```

---

## 📋 CHECKLIST DE IMPLEMENTACIÓN COMPLETA

Use este checklist antes de considerar el asistente "production-ready":

### Backend
- [ ] ✅ Migraciones de DB ejecutadas
- [ ] ✅ Todas las dependencias instaladas
- [ ] ✅ API keys configuradas en .env
- [ ] ⏸️ Autenticación async implementada
- [ ] ⏸️ Orchestrator async
- [ ] ⏸️ Tests unitarios (>80% coverage)
- [ ] ⏸️ WebSockets para notificaciones
- [ ] ⏸️ Rate limiting implementado
- [ ] ⏸️ Logging completo
- [ ] ⏸️ Error handling robusto

### Frontend
- [ ] ✅ AssistantPanel integrado en páginas
- [ ] ✅ Polling cada 15 segundos
- [ ] ✅ Toast notifications
- [ ] ⏸️ WebSocket connection
- [ ] ⏸️ Tests E2E con Playwright
- [ ] ⏸️ Error states (sin conexión, timeout)
- [ ] ⏸️ Loading states
- [ ] ⏸️ Optimistic UI updates
- [ ] ⏸️ Markdown rendering para respuestas
- [ ] ⏸️ Code syntax highlighting

### Seguridad
- [ ] ⏸️ JWT auth en todos los endpoints
- [ ] ⏸️ Rate limiting por usuario
- [ ] ⏸️ SQL injection protection (Vanna)
- [ ] ⏸️ XSS protection en frontend
- [ ] ⏸️ CORS configurado correctamente
- [ ] ⏸️ API keys no expuestas al frontend
- [ ] ⏸️ Logs no incluyen datos sensibles

### Performance
- [ ] ⏸️ Async operations no bloquean
- [ ] ⏸️ DB queries optimizadas (índices)
- [ ] ⏸️ Caching de respuestas frecuentes
- [ ] ⏸️ Streaming de respuestas largas
- [ ] ⏸️ Paginación de conversaciones

### Documentación
- [ ] ✅ README_ASSISTANT.md completo
- [ ] ✅ ASSISTANT_STATUS.md actualizado
- [ ] ✅ ASSISTANT_TODO.md (este archivo)
- [ ] ⏸️ API docs en Swagger actualizados
- [ ] ⏸️ Diagramas de arquitectura
- [ ] ⏸️ Guía de troubleshooting

---

## 🚀 ROADMAP FUTURO (Iteración 1+)

Estas features están fuera del scope de "Iteración 0" pero están planeadas:

### Iteración 1 (Future)
- [ ] Voice input/output con ElevenLabs
- [ ] Integración MCP (Model Context Protocol) para SQL
- [ ] Múltiples modelos LLM (GPT-4, Gemini Pro, etc.)
- [ ] Fine-tuning del modelo en datos de NQHUB
- [ ] Análisis de sentimiento de mercado
- [ ] Generación de reportes automáticos

### Iteración 2 (Future)
- [ ] Multi-agente collaboration
- [ ] Backtesting automático basado en preguntas
- [ ] Alertas personalizadas por usuario
- [ ] Dashboard de métricas del asistente
- [ ] A/B testing de prompts
- [ ] Self-healing (auto-fix de errores)

---

## 📝 NOTAS DE IMPLEMENTACIÓN

### Decisiones Técnicas Tomadas

1. **Sync vs Async**: Decidido usar sync temporal para Iteración 0 (testing local)
2. **Polling vs WebSockets**: Polling de 15s para simplicidad inicial
3. **Mock User**: Temporal para desarrollo, debe reemplazarse con auth real
4. **ChromaDB Local**: Evitar dependencias cloud para Vanna
5. **Pydantic Alias**: Usar `msg_metadata` para evitar conflicto con SQLAlchemy

### Problemas Conocidos Resueltos

1. ✅ SQLAlchemy `metadata` attribute conflict
2. ✅ Pydantic serialization con ORM models
3. ✅ Import paths incorrectos
4. ✅ Claude client graceful degradation
5. ✅ Orchestrator AttributeError con client None

### Warnings Actuales (No Críticos)

```
⚠️ Vanna not installed. NL→SQL features will be disabled.
⚠️ Claude API key not configured - Claude features will be disabled
⚠️ mem0: Unsupported LLM provider: google
```

Estos son **esperados** hasta que se instalen dependencias y configuren keys.

---

## 🆘 TROUBLESHOOTING

### Backend no arranca
```bash
# Ver logs
tail -f backend/logs/app.log

# Verificar puerto
lsof -i :8002

# Reiniciar
pkill -f "uvicorn app.main:app"
python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8002
```

### Frontend no muestra el panel
```bash
# Verificar que el componente esté importado
grep -r "AssistantPanel" frontend/src/client/pages/

# Verificar estado en React DevTools
# Buscar: ui.llmPanelOpen
```

### Chat no responde
```bash
# Verificar endpoint
curl -X POST http://localhost:8002/api/v1/assistant/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"test","conversation_id":null}'

# Ver logs de backend
# Buscar errores en orchestrator
```

---

**Última Actualización**: 2025-12-13 21:00 UTC
**Próxima Revisión**: Después de instalar dependencias y configurar API keys
**Mantenedor**: Claude Code + Ricardo
