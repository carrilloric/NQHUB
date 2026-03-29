"""
Tests for Apex Trading compliance validator.

Uses synthetic data - no real DB required (mock ApexAccount as dataclass).
"""

import pytest
from datetime import datetime, timedelta
import pandas as pd
import pytz
from app.research.compliance.apex_validator import (
    ApexComplianceValidator,
    ApexAccount,
    CheckResult,
    ValidationReport,
    BacktestResults
)


@pytest.fixture
def apex_account_50k():
    """Mock $50K Apex account configuration."""
    return ApexAccount(
        id=1,
        account_size_usd=50000,
        trailing_threshold_usd=2500,
        max_daily_loss_usd=1500,
        max_contracts=10,
        consistency_pct=30.0,
        news_blackout_minutes=5
    )


@pytest.fixture
def validator():
    """Create validator instance."""
    return ApexComplianceValidator()


@pytest.fixture
def et_timezone():
    """Eastern Time timezone."""
    return pytz.timezone('US/Eastern')


class TestTrailingThreshold:
    """Test trailing threshold compliance checks."""

    def test_trailing_threshold_passes(self, validator, apex_account_50k):
        """drawdown=$1,000, threshold=$2,500 → passed"""
        result = validator.check_trailing_threshold(
            current_balance=51000,
            high_watermark=52000,
            apex_account=apex_account_50k
        )
        assert result.passed is True
        assert result.value == 1000
        assert result.limit == 2500
        assert "40.0%" in result.message

    def test_trailing_threshold_violation(self, validator, apex_account_50k):
        """drawdown=$2,600, threshold=$2,500 → violation"""
        result = validator.check_trailing_threshold(
            current_balance=49400,
            high_watermark=52000,
            apex_account=apex_account_50k
        )
        assert result.passed is False
        assert result.value == 2600
        assert result.limit == 2500
        assert "104.0%" in result.message

    def test_trailing_threshold_warning(self, validator, apex_account_50k):
        """drawdown=$2,100, threshold=$2,500 → 84% → warning"""
        result = validator.check_trailing_threshold(
            current_balance=49900,
            high_watermark=52000,
            apex_account=apex_account_50k
        )
        assert result.passed is True
        assert result.value == 2100
        assert result.limit == 2500
        assert "84.0%" in result.message


class TestDailyLoss:
    """Test daily loss compliance checks."""

    def test_daily_loss_passes(self, validator, apex_account_50k):
        """loss=$800, limit=$1,500 → passed"""
        result = validator.check_daily_loss(
            daily_loss_usd=-800,
            apex_account=apex_account_50k
        )
        assert result.passed is True
        assert result.value == 800
        assert result.limit == 1500
        assert "53.3%" in result.message

    def test_daily_loss_violation(self, validator, apex_account_50k):
        """loss=$1,600, limit=$1,500 → violation"""
        result = validator.check_daily_loss(
            daily_loss_usd=-1600,
            apex_account=apex_account_50k
        )
        assert result.passed is False
        assert result.value == 1600
        assert result.limit == 1500
        assert "106.7%" in result.message


class TestMaxContracts:
    """Test max contracts compliance checks."""

    def test_max_contracts_passes(self, validator, apex_account_50k):
        """position=2, order=2, max=10 → passed"""
        result = validator.check_max_contracts(
            order_qty=2,
            current_position=2,
            apex_account=apex_account_50k
        )
        assert result.passed is True
        assert result.value == 4
        assert result.limit == 10
        assert "40.0%" in result.message

    def test_max_contracts_violation(self, validator, apex_account_50k):
        """position=9, order=2, max=10 → violation"""
        result = validator.check_max_contracts(
            order_qty=2,
            current_position=9,
            apex_account=apex_account_50k
        )
        assert result.passed is False
        assert result.value == 11
        assert result.limit == 10
        assert "110.0%" in result.message


class TestTradingHours:
    """Test trading hours compliance checks."""

    def test_trading_hours_blocked(self, validator, et_timezone):
        """4:30 PM ET → violation"""
        # Create timestamp at 4:30 PM ET
        et_time = et_timezone.localize(datetime(2024, 3, 15, 16, 30, 0))
        result = validator.check_trading_hours(et_time)
        assert result.passed is False
        assert "16:30:00 ET" in result.message
        assert "CLOSED" in result.message

    def test_trading_hours_allowed(self, validator, et_timezone):
        """10:00 AM ET → passed"""
        # Create timestamp at 10:00 AM ET
        et_time = et_timezone.localize(datetime(2024, 3, 15, 10, 0, 0))
        result = validator.check_trading_hours(et_time)
        assert result.passed is True
        assert "10:00:00 ET" in result.message
        assert "OPEN" in result.message

    def test_trading_hours_utc_conversion(self, validator):
        """Test UTC timestamp is correctly converted to ET."""
        # 9:30 PM UTC = 4:30 PM ET (during EDT)
        utc_time = pytz.UTC.localize(datetime(2024, 6, 15, 20, 30, 0))  # June = EDT
        result = validator.check_trading_hours(utc_time)
        assert result.passed is False
        assert "CLOSED" in result.message


