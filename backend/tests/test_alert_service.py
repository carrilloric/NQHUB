"""
Tests for Alert Service
Implements test cases from AUT-357
"""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from app.services.alert_service import (
    AlertService,
    AlertEvent,
    AlertLevel,
    TelegramAlertChannel,
    EmailAlertChannel,
    InAppAlertChannel
)
from app.models.production import BotInstance


@pytest.mark.asyncio
async def test_kill_switch_sends_telegram(async_db):
    """
    test_kill_switch_sends_telegram() → KILL_SWITCH_ACTIVATED → Telegram llamado
    """
    # Create bot with Telegram configuration
    bot = BotInstance(
        id="test_bot_1",
        name="Test Bot",
        risk_config={
            "notification_config": {
                "telegram_enabled": True,
                "telegram_chat_id": "123456789",
                "email_enabled": False,
                "in_app_enabled": False,
                "events": {
                    "kill_switch_activated": ["telegram"]
                }
            }
        }
    )
    async_db.add(bot)
    await async_db.flush()

    # Mock Telegram send
    with patch.object(TelegramAlertChannel, 'send', new_callable=AsyncMock) as mock_telegram:
        mock_telegram.return_value = True

        service = AlertService()
        await service.send(
            bot_id="test_bot_1",
            event=AlertEvent.KILL_SWITCH_ACTIVATED,
            level=AlertLevel.CRITICAL,
            message="Kill switch has been activated!"
        )

        # Verify Telegram was called
        mock_telegram.assert_called_once()
        call_args = mock_telegram.call_args
        assert call_args[1]["chat_id"] == "123456789"
        assert call_args[1]["level"] == AlertLevel.CRITICAL
        assert "Kill switch has been activated!" in call_args[1]["message"]


@pytest.mark.asyncio
async def test_kill_switch_sends_email(async_db):
    """
    test_kill_switch_sends_email() → KILL_SWITCH_ACTIVATED → SendGrid llamado
    """
    # Create bot with Email configuration
    bot = BotInstance(
        id="test_bot_2",
        name="Test Bot",
        risk_config={
            "notification_config": {
                "telegram_enabled": False,
                "email_enabled": True,
                "alert_email": "ricardo@automation-labs.ai",
                "in_app_enabled": False,
                "events": {
                    "kill_switch_activated": ["email"]
                }
            }
        }
    )
    async_db.add(bot)
    await async_db.flush()

    # Mock SendGrid send
    with patch.object(EmailAlertChannel, 'send', new_callable=AsyncMock) as mock_email:
        mock_email.return_value = True

        service = AlertService()
        await service.send(
            bot_id="test_bot_2",
            event=AlertEvent.KILL_SWITCH_ACTIVATED,
            level=AlertLevel.CRITICAL,
            message="Kill switch has been activated!"
        )

        # Verify SendGrid was called
        mock_email.assert_called_once()
        call_args = mock_email.call_args
        assert call_args[1]["to_email"] == "ricardo@automation-labs.ai"
        assert call_args[1]["level"] == AlertLevel.CRITICAL
        assert "Kill switch has been activated!" in call_args[1]["body"]


@pytest.mark.asyncio
async def test_kill_switch_publishes_redis(async_db):
    """
    test_kill_switch_publishes_redis() → KILL_SWITCH_ACTIVATED → Redis publish llamado
    """
    # Create bot with in-app configuration
    bot = BotInstance(
        id="test_bot_3",
        name="Test Bot",
        risk_config={
            "notification_config": {
                "telegram_enabled": False,
                "email_enabled": False,
                "in_app_enabled": True,
                "events": {
                    "kill_switch_activated": ["in_app"]
                }
            }
        }
    )
    async_db.add(bot)
    await async_db.flush()

    # Mock Redis publish
    with patch.object(InAppAlertChannel, 'send', new_callable=AsyncMock) as mock_in_app:
        mock_in_app.return_value = True

        service = AlertService()
        await service.send(
            bot_id="test_bot_3",
            event=AlertEvent.KILL_SWITCH_ACTIVATED,
            level=AlertLevel.CRITICAL,
            message="Kill switch has been activated!"
        )

        # Verify Redis publish was called
        mock_in_app.assert_called_once()
        call_args = mock_in_app.call_args
        assert call_args[1]["bot_id"] == "test_bot_3"
        assert call_args[1]["event"] == AlertEvent.KILL_SWITCH_ACTIVATED
        assert call_args[1]["level"] == AlertLevel.CRITICAL
        assert call_args[1]["message"] == "Kill switch has been activated!"


