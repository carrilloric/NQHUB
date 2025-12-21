"""
Claude (Anthropic) API client wrapper
"""
from typing import Optional, List, Dict, Any
from anthropic import Anthropic, AsyncAnthropic
from app.assistant.config import assistant_config


class ClaudeClient:
    """Wrapper for Claude API calls"""

    def __init__(self, api_key: Optional[str] = None):
        import logging
        self.api_key = api_key or assistant_config.CLAUDE_API_KEY
        self.available = bool(self.api_key)

        if not self.available:
            logging.warning("Claude API key not configured - Claude features will be disabled")
            self.client = None
            self.async_client = None
        else:
            self.client = Anthropic(api_key=self.api_key)
            self.async_client = AsyncAnthropic(api_key=self.api_key)

        self.model = assistant_config.CLAUDE_MODEL
        self.max_tokens = assistant_config.CLAUDE_MAX_TOKENS
        self.temperature = assistant_config.CLAUDE_TEMPERATURE

    def chat(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Send a chat request to Claude

        Args:
            messages: List of message dicts with 'role' and 'content'
            system: System prompt (optional)
            temperature: Override default temperature
            max_tokens: Override default max_tokens

        Returns:
            Dict with 'content', 'usage', and 'stop_reason'
        """
        if not self.available:
            return {
                "content": "Claude API is not configured. Please add ANTHROPIC_API_KEY to your .env file.",
                "usage": {"input_tokens": 0, "output_tokens": 0},
                "stop_reason": "not_configured",
                "model": "none",
            }

        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens or self.max_tokens,
            temperature=temperature or self.temperature,
            system=system or assistant_config.SYSTEM_PROMPT_GENERAL,
            messages=messages
        )

        return {
            "content": response.content[0].text if response.content else "",
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
            "stop_reason": response.stop_reason,
            "model": response.model,
        }

    async def chat_async(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Async version of chat()"""
        response = await self.async_client.messages.create(
            model=self.model,
            max_tokens=max_tokens or self.max_tokens,
            temperature=temperature or self.temperature,
            system=system or assistant_config.SYSTEM_PROMPT_GENERAL,
            messages=messages
        )

        return {
            "content": response.content[0].text if response.content else "",
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
            "stop_reason": response.stop_reason,
            "model": response.model,
        }

    def classify_intent(self, user_message: str) -> str:
        """
        Classify user's intent using Claude

        Returns: 'SQL_QUERY', 'STATUS_CHECK', or 'GENERAL_CHAT'
        """
        response = self.chat(
            messages=[{"role": "user", "content": user_message}],
            system=assistant_config.SYSTEM_PROMPT_SQL_CLASSIFICATION,
            temperature=0.1,
            max_tokens=20,
        )

        content = response["content"].strip().upper()

        # Validate response
        valid_intents = ["SQL_QUERY", "STATUS_CHECK", "GENERAL_CHAT"]
        for intent in valid_intents:
            if intent in content:
                return intent

        # Default to general chat if classification fails
        return "GENERAL_CHAT"


# Create singleton instance
_claude_client: Optional[ClaudeClient] = None


def get_claude_client() -> ClaudeClient:
    """Get or create Claude client singleton"""
    global _claude_client
    if _claude_client is None:
        _claude_client = ClaudeClient()
    return _claude_client
