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
from app.assistant.tools.status_monitor import get_etl_status, get_pattern_status, get_database_stats
from app.assistant.tools.system_health import get_system_health

logger = logging.getLogger(__name__)


class AssistantOrchestrator:
    """Simple orchestrator for routing user queries"""

    def __init__(self):
        self.claude = get_claude_client()
        self.memory = get_gemini_memory_client()

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
                # SQL query functionality has been removed (Vanna was deprecated in v2)
                response = {
                    "content": "SQL query functionality is currently unavailable. This feature was deprecated in v2 and is being replaced with a new implementation.",
                    "metadata": {"deprecated": True, "reason": "vanna_removed"},
                    "tool_used": "deprecated_feature"
                }
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