@pytest.mark.asyncio
async def test_trade_filled_no_channels(async_db):
    """
    test_trade_filled_no_channels() → TRADE_FILLED con config vacía → ningún canal llamado
    """
    # Create bot with empty configuration for TRADE_FILLED
    bot = BotInstance(
        id="test_bot_4",
        name="Test Bot",
        risk_config={
            "notification_config": {
                "telegram_enabled": True,
                "telegram_chat_id": "123456789",
                "email_enabled": True,
                "alert_email": "test@example.com",
                "in_app_enabled": True,
                "events": {
                    "trade_filled": []  # Empty channels for this event
                }
            }
        }
    )
    async_db.add(bot)
    await async_db.flush()

    # Mock all channels
    with patch.object(TelegramAlertChannel, 'send', new_callable=AsyncMock) as mock_telegram, \
         patch.object(EmailAlertChannel, 'send', new_callable=AsyncMock) as mock_email, \
         patch.object(InAppAlertChannel, 'send', new_callable=AsyncMock) as mock_in_app:

        service = AlertService()
        await service.send(
            bot_id="test_bot_4",
            event=AlertEvent.TRADE_FILLED,
            level=AlertLevel.INFO,
            message="Trade has been filled"
        )

        # Verify no channels were called
        mock_telegram.assert_not_called()
        mock_email.assert_not_called()
        mock_in_app.assert_not_called()


