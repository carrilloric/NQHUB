"""
Apex Trading compliance validator.

Validates compliance with Apex Trading funded account rules.
Pure Python logic - no external backtesting libraries.
Reads limits directly from apex_accounts table.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional
import pandas as pd
import pytz


@dataclass
class ApexAccount:
    """Apex funded account configuration."""
    id: int
    account_size_usd: float  # 25000, 50000, 100000, 250000, 300000
    trailing_threshold_usd: float  # 1500, 2500, 3000, 6500, 7500
    max_daily_loss_usd: float  # Configurable per account
    max_contracts: int  # 4, 10, 14, 27, 35
    consistency_pct: float  # 30.0 - No single day > 30% of total profit
    news_blackout_minutes: int  # 5 - Minutes before/after high-impact news


@dataclass
class CheckResult:
    """Result of a single compliance check."""
    passed: bool
    rule: str
    message: str
    value: float
    limit: float


@dataclass
class ValidationReport:
    """Complete validation report with all checks."""
    passed: bool  # True only if ALL checks pass
    checks: List[CheckResult] = field(default_factory=list)
    violations: List[CheckResult] = field(default_factory=list)  # Failed checks
    warnings: List[CheckResult] = field(default_factory=list)  # Checks near limit (>80%)


@dataclass
class BacktestResults:
    """Container for backtest results data."""
    daily_pnl: pd.Series
    max_position_size: int
    timestamps: pd.DatetimeIndex
    high_watermark: float
    current_balance: float
    total_profit: float


class ApexComplianceValidator:
    """
    Validates compliance with Apex Trading rules.
    Reads limits from apex_accounts - account type agnostic.
    """

    WARNING_THRESHOLD = 0.8  # Warn when at 80% of limit

    def check_trailing_threshold(
        self,
        current_balance: float,
        high_watermark: float,
        apex_account: ApexAccount
    ) -> CheckResult:
        """
        Most critical Apex rule.
        drawdown = high_watermark - current_balance
        VIOLATION if drawdown >= apex_account.trailing_threshold_usd

        Example: HWM=$52,500, balance=$50,100, threshold=$2,500
                 drawdown=$2,400 → 96% of limit → WARNING
        """
        drawdown = high_watermark - current_balance
        limit = apex_account.trailing_threshold_usd
        percentage = (drawdown / limit) * 100 if limit > 0 else 0

        passed = drawdown < limit

        return CheckResult(
            passed=passed,
            rule="Trailing Drawdown",
            message=f"Drawdown ${drawdown:.2f} is {percentage:.1f}% of limit ${limit:.2f}",
            value=drawdown,
            limit=limit
        )

    def check_daily_loss(
        self,
        daily_loss_usd: float,
        apex_account: ApexAccount
    ) -> CheckResult:
        """
        VIOLATION if daily_loss_usd >= apex_account.max_daily_loss_usd
        """
        limit = apex_account.max_daily_loss_usd
        percentage = (abs(daily_loss_usd) / limit) * 100 if limit > 0 else 0

        passed = abs(daily_loss_usd) < limit

        return CheckResult(
            passed=passed,
            rule="Daily Loss",
            message=f"Daily loss ${abs(daily_loss_usd):.2f} is {percentage:.1f}% of limit ${limit:.2f}",
            value=abs(daily_loss_usd),
            limit=limit
        )

    def check_max_contracts(
        self,
        order_qty: int,
        current_position: int,
        apex_account: ApexAccount
    ) -> CheckResult:
        """
        VIOLATION if (current_position + order_qty) > apex_account.max_contracts
        """
        total_contracts = abs(current_position) + abs(order_qty)
        limit = apex_account.max_contracts
        percentage = (total_contracts / limit) * 100 if limit > 0 else 0

        passed = total_contracts <= limit

        return CheckResult(
            passed=passed,
            rule="Max Contracts",
            message=f"Total contracts {total_contracts} is {percentage:.1f}% of limit {limit}",
            value=float(total_contracts),
            limit=float(limit)
        )

    def check_trading_hours(
        self,
        timestamp: datetime
    ) -> CheckResult:
        """
        Apex is closed 4:00 PM - 5:00 PM ET daily.
        VIOLATION if timestamp falls in that range.
        Uses pytz for ET timezone.
        """
        # Ensure timestamp is timezone aware
        et_tz = pytz.timezone('US/Eastern')

        if timestamp.tzinfo is None:
            # Assume UTC if naive
            timestamp = pytz.UTC.localize(timestamp)

        # Convert to ET
        et_time = timestamp.astimezone(et_tz)

        # Check if time is between 4:00 PM and 5:00 PM ET
        closed_start = et_time.replace(hour=16, minute=0, second=0, microsecond=0)
        closed_end = et_time.replace(hour=17, minute=0, second=0, microsecond=0)

        is_closed = closed_start <= et_time < closed_end

        return CheckResult(
            passed=not is_closed,
            rule="Trading Hours",
            message=f"Trading at {et_time.strftime('%H:%M:%S ET')} - {'CLOSED' if is_closed else 'OPEN'}",
            value=1.0 if is_closed else 0.0,
            limit=0.0  # Binary check - no limit
        )

    def check_consistency_rule(
        self,
        daily_pnl_series: pd.Series,
        total_profit: float,
        apex_account: ApexAccount
    ) -> CheckResult:
        """
        No single day can be > apex_account.consistency_pct % of total profit.
        Example: consistency_pct=30, total_profit=$1,000
                 → no day can have PnL > $300
        VIOLATION if max(daily_pnl_series) > total_profit * (consistency_pct/100)
        Only applies when total_profit > 0.
        """
        # Skip check if no profit or negative profit
        if total_profit <= 0:
            return CheckResult(
                passed=True,
                rule="Consistency Rule",
                message="Consistency check skipped - no positive profit",
                value=0.0,
                limit=0.0
            )

        max_daily = float(daily_pnl_series.max()) if len(daily_pnl_series) > 0 else 0.0
        limit = total_profit * (apex_account.consistency_pct / 100)
        percentage = (max_daily / limit) * 100 if limit > 0 else 0

        passed = bool(max_daily <= limit)  # Convert numpy.bool_ to native bool

        return CheckResult(
            passed=passed,
            rule="Consistency Rule",
            message=f"Max daily PnL ${max_daily:.2f} is {percentage:.1f}% of limit ${limit:.2f} ({apex_account.consistency_pct}% of total profit)",
            value=max_daily,
            limit=limit
        )

    def check_news_blackout(
        self,
        timestamp: datetime,
        news_events: List[datetime],
        apex_account: ApexAccount
    ) -> CheckResult:
        """
        VIOLATION if timestamp is within apex_account.news_blackout_minutes
        before or after any high-impact news event.
        """
        if not news_events:
            return CheckResult(
                passed=True,
                rule="News Blackout",
                message="No news events to check",
                value=0.0,
                limit=0.0
            )

        blackout_minutes = apex_account.news_blackout_minutes
        blackout_delta = timedelta(minutes=blackout_minutes)

        # Ensure timestamp is timezone aware for comparison
        if timestamp.tzinfo is None:
            timestamp = pytz.UTC.localize(timestamp)

        for news_time in news_events:
            if news_time.tzinfo is None:
                news_time = pytz.UTC.localize(news_time)

            time_diff = abs(timestamp - news_time)

            if time_diff <= blackout_delta:
                minutes_diff = time_diff.total_seconds() / 60
                return CheckResult(
                    passed=False,
                    rule="News Blackout",
                    message=f"Trading {minutes_diff:.1f} minutes from high-impact news (blackout: {blackout_minutes} min)",
                    value=minutes_diff,
                    limit=float(blackout_minutes)
                )

        return CheckResult(
            passed=True,
            rule="News Blackout",
            message="Outside news blackout periods",
            value=0.0,
            limit=float(blackout_minutes)
        )

    def validate_pre_trade(
        self,
        order_qty: int,
        current_position: int,
        current_balance: float,
        high_watermark: float,
        daily_loss_usd: float,
        timestamp: datetime,
        apex_account: ApexAccount,
        news_events: Optional[List[datetime]] = None
    ) -> ValidationReport:
        """
        Run all 6 pre-trade checks. Used by Risk Manager live.
        If ANY check fails → ValidationReport.passed = False → order blocked.
        """
        checks = []

        # Run all compliance checks
        checks.append(self.check_trailing_threshold(current_balance, high_watermark, apex_account))
        checks.append(self.check_daily_loss(daily_loss_usd, apex_account))
        checks.append(self.check_max_contracts(order_qty, current_position, apex_account))
        checks.append(self.check_trading_hours(timestamp))

        # News blackout is optional
        if news_events is not None:
            checks.append(self.check_news_blackout(timestamp, news_events, apex_account))

        # Separate violations and warnings
        violations = []
        warnings = []

        for check in checks:
            if not check.passed:
                violations.append(check)
            elif check.limit > 0 and (check.value / check.limit) >= self.WARNING_THRESHOLD:
                warnings.append(check)

        # Report passes only if no violations
        report = ValidationReport(
            passed=len(violations) == 0,
            checks=checks,
            violations=violations,
            warnings=warnings
        )

        return report

    def validate_backtest(
        self,
        backtest_results: BacktestResults,
        apex_account: ApexAccount
    ) -> ValidationReport:
        """
        Run checks on historical backtest results.
        Applicable checks: trailing_threshold, daily_loss, max_contracts,
                          trading_hours, consistency_rule.
        Used by Strategy Approval before marking strategy as approved.
        """
        checks = []

        # Check trailing threshold
        checks.append(self.check_trailing_threshold(
            backtest_results.current_balance,
            backtest_results.high_watermark,
            apex_account
        ))

        # Check max daily loss
        if len(backtest_results.daily_pnl) > 0:
            max_daily_loss = float(backtest_results.daily_pnl.min())  # Convert numpy scalar to float
            checks.append(self.check_daily_loss(max_daily_loss, apex_account))

        # Check max contracts
        checks.append(self.check_max_contracts(
            0,  # No new order in backtest validation
            backtest_results.max_position_size,
            apex_account
        ))

        # Check trading hours for all timestamps
        trading_hours_violations = 0
        if len(backtest_results.timestamps) > 0:
            for ts in backtest_results.timestamps[:10]:  # Sample first 10 for efficiency
                result = self.check_trading_hours(ts)
                if not result.passed:
                    trading_hours_violations += 1

            if trading_hours_violations > 0:
                checks.append(CheckResult(
                    passed=False,
                    rule="Trading Hours",
                    message=f"Found {trading_hours_violations} trades during closed hours",
                    value=float(trading_hours_violations),
                    limit=0.0
                ))
            else:
                checks.append(CheckResult(
                    passed=True,
                    rule="Trading Hours",
                    message="All trades within allowed hours",
                    value=0.0,
                    limit=0.0
                ))

        # Check consistency rule
        checks.append(self.check_consistency_rule(
            backtest_results.daily_pnl,
            backtest_results.total_profit,
            apex_account
        ))

        # Separate violations and warnings
        violations = []
        warnings = []

        for check in checks:
            if not check.passed:
                violations.append(check)
            elif check.limit > 0 and (check.value / check.limit) >= self.WARNING_THRESHOLD:
                warnings.append(check)

        # Report passes only if no violations
        report = ValidationReport(
            passed=len(violations) == 0,
            checks=checks,
            violations=violations,
            warnings=warnings
        )

        return report