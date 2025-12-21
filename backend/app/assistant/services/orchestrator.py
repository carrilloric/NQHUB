"""
LangGraph orchestrator for query routing
Simple routing based on Claude's intent classification
"""
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
import logging
import json

from app.assistant.llm.claude_client import get_claude_client
from app.assistant.llm.gemini_client import get_gemini_memory_client
from app.assistant.tools.vanna_sql import get_vanna_client
from app.assistant.tools.status_monitor import get_etl_status, get_pattern_status, get_database_stats
from app.assistant.tools.system_health import get_system_health

logger = logging.getLogger(__name__)


class AssistantOrchestrator:
    """Simple orchestrator for routing user queries"""

    def __init__(self):
        self.claude = get_claude_client()
        self.memory = get_gemini_memory_client()
        self.vanna = get_vanna_client()

    def process_message(
        self,
        user_message: str,
        user_id: str,
        db: Session,
        conversation_history: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Process a user message and route to appropriate handler

        Args:
            user_message: User's message
            user_id: User ID for memory
            db: Database session
            conversation_history: Optional chat history

        Returns:
            Dict with 'content', 'metadata', 'tool_used'
        """
        try:
            # Step 1: Classify intent
            intent = self.claude.classify_intent(user_message)
            logger.info(f"Classified intent: {intent}")

            # Step 2: Get relevant memories for context
            memories = self.memory.get_relevant_memories(user_id, user_message, limit=3)
            memory_context = self.memory.format_memories_for_context(memories)

            # Step 3: Route based on intent
            if intent == "SQL_QUERY":
                # NEW: 2-stage approach - enhance query with Claude before Vanna
                enhancement = self._enhance_sql_query(user_message, conversation_history)

                if enhancement.get("needs_clarification"):
                    response = {
                        "content": enhancement["clarification_question"],
                        "metadata": {"needs_clarification": True},
                        "tool_used": "claude_clarification"
                    }
                else:
                    # Call Vanna with enhanced question
                    response = self._handle_sql_query(
                        question=enhancement["enhanced_question"],
                        memory_context=memory_context,
                        db=db,
                        table_hint=enhancement.get("table_hint")
                    )
            elif intent == "STATUS_CHECK":
                response = self._handle_status_check(user_message, memory_context, db)
            else:  # GENERAL_CHAT
                response = self._handle_general_chat(user_message, memory_context, conversation_history)

            # Step 4: Add to memory
            self.memory.add_to_memory(
                user_id=user_id,
                message=f"Q: {user_message}\nA: {response['content']}",
                metadata={"intent": intent, "tool_used": response.get('tool_used')}
            )

            return response

        except Exception as e:
            logger.error(f"Orchestrator error: {e}")
            return {
                "content": f"I encountered an error processing your request: {str(e)}",
                "metadata": {"error": str(e)},
                "tool_used": "error_handler"
            }

    def _enhance_sql_query(self, user_message: str, conversation_history: Optional[list]) -> Dict[str, Any]:
        """
        Use Claude to enhance query with context resolution and table selection

        Args:
            user_message: User's original query
            conversation_history: Previous conversation turns

        Returns:
            Dict with enhanced_question, table_hint, extracted_entities, needs_clarification
        """
        system_prompt = """You are a SQL query enhancer for a trading analytics system.

Your job is to:
1. Extract context from previous conversation messages
2. Identify which candlestick table to use based on temporal keywords:
   - candlestick_30s: ultra-fast scalping, tick analysis
   - candlestick_1min: scalping, very short-term
   - candlestick_5min: intraday trading (DEFAULT for general queries)
   - candlestick_15min: session analysis
   - candlestick_1hr: hourly trends
   - candlestick_4hr: swing trading
   - candlestick_daily: day-to-day comparisons, daily aggregations
   - candlestick_weekly: long-term trends, weekly analysis
3. Resolve references like "ese día", "esa hora", "el mismo mes"
4. Check if question is ambiguous and needs clarification

IMPORTANT TABLE SELECTION RULES:
- If query mentions "día", "diario", "daily", "por día" → use candlestick_daily
- If query mentions "semana", "semanal", "weekly" → use candlestick_weekly
- If query mentions "hora", "hourly", "cada hora", "por hora" → use candlestick_1hr
- If query mentions "minutos", specific minute intervals → use appropriate minute table
- For general queries without time specification → use candlestick_5min (default)

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

Input: "cual fue el volumen diario promedio de noviembre 2025"
Context: None
Output:
{
  "enhanced_question": "use candlestick_daily: cual fue el volumen diario promedio de noviembre 2025",
  "table_hint": "candlestick_daily",
  "extracted_entities": {"month": "2025-11", "metric": "volume", "aggregation": "average"},
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
            # Include last 3 exchanges for context (6 messages)
            messages.extend(conversation_history[-6:])

        messages.append({
            "role": "user",
            "content": f"Enhance this SQL query: {user_message}"
        })

        try:
            response = self.claude.chat(messages=messages, system=system_prompt)

            # Parse JSON response
            enhancement = json.loads(response["content"])
            logger.info(f"Query enhancement: {enhancement}")

            return enhancement

        except Exception as e:
            logger.error(f"Enhancement error: {e}")
            # Fallback: return original question without enhancement
            return {
                "enhanced_question": user_message,
                "table_hint": None,
                "extracted_entities": {},
                "needs_clarification": False
            }

    def _handle_sql_query(
        self,
        question: str,
        memory_context: str,
        db: Session,
        table_hint: Optional[str] = None
    ) -> Dict[str, Any]:
        """Handle SQL queries using Vanna"""
        result = self.vanna.ask(question, table_hint=table_hint, auto_train=True)

        if result["success"]:
            rows = result["results"]
            count = len(rows)

            # Format response with SQL query displayed first
            sql_display = f"**Generated SQL Query:**\n```sql\n{result['sql']}\n```\n\n---\n\n"

            # Format results
            if count == 0:
                answer = sql_display + "**No results found for your query.**"
            elif count == 1 and len(rows[0]) == 1:
                # Single value result
                value = list(rows[0].values())[0]
                answer = sql_display + f"**Result:** {value}"
            else:
                # Multiple rows/columns - create markdown table
                answer = sql_display + f"**Found {count} results:**\n\n"
                if count <= 10:
                    # Show all results as table
                    if rows:
                        headers = list(rows[0].keys())
                        answer += "| " + " | ".join(headers) + " |\n"
                        answer += "|" + "|".join(["---" for _ in headers]) + "|\n"
                        for row in rows:
                            answer += "| " + " | ".join(str(v) for v in row.values()) + " |\n"
                else:
                    answer += f"(Showing first 10 of {count} results)\n\n"
                    headers = list(rows[0].keys())
                    answer += "| " + " | ".join(headers) + " |\n"
                    answer += "|" + "|".join(["---" for _ in headers]) + "|\n"
                    for row in rows[:10]:
                        answer += "| " + " | ".join(str(v) for v in row.values()) + " |\n"

            return {
                "content": answer,
                "metadata": {"sql": result["sql"], "row_count": count},
                "tool_used": "vanna_sql"
            }
        else:
            # Show SQL even on error
            sql_display = ""
            if result.get("sql"):
                sql_display = f"**Generated SQL Query:**\n```sql\n{result['sql']}\n```\n\n---\n\n"

            return {
                "content": sql_display + f"**Error executing query:** {result['error']}",
                "metadata": {"error": result["error"], "sql": result.get("sql")},
                "tool_used": "vanna_sql_error"
            }

    def _handle_status_check(self, question: str, memory_context: str, db: Session) -> Dict[str, Any]:
        """Handle status check queries"""
        # Determine which status to check based on keywords
        q_lower = question.lower()

        if any(word in q_lower for word in ["etl", "job", "pipeline", "ingest"]):
            status = get_etl_status(db)
            summary = f"**ETL Status:**\n- Total jobs: {status['total_jobs']}\n- Running: {status['running']}\n- Completed: {status['completed']}\n- Failed: {status['failed']}"
            metadata = {"status_type": "etl", "data": status}

        elif any(word in q_lower for word in ["pattern", "fvg", "liquidity", "order block"]):
            status = get_pattern_status(db)
            summary = f"**Pattern Detection Status:**\n- Total FVGs: {status['total_fvgs']}\n- Total Liquidity Pools: {status['total_lps']}\n- Total Order Blocks: {status['total_obs']}\n- Recent detections: {len(status['recent_detections'])}"
            metadata = {"status_type": "patterns", "data": status}

        elif any(word in q_lower for word in ["database", "data", "candle", "tick"]):
            status = get_database_stats(db)
            summary = f"**Database Statistics:**\n- Total candles: {status['total_candles']:,}\n- Total ticks: {status['total_ticks']:,}\n- Active contracts: {status['active_contracts']}"
            metadata = {"status_type": "database", "data": status}

        elif any(word in q_lower for word in ["system", "health", "worker", "memory", "cpu"]):
            status = get_system_health()
            summary = f"**System Health:**\n- API Status: {status['api_status']}\n- Workers: {status['workers_active']}/{status['workers_total']}\n- Memory: {status.get('memory_usage', {}).get('percent', 'N/A')}%\n- CPU: {status.get('cpu_percent', 'N/A')}%"
            metadata = {"status_type": "system", "data": status}

        else:
            # Default: show all statuses
            etl = get_etl_status(db)
            patterns = get_pattern_status(db)
            db_stats = get_database_stats(db)
            system = get_system_health()

            summary = f"""**System Overview:**

**ETL:** {etl['running']} running, {etl['completed']} completed, {etl['failed']} failed
**Patterns:** {patterns['total_fvgs']} FVGs, {patterns['total_lps']} LPs, {patterns['total_obs']} OBs
**Database:** {db_stats['total_candles']:,} candles, {db_stats['total_ticks']:,} ticks
**System:** {system['workers_active']}/{system['workers_total']} workers, {system.get('memory_usage', {}).get('percent', 'N/A')}% memory"""

            metadata = {
                "status_type": "overview",
                "data": {"etl": etl, "patterns": patterns, "database": db_stats, "system": system}
            }

        return {
            "content": summary,
            "metadata": metadata,
            "tool_used": "status_monitor"
        }

    def _handle_general_chat(
        self,
        message: str,
        memory_context: str,
        conversation_history: Optional[list] = None
    ) -> Dict[str, Any]:
        """Handle general chat using Claude"""
        # Build messages
        messages = conversation_history or []
        messages.append({"role": "user", "content": message})

        # Add memory context to system prompt if available
        system_prompt = ""
        if self.claude.client:
            system_prompt = getattr(self.claude.client, 'system', '') or ""
        if memory_context:
            system_prompt = f"{system_prompt}\n\n{memory_context}"

        response = self.claude.chat(messages=messages, system=system_prompt)

        return {
            "content": response["content"],
            "metadata": {"usage": response["usage"]},
            "tool_used": "claude_chat"
        }


# Singleton
_orchestrator: Optional[AssistantOrchestrator] = None


def get_orchestrator() -> AssistantOrchestrator:
    """Get or create orchestrator singleton"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AssistantOrchestrator()
    return _orchestrator
