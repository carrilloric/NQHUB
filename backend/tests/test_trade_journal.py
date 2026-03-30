"""
Tests for Trade Journal API Endpoints (AUT-351)

Tests for M3.8 Trade Journal with post-trade analysis and EOD reports.
"""

import pytest
from datetime import datetime, date, timedelta
from uuid import uuid4
from decimal import Decimal
from fastapi import status

from app.models.production import Order, Trade, BotInstance
from app.models.strategy import Strategy


# ============= Test Fixtures =============

@pytest.fixture
async def test_strategy(async_db):
    """Create a test strategy"""
    strategy = Strategy(
        id=uuid4(),
        name="Test Strategy",
        version="1.0.0",
        type="rule_based",
        status="approved"
    )
    async_db.add(strategy)
    await async_db.flush()
    await async_db.refresh(strategy)
    return strategy


@pytest.fixture
async def test_bot(async_db, test_strategy):
    """Create a test bot instance"""
    bot = BotInstance(
        id=uuid4(),
        name="Test Bot",
        strategy_id=test_strategy.id,
        mode="paper",
        status="running"
    )
    async_db.add(bot)
    await async_db.flush()
    await async_db.refresh(bot)
    return bot


@pytest.fixture
async def bracket_orders(async_db, test_bot):
    """Create a complete bracket order set (entry + stop loss filled)"""
    bracket_id = uuid4()
    now = datetime.utcnow()

    # Entry order (FILLED)
    entry = Order(
        id=uuid4(),
        bot_id=test_bot.id,
        bracket_id=bracket_id,
        symbol="NQ",
        side="BUY",
        type="MARKET",
        quantity=1,
        fill_price=Decimal("16850.00"),
        status="FILLED",
        submitted_at=now,
        filled_at=now + timedelta(seconds=1)
    )

    # Stop loss order (FILLED) - triggers at loss
    stop_loss = Order(
        id=uuid4(),
        bot_id=test_bot.id,
        bracket_id=bracket_id,
        symbol="NQ",
        side="SELL",
        type="STOP",
        quantity=1,
        price=Decimal("16840.00"),
        fill_price=Decimal("16840.00"),
        status="FILLED",
        submitted_at=now,
        filled_at=now + timedelta(seconds=30)
    )

    # Take profit order (PENDING) - didn't trigger
    take_profit = Order(
        id=uuid4(),
        bot_id=test_bot.id,
        bracket_id=bracket_id,
        symbol="NQ",
        side="SELL",
        type="LIMIT",
        quantity=1,
        price=Decimal("16870.00"),
        status="CANCELLED",
        submitted_at=now,
        cancelled_at=now + timedelta(seconds=30)
    )

    async_db.add_all([entry, stop_loss, take_profit])
    await async_db.flush()
    await async_db.refresh(entry)
    await async_db.refresh(stop_loss)
    await async_db.refresh(take_profit)

    return {
        'bracket_id': bracket_id,
        'entry': entry,
        'stop_loss': stop_loss,
        'take_profit': take_profit
    }


@pytest.fixture
async def winning_bracket(async_db, test_bot):
    """Create a winning bracket (take profit filled)"""
    bracket_id = uuid4()
    now = datetime.utcnow()

    # Entry order
    entry = Order(
        id=uuid4(),
        bot_id=test_bot.id,
        bracket_id=bracket_id,
        symbol="NQ",
        side="BUY",
        type="MARKET",
        quantity=2,
        fill_price=Decimal("16850.00"),
        status="FILLED",
        submitted_at=now,
        filled_at=now + timedelta(seconds=1)
    )

    # Take profit order (FILLED)
    take_profit = Order(
        id=uuid4(),
        bot_id=test_bot.id,
        bracket_id=bracket_id,
        symbol="NQ",
        side="SELL",
        type="LIMIT",
        quantity=2,
        price=Decimal("16870.00"),
        fill_price=Decimal("16870.00"),
        status="FILLED",
        submitted_at=now,
        filled_at=now + timedelta(seconds=45)
    )

    # Stop loss (CANCELLED)
    stop_loss = Order(
        id=uuid4(),
        bot_id=test_bot.id,
        bracket_id=bracket_id,
        symbol="NQ",
        side="SELL",
        type="STOP",
        quantity=2,
        price=Decimal("16840.00"),
        status="CANCELLED",
        submitted_at=now,
        cancelled_at=now + timedelta(seconds=45)
    )

    async_db.add_all([entry, take_profit, stop_loss])
    await async_db.flush()
    await async_db.refresh(entry)
    await async_db.refresh(take_profit)
    await async_db.refresh(stop_loss)

    return {
        'bracket_id': bracket_id,
        'entry': entry,
        'take_profit': take_profit,
        'stop_loss': stop_loss
    }