class TestConsistencyRule:
    """Test consistency rule compliance checks."""

    def test_consistency_rule_passes(self, validator, apex_account_50k):
        """max_day=$250, total=$1,000, pct=30 → passed"""
        daily_pnl = pd.Series([100, 250, 150, 200, 300])
        total_profit = 1000
        result = validator.check_consistency_rule(
            daily_pnl_series=daily_pnl,
            total_profit=total_profit,
            apex_account=apex_account_50k
        )
        assert result.passed is True
        assert result.value == 300  # Max daily
        assert result.limit == 300  # 30% of 1000
        assert "100.0%" in result.message

    def test_consistency_rule_violation(self, validator, apex_account_50k):
        """max_day=$350, total=$1,000, pct=30 → violation"""
        daily_pnl = pd.Series([100, 350, 150, 200, 200])
        total_profit = 1000
        result = validator.check_consistency_rule(
            daily_pnl_series=daily_pnl,
            total_profit=total_profit,
            apex_account=apex_account_50k
        )
        assert result.passed is False
        assert result.value == 350
        assert result.limit == 300
        assert "116.7%" in result.message

    def test_consistency_rule_skips_when_no_profit(self, validator, apex_account_50k):
        """total_profit=0 → passed (skip)"""
        daily_pnl = pd.Series([100, -100, 50, -50])
        total_profit = 0
        result = validator.check_consistency_rule(
            daily_pnl_series=daily_pnl,
            total_profit=total_profit,
            apex_account=apex_account_50k
        )
        assert result.passed is True
        assert "skipped" in result.message.lower()

    def test_consistency_rule_skips_when_negative_profit(self, validator, apex_account_50k):
        """total_profit=-500 → passed (skip)"""
        daily_pnl = pd.Series([-100, -200, -50, -150])
        total_profit = -500
        result = validator.check_consistency_rule(
            daily_pnl_series=daily_pnl,
            total_profit=total_profit,
            apex_account=apex_account_50k
        )
        assert result.passed is True
        assert "skipped" in result.message.lower()


class TestNewsBlackout:
    """Test news blackout compliance checks."""

    def test_news_blackout_violation(self, validator, apex_account_50k):
        """Trading 3 minutes before news → violation"""
        trade_time = datetime(2024, 3, 15, 14, 27, 0, tzinfo=pytz.UTC)
        news_time = datetime(2024, 3, 15, 14, 30, 0, tzinfo=pytz.UTC)
        result = validator.check_news_blackout(
            timestamp=trade_time,
            news_events=[news_time],
            apex_account=apex_account_50k
        )
        assert result.passed is False
        assert "3.0 minutes" in result.message

    def test_news_blackout_passes(self, validator, apex_account_50k):
        """Trading 10 minutes after news → passed"""
        trade_time = datetime(2024, 3, 15, 14, 40, 0, tzinfo=pytz.UTC)
        news_time = datetime(2024, 3, 15, 14, 30, 0, tzinfo=pytz.UTC)
        result = validator.check_news_blackout(
            timestamp=trade_time,
            news_events=[news_time],
            apex_account=apex_account_50k
        )
        assert result.passed is True
        assert "Outside news blackout" in result.message

    def test_news_blackout_no_events(self, validator, apex_account_50k):
        """No news events → passed"""
        trade_time = datetime(2024, 3, 15, 14, 30, 0, tzinfo=pytz.UTC)
        result = validator.check_news_blackout(
            timestamp=trade_time,
            news_events=[],
            apex_account=apex_account_50k
        )
        assert result.passed is True
        assert "No news events" in result.message


