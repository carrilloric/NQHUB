"""
Gemini + mem0 integration for conversational memory
"""
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)

try:
    from mem0 import Memory
    MEM0_AVAILABLE = True
except ImportError:
    MEM0_AVAILABLE = False
    logger.warning("mem0ai not installed. Memory features will be disabled.")

from app.assistant.config import assistant_config


class GeminiMemoryClient:
    """Client for managing conversational memory with mem0 + Gemini"""

    def __init__(self):
        if not assistant_config.MEM0_ENABLED or not MEM0_AVAILABLE:
            logger.warning("mem0 is disabled or not available")
            self.memory = None
            return

        try:
            # Configure mem0 with Gemini
            config = {
                "llm": {
                    "provider": "google",
                    "config": {
                        "model": assistant_config.GEMINI_MODEL,
                        "temperature": 0.7,
                    }
                }
            }

            # Add API key if available
            if assistant_config.GEMINI_API_KEY:
                config["llm"]["config"]["api_key"] = assistant_config.GEMINI_API_KEY

            self.memory = Memory.from_config(config)
            logger.info("mem0 initialized successfully with Gemini")

        except Exception as e:
            logger.error(f"Failed to initialize mem0: {e}")
            self.memory = None

    def add_to_memory(
        self,
        user_id: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add a message to user's memory

        Args:
            user_id: Unique user identifier
            message: Message content to remember
            metadata: Optional metadata (conversation_id, intent, etc.)

        Returns:
            True if successful, False otherwise
        """
        if not self.memory:
            return False

        try:
            self.memory.add(
                message,
                user_id=user_id,
                metadata=metadata or {}
            )
            return True
        except Exception as e:
            logger.error(f"Failed to add to memory: {e}")
            return False

    def get_relevant_memories(
        self,
        user_id: str,
        query: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant memories for context

        Args:
            user_id: Unique user identifier
            query: Current query to find relevant context
            limit: Maximum number of memories to retrieve

        Returns:
            List of relevant memory objects
        """
        if not self.memory:
            return []

        try:
            results = self.memory.search(
                query,
                user_id=user_id,
                limit=limit
            )
            return results if results else []
        except Exception as e:
            logger.error(f"Failed to search memories: {e}")
            return []

    def get_all_memories(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all memories for a user"""
        if not self.memory:
            return []

        try:
            return self.memory.get_all(user_id=user_id)
        except Exception as e:
            logger.error(f"Failed to get all memories: {e}")
            return []

    def delete_memory(self, memory_id: str) -> bool:
        """Delete a specific memory"""
        if not self.memory:
            return False

        try:
            self.memory.delete(memory_id)
            return True
        except Exception as e:
            logger.error(f"Failed to delete memory: {e}")
            return False

    def format_memories_for_context(
        self,
        memories: List[Dict[str, Any]]
    ) -> str:
        """
        Format memories into a string for prompt context

        Args:
            memories: List of memory objects from search

        Returns:
            Formatted string for system prompt
        """
        if not memories:
            return ""

        context_lines = ["Previous context:"]
        for mem in memories:
            # mem0 typically returns: {'memory': '...', 'metadata': {...}}
            memory_text = mem.get('memory', '')
            if memory_text:
                context_lines.append(f"- {memory_text}")

        return "\n".join(context_lines)


# Create singleton instance
_gemini_memory_client: Optional[GeminiMemoryClient] = None


def get_gemini_memory_client() -> GeminiMemoryClient:
    """Get or create Gemini memory client singleton"""
    global _gemini_memory_client
    if _gemini_memory_client is None:
        _gemini_memory_client = GeminiMemoryClient()
    return _gemini_memory_client
