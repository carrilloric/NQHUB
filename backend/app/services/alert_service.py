"""
Alert Service for NQHUB 2.0
Implements ADR-013: Multi-channel alert system for risk monitoring

Channels:
- Telegram Bot API
- SendGrid (email)
- Redis Pub/Sub (in-app)

All operations are async and non-blocking.
Failures in one channel do not affect others.
"""

import json
import logging
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
import httpx
import redis.asyncio as aioredis
from app.config import settings
from app.core.database import AsyncSessionLocal
from app.models.production import BotInstance
from sqlalchemy import select

logger = logging.getLogger(__name__)


class AlertEvent(str, Enum):
    """Alert event types for risk monitoring"""
    KILL_SWITCH_ACTIVATED = "kill_switch_activated"
    CIRCUIT_BREAKER_TRIGGERED = "circuit_breaker_triggered"
    DAILY_LOSS_WARNING = "daily_loss_warning"
    DAILY_LOSS_CRITICAL = "daily_loss_critical"
    TRAILING_DRAWDOWN_WARNING = "trailing_drawdown_warning"
    TRAILING_DRAWDOWN_CRITICAL = "trailing_drawdown_critical"
    TRADE_FILLED = "trade_filled"
    BOT_HEARTBEAT_LOST = "bot_heartbeat_lost"
    BOT_STARTED = "bot_started"
    BOT_STOPPED = "bot_stopped"
    PARAMS_DIVERGENCE = "params_divergence"


class AlertLevel(str, Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class TelegramAlertChannel:
    """
    Telegram Bot API channel.
    Token: settings.TELEGRAM_BOT_TOKEN (env var)
    Chat ID: per bot in risk_config.notification_config.telegram_chat_id
    """

    def __init__(self):
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.base_url = f"https://api.telegram.org/bot{self.token}"

    async def send(self, chat_id: str, message: str, level: AlertLevel) -> bool:
        """
        Send Telegram message with level-appropriate emoji
        Format: 🔴 CRITICAL — NQHUB Bot: {bot_name}
        """
        try:
            # Add emoji based on level
            emoji = {
                AlertLevel.INFO: "ℹ️",
                AlertLevel.WARNING: "⚠️",
                AlertLevel.CRITICAL: "🔴"
            }.get(level, "ℹ️")

            formatted_message = f"{emoji} {level.value.upper()} — NQHUB Alert\n\n{message}"

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/sendMessage",
                    json={
                        "chat_id": chat_id,
                        "text": formatted_message,
                        "parse_mode": "HTML"
                    },
                    timeout=10.0
                )
                response.raise_for_status()
                logger.info(f"Telegram alert sent successfully to chat {chat_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to send Telegram alert: {e}")
            return False


class EmailAlertChannel:
    """
    SendGrid API channel.
    API Key: settings.SENDGRID_API_KEY (env var)
    From: nqhub-alerts@automation-labs.ai
    To: per bot in risk_config.notification_config.alert_email
    """

    def __init__(self):
        self.api_key = settings.SENDGRID_API_KEY
        self.from_email = "nqhub-alerts@automation-labs.ai"
        self.base_url = "https://api.sendgrid.com/v3"

    async def send(self, to_email: str, subject: str, body: str, level: AlertLevel) -> bool:
        """
        Send email via SendGrid
        Subject format: [NQHUB][CRITICAL] Event — Bot Name
        """
        try:
            level_tag = f"[{level.value.upper()}]"
            formatted_subject = f"[NQHUB]{level_tag} {subject}"

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/mail/send",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "personalizations": [{
                            "to": [{"email": to_email}]
                        }],
                        "from": {"email": self.from_email, "name": "NQHUB Alerts"},
                        "subject": formatted_subject,
                        "content": [{
                            "type": "text/plain",
                            "value": body
                        }]
                    },
                    timeout=10.0
                )
                response.raise_for_status()
                logger.info(f"Email alert sent successfully to {to_email}")
                return True

        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
            return False