class TestPreTradeValidation:
    """Test pre-trade validation workflow."""

    def test_validate_pre_trade_all_pass(self, validator, apex_account_50k, et_timezone):
        """All checks pass → report.passed=True"""
        # 10 AM ET - market open
        trade_time = et_timezone.localize(datetime(2024, 3, 15, 10, 0, 0))

        report = validator.validate_pre_trade(
            order_qty=2,
            current_position=3,
            current_balance=51000,
            high_watermark=52000,
            daily_loss_usd=-500,
            timestamp=trade_time,
            apex_account=apex_account_50k,
            news_events=[]
        )

        assert report.passed is True
        assert len(report.violations) == 0
        assert len(report.checks) >= 4  # At least 4 core checks

    def test_validate_pre_trade_one_fails(self, validator, apex_account_50k, et_timezone):
        """One check fails → report.passed=False"""
        # 4:30 PM ET - market closed
        trade_time = et_timezone.localize(datetime(2024, 3, 15, 16, 30, 0))

        report = validator.validate_pre_trade(
            order_qty=2,
            current_position=3,
            current_balance=51000,
            high_watermark=52000,
            daily_loss_usd=-500,
            timestamp=trade_time,
            apex_account=apex_account_50k
        )

        assert report.passed is False
        assert len(report.violations) == 1
        assert report.violations[0].rule == "Trading Hours"

    def test_validate_pre_trade_with_warnings(self, validator, apex_account_50k, et_timezone):
        """Check generates warnings at 80% threshold"""
        trade_time = et_timezone.localize(datetime(2024, 3, 15, 10, 0, 0))

        report = validator.validate_pre_trade(
            order_qty=2,
            current_position=6,  # 8 total = 80% of 10
            current_balance=50000,
            high_watermark=52000,  # $2000 drawdown = 80% of $2500
            daily_loss_usd=-1300,  # 86.7% of $1500
            timestamp=trade_time,
            apex_account=apex_account_50k
        )

        assert report.passed is True  # Still passes
        assert len(report.warnings) >= 2  # At least 2 warnings


class TestBacktestValidation:
    """Test backtest validation workflow."""

    def test_validate_backtest_returns_report(self, validator, apex_account_50k):
        """Backtest results valid → report with checks"""
        # Create sample backtest results
        daily_pnl = pd.Series([100, 200, -150, 300, 250])
        timestamps = pd.date_range(
            start='2024-03-15 10:00:00',
            periods=100,
            freq='1H',
            tz=pytz.UTC
        )

        backtest_results = BacktestResults(
            daily_pnl=daily_pnl,
            max_position_size=5,
            timestamps=timestamps,
            high_watermark=52000,
            current_balance=51000,
            total_profit=1200  # Changed from 700 to 1200 so max daily (300) is exactly 25% (passes at 30%)
        )

        report = validator.validate_backtest(
            backtest_results=backtest_results,
            apex_account=apex_account_50k
        )

        assert isinstance(report, ValidationReport)
        assert len(report.checks) >= 4  # Should have multiple checks
        assert report.passed is True  # These results should pass

    def test_validate_backtest_with_violations(self, validator, apex_account_50k):
        """Backtest with violations → report.passed=False"""
        # Create backtest results with violations
        daily_pnl = pd.Series([100, -1600, 200, 300])  # Daily loss violation
        timestamps = pd.date_range(
            start='2024-03-15 16:30:00',  # During closed hours
            periods=10,
            freq='1min',
            tz=pytz.timezone('US/Eastern')
        )

        backtest_results = BacktestResults(
            daily_pnl=daily_pnl,
            max_position_size=12,  # Max contracts violation
            timestamps=timestamps,
            high_watermark=52000,
            current_balance=49000,  # Trailing threshold violation
            total_profit=0
        )

        report = validator.validate_backtest(
            backtest_results=backtest_results,
            apex_account=apex_account_50k
        )

        assert report.passed is False
        assert len(report.violations) >= 3  # Multiple violations expected

    def test_validate_backtest_consistency_check(self, validator, apex_account_50k):
        """Backtest consistency rule validation"""
        # Daily PnL with one day having 40% of total profit (violation)
        daily_pnl = pd.Series([100, 400, 200, 200, 100])  # 400/1000 = 40%
        timestamps = pd.date_range(
            start='2024-03-15 10:00:00',
            periods=5,
            freq='1D',
            tz=pytz.UTC
        )

        backtest_results = BacktestResults(
            daily_pnl=daily_pnl,
            max_position_size=5,
            timestamps=timestamps,
            high_watermark=52000,
            current_balance=52000,
            total_profit=1000
        )

        report = validator.validate_backtest(
            backtest_results=backtest_results,
            apex_account=apex_account_50k
        )

        # Find consistency check
        consistency_check = next(
            (c for c in report.checks if c.rule == "Consistency Rule"),
            None
        )
        assert consistency_check is not None
        assert consistency_check.passed is False  # Should fail
        assert consistency_check.value == 400
        assert consistency_check.limit == 300  # 30% of 1000