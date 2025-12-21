# Propuesta: Arquitectura Claude + Vanna (2-Stage SQL Generation)

## Problema Actual

1. **Vanna usa siempre candlestick_5min** incluso para consultas diarias/semanales/horarias
2. **No hay contexto conversacional**: "de ese día" no funciona porque Vanna no sabe qué día
3. **Consultas ambiguas fallan**: Vanna no pide aclaraciones, simplemente falla

## Solución: 2-Stage Architecture

### Stage 1: Claude Orchestrator (Context & Intelligence)

**Ubicación**: `backend/app/assistant/services/orchestrator.py`

**Responsabilidades**:
1. **Context Resolution**: Extraer entidades de mensajes previos
2. **Table Selection**: Decidir qué tabla candlestick usar
3. **Query Enhancement**: Agregar hints y contexto completo
4. **Validation**: Validar fechas, años, parámetros

**Input**:
```python
{
  "user_message": "de ese dia que hora tuvo mas volumen",
  "conversation_history": [
    {"role": "user", "content": "dame el dia con mas volumen de noviembre 2025"},
    {"role": "assistant", "content": "El día fue 2025-11-20 con volumen 969348.0",
     "metadata": {"sql": "SELECT DATE...", "date_result": "2025-11-20"}}
  ]
}
```

**Output**:
```python
{
  "enhanced_question": "use candlestick_1hr: dame las 3 horas con más volumen del día 2025-11-20",
  "table_hint": "candlestick_1hr",
  "extracted_entities": {
    "date": "2025-11-20",
    "metric": "volume",
    "aggregation": "top 3"
  },
  "needs_clarification": False
}
```

### Stage 2: Vanna SQL Generator (SQL Expertise)

**Ubicación**: `backend/app/assistant/tools/vanna_sql.py`

**Responsabilidades**:
1. **SQL Generation**: Generar SQL basado en enhanced_question
2. **Tool Memory**: Buscar queries similares exitosas
3. **SQL Validation**: Validar sintaxis y seguridad
4. **Execution**: Ejecutar contra PostgreSQL

**Input**: Enhanced question con hints
**Output**: SQL + Results

## Implementación Detallada

### 1. Modificar `orchestrator.py`

```python
class AssistantOrchestrator:
    def __init__(self):
        self.claude = get_claude_client()
        self.memory = get_gemini_memory_client()
        self.vanna = get_vanna_client()

    def process_message(self, user_message: str, user_id: str, db: Session,
                       conversation_history: Optional[list] = None) -> Dict[str, Any]:

        # Step 1: Classify intent
        intent = self.claude.classify_intent(user_message)

        if intent == "SQL_QUERY":
            # NEW: Enhance query with Claude before Vanna
            enhancement = self._enhance_sql_query(user_message, conversation_history)

            if enhancement["needs_clarification"]:
                return {
                    "content": enhancement["clarification_question"],
                    "metadata": {"needs_clarification": True},
                    "tool_used": "claude_clarification"
                }

            # Call Vanna with enhanced question
            response = self._handle_sql_query(
                question=enhancement["enhanced_question"],
                memory_context="",
                db=db,
                table_hint=enhancement.get("table_hint")
            )
            return response

        # ... resto del código

    def _enhance_sql_query(self, user_message: str,
                          conversation_history: Optional[list]) -> Dict[str, Any]:
        """
        Use Claude to:
        1. Resolve context from conversation
        2. Extract entities (dates, times, values)
        3. Select appropriate table
        4. Check if clarification needed
        """

        system_prompt = """You are a SQL query enhancer for a trading analytics system.

Your job is to:
1. Extract context from previous conversation
2. Identify which candlestick table to use:
   - candlestick_30s: ultra-fast scalping, tick analysis
   - candlestick_1min: scalping, very short-term
   - candlestick_5min: intraday trading (DEFAULT for general queries)
   - candlestick_15min: session analysis
   - candlestick_1hr: hourly trends
   - candlestick_4hr: swing trading
   - candlestick_daily: day-to-day comparisons
   - candlestick_weekly: long-term trends
3. Resolve references like "ese día", "esa hora", "el mismo mes"
4. Check if question is ambiguous and needs clarification

Return JSON:
{
  "enhanced_question": "complete standalone question with table hint",
  "table_hint": "candlestick_xxx",
  "extracted_entities": {"date": "...", "metric": "..."},
  "needs_clarification": false,
  "clarification_question": null
}

Examples:

Input: "de ese dia que hora tuvo mas volumen"
Context: Previous answer mentioned 2025-11-20
Output:
{
  "enhanced_question": "use candlestick_1hr: dame las 3 horas con más volumen del día 2025-11-20",
  "table_hint": "candlestick_1hr",
  "extracted_entities": {"date": "2025-11-20", "metric": "volume"},
  "needs_clarification": false
}

Input: "cual fue el volumen promedio"
Context: None
Output:
{
  "enhanced_question": null,
  "table_hint": null,
  "needs_clarification": true,
  "clarification_question": "¿De qué período quieres el promedio? (día, semana, mes, hora)"
}
"""

        # Build messages with conversation context
        messages = []
        if conversation_history:
            # Include last 3 exchanges for context
            messages.extend(conversation_history[-6:])

        messages.append({
            "role": "user",
            "content": f"Enhance this SQL query: {user_message}"
        })

        response = self.claude.chat(messages=messages, system=system_prompt)

        # Parse JSON response
        import json
        enhancement = json.loads(response["content"])

        return enhancement
```