@pytest.fixture
async def sample_trade(async_db, test_bot, test_strategy, bracket_orders):
    """Create a sample trade"""
    trade = Trade(
        id=uuid4(),
        bot_id=test_bot.id,
        strategy_id=test_strategy.id,
        entry_order_id=bracket_orders['entry'].id,
        exit_order_id=bracket_orders['stop_loss'].id,
        direction="LONG",
        entry_price=Decimal("16850.00"),
        exit_price=Decimal("16840.00"),
        quantity=1,
        pnl_ticks=-40,  # (16840 - 16850) / 0.25 = -40 ticks
        pnl_usd=Decimal("-200.00"),  # -40 ticks * $5 = -$200
        commission=Decimal("4.50"),
        notes="Test losing trade",
        tags=["test", "backtest"],
        opened_at=bracket_orders['entry'].filled_at,
        closed_at=bracket_orders['stop_loss'].filled_at
    )

    async_db.add(trade)
    await async_db.flush()
    await async_db.refresh(trade)
    return trade


# ============= Happy Path Tests =============

@pytest.mark.asyncio
async def test_list_trades_empty(async_client, auth_headers):
    """Test GET /trade-journal/trades returns empty list when no trades"""
    response = await async_client.get(
        "/api/v1/trade-journal/trades",
        headers=auth_headers
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


@pytest.mark.asyncio
async def test_list_trades_with_data(async_client, auth_headers, sample_trade):
    """Test GET /trade-journal/trades returns trades"""
    response = await async_client.get(
        "/api/v1/trade-journal/trades",
        headers=auth_headers
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1

    trade = data[0]
    assert trade['direction'] == "LONG"
    assert float(trade['pnl_usd']) == -200.0
    assert trade['pnl_ticks'] == -40
    assert trade['notes'] == "Test losing trade"
    assert trade['tags'] == ["test", "backtest"]


@pytest.mark.asyncio
async def test_list_trades_with_filters(async_client, auth_headers, sample_trade, test_bot):
    """Test GET /trade-journal/trades with bot_id filter"""
    response = await async_client.get(
        f"/api/v1/trade-journal/trades?bot_id={test_bot.id}",
        headers=auth_headers
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]['bot_id'] == str(test_bot.id)


@pytest.mark.asyncio
async def test_get_single_trade(async_client, auth_headers, sample_trade):
    """Test GET /trade-journal/trades/{trade_id}"""
    response = await async_client.get(
        f"/api/v1/trade-journal/trades/{sample_trade.id}",
        headers=auth_headers
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data['id'] == str(sample_trade.id)
    assert data['direction'] == "LONG"
    assert float(data['pnl_usd']) == -200.0


@pytest.mark.asyncio
async def test_get_single_trade_not_found(async_client, auth_headers):
    """Test GET /trade-journal/trades/{trade_id} returns 404 for non-existent trade"""
    fake_id = uuid4()
    response = await async_client.get(
        f"/api/v1/trade-journal/trades/{fake_id}",
        headers=auth_headers
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_calculate_trades_from_bracket(async_client, auth_headers, bracket_orders, test_bot, async_db):
    """Test POST /trade-journal/calculate creates trades from bracket orders"""
    response = await async_client.post(
        "/api/v1/trade-journal/calculate",
        json={
            "bracket_ids": [str(bracket_orders['bracket_id'])]
        },
        headers=auth_headers
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data['trades_created'] >= 1
    assert data['brackets_processed'] == 1
    assert len(data['errors']) == 0

    # Verify trade was created in database
    from sqlalchemy import select
    result = await async_db.execute(
        select(Trade).where(Trade.bot_id == test_bot.id)
    )
    trades = result.scalars().all()
    assert len(trades) >= 1

    trade = trades[0]
    assert trade.direction == "LONG"
    assert trade.pnl_ticks == -40  # (16840 - 16850) / 0.25 = -40 ticks
    assert trade.pnl_usd == Decimal("-200.00")  # -40 * $5


@pytest.mark.asyncio
async def test_calculate_winning_trade(async_client, auth_headers, winning_bracket, test_bot, async_db):
    """Test calculating a winning trade (take profit filled)"""
    response = await async_client.post(
        "/api/v1/trade-journal/calculate",
        json={
            "bracket_ids": [str(winning_bracket['bracket_id'])]
        },
        headers=auth_headers
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data['trades_created'] >= 1

    # Verify trade calculation
    from sqlalchemy import select
    result = await async_db.execute(
        select(Trade).where(Trade.bot_id == test_bot.id)
    )
    trades = result.scalars().all()
    trade = trades[0]

    # Winning trade: entry 16850, exit 16870
    # P&L = (16870 - 16850) / 0.25 = 80 ticks * $5 = $400 per contract
    # With 2 contracts = $800
    assert trade.pnl_ticks == 80
    assert trade.pnl_usd == Decimal("800.00")


@pytest.mark.asyncio
async def test_update_trade_annotations(async_client, auth_headers, sample_trade):
    """Test PATCH /trade-journal/trades/{trade_id}/annotations updates notes and tags only"""
    new_notes = "Updated analysis: poor entry timing"
    new_tags = ["reviewed", "need-improvement"]

    response = await async_client.patch(
        f"/api/v1/trade-journal/trades/{sample_trade.id}/annotations",
        json={
            "notes": new_notes,
            "tags": new_tags
        },
        headers=auth_headers
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data['notes'] == new_notes
    assert data['tags'] == new_tags

    # Verify other fields unchanged
    assert data['direction'] == "LONG"
    assert float(data['pnl_usd']) == -200.0
    assert data['pnl_ticks'] == -40


@pytest.mark.asyncio
async def test_update_annotations_partial(async_client, auth_headers, sample_trade):
    """Test PATCH only updates provided fields (partial update)"""
    response = await async_client.patch(
        f"/api/v1/trade-journal/trades/{sample_trade.id}/annotations",
        json={
            "notes": "Only updating notes"
        },
        headers=auth_headers
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data['notes'] == "Only updating notes"
    assert data['tags'] == ["test", "backtest"]  # Original tags unchanged


@pytest.mark.asyncio
async def test_eod_report_empty(async_client, auth_headers):
    """Test POST /trade-journal/eod-report with no trades"""
    today = date.today()

    response = await async_client.post(
        "/api/v1/trade-journal/eod-report",
        json={
            "report_date": str(today)
        },
        headers=auth_headers
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data['total_trades'] == 0
    assert float(data['total_pnl_usd']) == 0.0
    assert data['win_rate'] == 0.0


@pytest.mark.asyncio
async def test_eod_report_with_trades(async_client, auth_headers, sample_trade):
    """Test POST /trade-journal/eod-report generates report with metrics"""
    today = date.today()

    response = await async_client.post(
        "/api/v1/trade-journal/eod-report",
        json={
            "report_date": str(today)
        },
        headers=auth_headers
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    # Basic stats
    assert data['total_trades'] == 1
    assert float(data['total_pnl_usd']) == -200.0
    assert data['total_pnl_ticks'] == -40

    # Performance metrics
    assert data['win_rate'] == 0.0  # 0 wins out of 1 trade
    assert 'trades' in data
    assert len(data['trades']) == 1


@pytest.mark.asyncio
async def test_eod_report_with_bot_filter(async_client, auth_headers, sample_trade, test_bot):
    """Test EOD report with bot_id filter"""
    today = date.today()

    response = await async_client.post(
        "/api/v1/trade-journal/eod-report",
        json={
            "report_date": str(today),
            "bot_id": str(test_bot.id)
        },
        headers=auth_headers
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data['total_trades'] == 1


# ============= Edge Cases =============

@pytest.mark.asyncio
async def test_calculate_incomplete_bracket(async_client, auth_headers, test_bot, async_db):
    """Test calculating trades with incomplete bracket (only entry, no exit)"""
    bracket_id = uuid4()
    now = datetime.utcnow()

    # Only entry order, no exit
    entry = Order(
        id=uuid4(),
        bot_id=test_bot.id,
        bracket_id=bracket_id,
        symbol="NQ",
        side="BUY",
        type="MARKET",
        quantity=1,
        fill_price=Decimal("16850.00"),
        status="FILLED",
        submitted_at=now,
        filled_at=now + timedelta(seconds=1)
    )

    async_db.add(entry)
    await async_db.flush()

    response = await async_client.post(
        "/api/v1/trade-journal/calculate",
        json={
            "bracket_ids": [str(bracket_id)]
        },
        headers=auth_headers
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    # Should skip incomplete brackets
    assert data['trades_created'] == 0
    assert data['brackets_processed'] == 1


@pytest.mark.asyncio
async def test_pnl_calculation_short_trade(async_client, auth_headers, test_bot, async_db):
    """Test P&L calculation for SHORT trade"""
    bracket_id = uuid4()
    now = datetime.utcnow()

    # Short entry (SELL)
    entry = Order(
        id=uuid4(),
        bot_id=test_bot.id,
        bracket_id=bracket_id,
        symbol="NQ",
        side="SELL",
        type="MARKET",
        quantity=1,
        fill_price=Decimal("16850.00"),
        status="FILLED",
        submitted_at=now,
        filled_at=now + timedelta(seconds=1)
    )

    # Cover at profit (BUY at lower price)
    cover = Order(
        id=uuid4(),
        bot_id=test_bot.id,
        bracket_id=bracket_id,
        symbol="NQ",
        side="BUY",
        type="LIMIT",
        quantity=1,
        fill_price=Decimal("16830.00"),
        status="FILLED",
        submitted_at=now,
        filled_at=now + timedelta(seconds=30)
    )

    async_db.add_all([entry, cover])
    await async_db.flush()

    response = await async_client.post(
        "/api/v1/trade-journal/calculate",
        json={
            "bracket_ids": [str(bracket_id)]
        },
        headers=auth_headers
    )

    assert response.status_code == status.HTTP_200_OK

    # Verify SHORT P&L calculation
    from sqlalchemy import select
    result = await async_db.execute(
        select(Trade).where(Trade.bot_id == test_bot.id)
    )
    trade = result.scalar_one()

    # SHORT: entry 16850, exit 16830
    # P&L = (16850 - 16830) / 0.25 = 80 ticks
    assert trade.direction == "SHORT"
    assert trade.pnl_ticks == 80
    assert trade.pnl_usd == Decimal("400.00")  # 80 * $5