class InAppAlertChannel:
    """
    Redis Pub/Sub channel for in-app notifications.
    Publishes to channel: nqhub.risk.alerts
    WebSocket server rebroadcasts to frontend (Risk Monitor page).
    NEVER throttled — maximum priority.
    """

    def __init__(self):
        self.redis_client: Optional[aioredis.Redis] = None
        self.channel = "nqhub.risk.alerts"

    async def _get_redis(self) -> aioredis.Redis:
        """Get or create Redis connection"""
        if not self.redis_client:
            self.redis_client = await aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
        return self.redis_client

    async def send(
        self,
        bot_id: str,
        event: AlertEvent,
        level: AlertLevel,
        message: str,
        data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Publish alert to Redis for WebSocket distribution
        """
        try:
            redis = await self._get_redis()

            payload = {
                "channel": "risk",
                "event": "alert",
                "data": {
                    "bot_id": bot_id,
                    "event": event.value,
                    "level": level.value,
                    "message": message,
                    "data": data or {},
                    "timestamp": datetime.utcnow().isoformat()
                }
            }

            await redis.publish(self.channel, json.dumps(payload))
            logger.info(f"In-app alert published for bot {bot_id}: {event.value}")
            return True

        except Exception as e:
            logger.error(f"Failed to publish in-app alert: {e}")
            return False

    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()


class AlertService:
    """
    Multi-channel alert service.
    Sends alerts via configured channels based on bot's risk_config.
    Never blocks — all operations are async.
    Failures in one channel don't affect others.
    """

    def __init__(self):
        self.telegram = TelegramAlertChannel()
        self.email = EmailAlertChannel()
        self.in_app = InAppAlertChannel()

    async def send(
        self,
        bot_id: str,
        event: AlertEvent,
        level: AlertLevel,
        message: str,
        data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Main dispatcher. Reads bot config and sends via active channels.

        Args:
            bot_id: Bot identifier
            event: Type of alert event
            level: Severity level
            message: Alert message
            data: Optional additional data
        """
        try:
            # Get bot configuration from database
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(BotInstance).where(BotInstance.id == bot_id)
                )
                bot = result.scalar_one_or_none()

                if not bot:
                    logger.error(f"Bot {bot_id} not found")
                    return

                risk_config = bot.risk_config or {}
                notification_config = risk_config.get("notification_config", {})

                # Get configured channels for this event
                event_channels = notification_config.get("events", {}).get(event.value, [])

                # Always add bot name to message for context
                bot_message = f"Bot: {bot.name}\n{message}"

                # Send via Telegram if configured
                if "telegram" in event_channels and notification_config.get("telegram_enabled", False):
                    chat_id = notification_config.get("telegram_chat_id")
                    if chat_id:
                        await self.telegram.send(
                            chat_id=chat_id,
                            message=bot_message,
                            level=level
                        )
                    else:
                        logger.warning(f"Telegram enabled but no chat_id for bot {bot_id}")

                # Send via Email if configured
                if "email" in event_channels and notification_config.get("email_enabled", False):
                    alert_email = notification_config.get("alert_email")
                    if alert_email:
                        await self.email.send(
                            to_email=alert_email,
                            subject=f"{event.value.replace('_', ' ').title()} — {bot.name}",
                            body=bot_message,
                            level=level
                        )
                    else:
                        logger.warning(f"Email enabled but no alert_email for bot {bot_id}")

                # Always send in-app if configured (never throttled)
                if "in_app" in event_channels and notification_config.get("in_app_enabled", True):
                    await self.in_app.send(
                        bot_id=bot_id,
                        event=event,
                        level=level,
                        message=message,
                        data=data
                    )

                logger.info(f"Alert dispatched for bot {bot_id}: {event.value} ({level.value})")

        except Exception as e:
            # Log error but don't raise — alerts should never crash the system
            logger.error(f"Alert service error for bot {bot_id}: {e}")

    async def close(self):
        """Cleanup resources"""
        await self.in_app.close()


# Global instance
alert_service = AlertService()