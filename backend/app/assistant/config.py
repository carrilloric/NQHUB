"""
Configuration for AI Assistant module
"""
from app.config import settings


class AssistantConfig:
    """Configuration for the AI Assistant"""

    # Feature flag
    ENABLED: bool = True

    # Claude (Anthropic) configuration
    CLAUDE_API_KEY: str | None = settings.ANTHROPIC_API_KEY
    CLAUDE_MODEL: str = "claude-3-opus-20240229"  # Claude 3 Opus (most capable, available to all)
    CLAUDE_MAX_TOKENS: int = 4096
    CLAUDE_TEMPERATURE: float = 0.7

    # Gemini configuration (for mem0)
    GEMINI_API_KEY: str | None = settings.OPENAI_API_KEY  # Will be updated when added to settings
    GEMINI_MODEL: str = "gemini-2.0-flash-exp"

    # mem0 configuration
    MEM0_API_KEY: str | None = settings.MEM0_API_KEY
    MEM0_ENABLED: bool = MEM0_API_KEY is not None

    # Polling configuration for proactive notifications
    POLLING_INTERVAL_SECONDS: int = 15
    MAX_EVENTS_PER_POLL: int = 10
    EVENT_RETENTION_HOURS: int = 24  # How long to keep notified events

    # Conversation limits
    MAX_CONVERSATION_TITLE_LENGTH: int = 255
    MAX_MESSAGE_LENGTH: int = 5000
    MAX_MESSAGES_PER_CONVERSATION: int = 100

    # System prompts
    SYSTEM_PROMPT_GENERAL: str = """You are a helpful AI assistant for NQHUB, a professional trading analytics platform.
You can help users:
- Query the database using natural language (you have access to SQL tools)
- Check system status (ETL jobs, pattern detection, database stats)
- Answer questions about trading patterns (FVGs, Liquidity Pools, Order Blocks)
- Provide insights about market data

Be concise, professional, and trading-focused. Use trading terminology when appropriate."""

    SYSTEM_PROMPT_SQL_CLASSIFICATION: str = """Classify the user's query into one of these categories:
- SQL_QUERY: User wants data from the database (counts, lists, statistics, etc.)
- STATUS_CHECK: User wants to know system status (ETL jobs, patterns, health)
- GENERAL_CHAT: General question or conversation

Respond with ONLY the category name, nothing else."""

    # Tool descriptions for LangGraph
    TOOLS = {
        "status_monitor": {
            "name": "check_status",
            "description": "Check system status including ETL jobs, pattern detection, database stats, and system health.",
        },
    }


# Create singleton instance
assistant_config = AssistantConfig()