### 2. Modificar `vanna_sql.py` para aceptar table_hint

```python
def ask(
    self,
    question: str = None,
    table_hint: Optional[str] = None,  # NEW parameter
    auto_train: bool = True,
    **kwargs
) -> Dict[str, Any]:
    """
    Generate and execute SQL from natural language question

    Args:
        question: Natural language query
        table_hint: Optional hint about which table to use (e.g., "candlestick_daily")
        auto_train: Whether to train on DDL/docs
    """

    try:
        # If table_hint provided, prepend to question
        if table_hint:
            question = f"use {table_hint}: {question}"

        # Rest of implementation...
```

### 3. Actualizar DDL para entender hints

```sql
-- En el DDL, agregar guía para hints

-- USAGE HINTS:
-- If the user question contains "use candlestick_XXX:",
-- you MUST use that specific table in your SQL query.
-- Example:
--   Question: "use candlestick_daily: dame el máximo de noviembre"
--   SQL: SELECT MAX(high) FROM candlestick_daily WHERE...
```

## Ventajas de esta Arquitectura

### ✅ Separación de Responsabilidades
- **Claude**: Inteligencia conversacional, contexto, decisiones
- **Vanna**: Expertise SQL, optimización de queries, ejecución

### ✅ Mejor UX
- Maneja follow-up questions: "de ese día", "y la hora?"
- Pide aclaraciones cuando es necesario
- Selecciona tabla correcta automáticamente

### ✅ Mantenible
- Cambios de lógica de negocio → Claude prompts
- Cambios de SQL patterns → Vanna training
- Cada componente hace lo que mejor sabe hacer

### ✅ Extensible
- Fácil agregar validaciones en Claude layer
- Fácil agregar nuevas tablas (solo actualizar prompt de Claude)
- Puede agregar MCP tools en el futuro para otras fuentes de datos

## Plan de Implementación

### Fase 1: MVP (2-3 horas)
1. ✅ Agregar `_enhance_sql_query()` en orchestrator
2. ✅ Modificar `vanna_sql.ask()` para aceptar `table_hint`
3. ✅ Actualizar DDL con guía de hints
4. ✅ Restart backend y probar

### Fase 2: Refinamiento (1-2 horas)
1. ✅ Mejorar prompts de Claude para table selection
2. ✅ Agregar entity extraction más robusta
3. ✅ Agregar validación de fechas (año 2025 válido)
4. ✅ Tests de conversaciones multi-turno

### Fase 3: Optimización (opcional)
1. ⭕ Cache de enhancements para queries similares
2. ⭕ Metrics de calidad (% de queries exitosas)
3. ⭕ Feedback loop (guardar corrections)

## Alternativa: MCP Tool para SQL Generation

Si en el futuro necesitas más flexibilidad, podríamos crear un **MCP Server** dedicado:

```python
# backend/app/assistant/mcp/sql_generator.py

class SqlGeneratorMCP:
    """MCP server que expone tool para SQL generation con contexto"""

    @tool
    def generate_sql_with_context(
        question: str,
        conversation_history: List[Dict],
        available_tables: List[str]
    ) -> Dict[str, Any]:
        """
        Generate SQL with full conversational context

        This tool:
        1. Resolves references from previous messages
        2. Selects optimal table
        3. Generates SQL
        4. Validates syntax
        """
        pass
```

Esto permitiría que **cualquier LLM** (no solo Claude) pueda usar el SQL generator como tool.

## Próximos Pasos

1. **Aprobar arquitectura**: ¿Te gusta este enfoque 2-stage?
2. **Implementar Fase 1**: Modificar orchestrator y vanna_sql
3. **Probar**: Correr tests de conversaciones
4. **Iterar**: Mejorar prompts basado en resultados

¿Quieres que implemente la Fase 1 ahora?