@pytest.mark.asyncio
async def test_critical_level_uses_red_emoji(async_db):
    """
    test_critical_level_uses_red_emoji() → level=critical → mensaje tiene 🔴
    """
    # Create bot with Telegram configuration
    bot = BotInstance(
        id="test_bot_5",
        name="Test Bot",
        risk_config={
            "notification_config": {
                "telegram_enabled": True,
                "telegram_chat_id": "123456789",
                "email_enabled": False,
                "in_app_enabled": False,
                "events": {
                    "circuit_breaker_triggered": ["telegram"]
                }
            }
        }
    )
    async_db.add(bot)
    await async_db.flush()

    # Mock httpx client to capture the message
    with patch('app.services.alert_service.httpx.AsyncClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.raise_for_status = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value.__aenter__.return_value = mock_client

        service = AlertService()
        await service.send(
            bot_id="test_bot_5",
            event=AlertEvent.CIRCUIT_BREAKER_TRIGGERED,
            level=AlertLevel.CRITICAL,
            message="Circuit breaker triggered!"
        )

        # Verify red emoji is in the message
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        message_data = call_args[1]["json"]
        assert "🔴" in message_data["text"]
        assert "CRITICAL" in message_data["text"]


@pytest.mark.asyncio
async def test_telegram_disabled_skips_channel(async_db):
    """
    test_telegram_disabled_skips_channel() → telegram_enabled=false → Telegram NO llamado
    """
    # Create bot with Telegram disabled
    bot = BotInstance(
        id="test_bot_6",
        name="Test Bot",
        risk_config={
            "notification_config": {
                "telegram_enabled": False,  # Disabled
                "telegram_chat_id": "123456789",
                "email_enabled": False,
                "in_app_enabled": False,
                "events": {
                    "daily_loss_warning": ["telegram"]  # Event configured but channel disabled
                }
            }
        }
    )
    async_db.add(bot)
    await async_db.flush()

    # Mock Telegram send
    with patch.object(TelegramAlertChannel, 'send', new_callable=AsyncMock) as mock_telegram:
        service = AlertService()
        await service.send(
            bot_id="test_bot_6",
            event=AlertEvent.DAILY_LOSS_WARNING,
            level=AlertLevel.WARNING,
            message="Daily loss warning!"
        )

        # Verify Telegram was NOT called
        mock_telegram.assert_not_called()


@pytest.mark.asyncio
async def test_in_app_always_highest_priority(async_db):
    """
    test_in_app_always_highest_priority() → in_app channel → Redis publish con canal risk
    """
    # Create bot with in-app configuration
    bot = BotInstance(
        id="test_bot_7",
        name="Test Bot",
        risk_config={
            "notification_config": {
                "telegram_enabled": False,
                "email_enabled": False,
                "in_app_enabled": True,
                "events": {
                    "trailing_drawdown_critical": ["in_app"]
                }
            }
        }
    )
    async_db.add(bot)
    await async_db.flush()

    # Mock Redis client to capture the publish
    with patch('app.services.alert_service.aioredis.from_url') as mock_redis_from_url:
        mock_redis = AsyncMock()
        mock_redis_from_url.return_value = mock_redis

        service = AlertService()
        await service.send(
            bot_id="test_bot_7",
            event=AlertEvent.TRAILING_DRAWDOWN_CRITICAL,
            level=AlertLevel.CRITICAL,
            message="Trailing drawdown critical!"
        )

        # Verify Redis publish was called with risk channel
        mock_redis.publish.assert_called_once()
        call_args = mock_redis.publish.call_args
        assert call_args[0][0] == "nqhub.risk.alerts"  # Channel name

        # Parse the JSON payload
        payload = json.loads(call_args[0][1])
        assert payload["channel"] == "risk"
        assert payload["event"] == "alert"
        assert payload["data"]["bot_id"] == "test_bot_7"
        assert payload["data"]["level"] == "critical"


@pytest.mark.asyncio
async def test_alert_never_blocks_on_failure(async_db):
    """
    test_alert_never_blocks_on_failure() → Telegram falla → no exception, otros canales continúan
    """
    # Create bot with multiple channels
    bot = BotInstance(
        id="test_bot_8",
        name="Test Bot",
        risk_config={
            "notification_config": {
                "telegram_enabled": True,
                "telegram_chat_id": "123456789",
                "email_enabled": True,
                "alert_email": "test@example.com",
                "in_app_enabled": True,
                "events": {
                    "bot_stopped": ["telegram", "email", "in_app"]
                }
            }
        }
    )
    async_db.add(bot)
    await async_db.flush()

    # Mock channels - Telegram fails, others succeed
    with patch.object(TelegramAlertChannel, 'send', new_callable=AsyncMock) as mock_telegram, \
         patch.object(EmailAlertChannel, 'send', new_callable=AsyncMock) as mock_email, \
         patch.object(InAppAlertChannel, 'send', new_callable=AsyncMock) as mock_in_app:

        # Telegram fails
        mock_telegram.side_effect = Exception("Telegram API error")
        # Others succeed
        mock_email.return_value = True
        mock_in_app.return_value = True

        service = AlertService()

        # Should not raise exception
        await service.send(
            bot_id="test_bot_8",
            event=AlertEvent.BOT_STOPPED,
            level=AlertLevel.INFO,
            message="Bot has stopped"
        )

        # Verify all channels were attempted
        mock_telegram.assert_called_once()
        mock_email.assert_called_once()
        mock_in_app.assert_called_once()


@pytest.mark.asyncio
async def test_heartbeat_lost_alert_fires(async_db):
    """
    test_heartbeat_lost_alert_fires() → bot sin heartbeat >120s → BOT_HEARTBEAT_LOST enviado

    Note: This test verifies that the alert can be sent. The actual heartbeat
    monitoring logic would be in a separate service that calls AlertService.
    """
    # Create bot with configuration for heartbeat lost
    bot = BotInstance(
        id="test_bot_9",
        name="Test Bot",
        risk_config={
            "notification_config": {
                "telegram_enabled": True,
                "telegram_chat_id": "123456789",
                "email_enabled": True,
                "alert_email": "admin@example.com",
                "in_app_enabled": True,
                "events": {
                    "bot_heartbeat_lost": ["telegram", "email", "in_app"]
                }
            }
        }
    )
    async_db.add(bot)
    await async_db.flush()

    # Mock all channels
    with patch.object(TelegramAlertChannel, 'send', new_callable=AsyncMock) as mock_telegram, \
         patch.object(EmailAlertChannel, 'send', new_callable=AsyncMock) as mock_email, \
         patch.object(InAppAlertChannel, 'send', new_callable=AsyncMock) as mock_in_app:

        mock_telegram.return_value = True
        mock_email.return_value = True
        mock_in_app.return_value = True

        service = AlertService()

        # Simulate heartbeat lost alert
        await service.send(
            bot_id="test_bot_9",
            event=AlertEvent.BOT_HEARTBEAT_LOST,
            level=AlertLevel.CRITICAL,
            message="Bot heartbeat lost for >120 seconds",
            data={"last_heartbeat": (datetime.utcnow() - timedelta(seconds=125)).isoformat()}
        )

        # Verify all configured channels were called
        mock_telegram.assert_called_once()
        mock_email.assert_called_once()
        mock_in_app.assert_called_once()

        # Verify critical level was used
        assert mock_telegram.call_args[1]["level"] == AlertLevel.CRITICAL
        assert mock_email.call_args[1]["level"] == AlertLevel.CRITICAL
        assert mock_in_app.call_args[1]["level"] == AlertLevel.CRITICAL