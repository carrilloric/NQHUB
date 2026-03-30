"""
Kill Zone Detector

Detects ICT Kill Zones (high-probability trading windows) using smartmoneyconcepts.
"""

import pandas as pd
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from typing import List, Optional, Tuple
import pytz

try:
    from smartmoneyconcepts import smc
except ImportError:
    import warnings
    warnings.warn("smartmoneyconcepts not installed. Some features will be limited.")
    smc = None


@dataclass
class KillZone:
    """
    Kill Zone trading session

    Represents specific time windows where institutional trading activity is highest.
    """
    name: str
    start_time: time  # ET time
    end_time: time    # ET time
    description: str
    is_active: bool = False  # Currently active?
    session_type: str = "standard"  # standard, custom, or smc

    def __repr__(self) -> str:
        status = "ACTIVE" if self.is_active else "inactive"
        return (f"KillZone({self.name}, "
                f"{self.start_time.strftime('%H:%M')}-{self.end_time.strftime('%H:%M')} ET, "
                f"{status})")


# ICT-defined Kill Zones (all times in ET)
ICT_KILL_ZONES = [
    KillZone(
        "London Open",
        time(2, 0),
        time(5, 0),
        "London market open - high volatility period",
        session_type="smc"
    ),
    KillZone(
        "NY AM Session",
        time(8, 30),
        time(11, 0),
        "Primary New York session - highest volume",
        session_type="smc"
    ),
    KillZone(
        "Silver Bullet",
        time(10, 0),
        time(11, 0),
        "ICT's specific 1-hour window for high-probability setups",
        session_type="custom"
    ),
    KillZone(
        "NY Lunch",
        time(12, 0),
        time(13, 0),
        "Low liquidity period - avoid trading",
        session_type="standard"
    ),
    KillZone(
        "NY PM Session",
        time(13, 30),
        time(16, 0),
        "Secondary New York session",
        session_type="smc"
    ),
    KillZone(
        "London Close",
        time(10, 0),
        time(12, 0),
        "London market close - potential reversals",
        session_type="smc"
    ),
]


class KillZoneDetector:
    """
    Detects and manages ICT Kill Zones using smartmoneyconcepts library.

    Combines SMC sessions with custom ICT-specific sessions like Silver Bullet.
    """

    def __init__(self, timezone_str: str = "America/New_York"):
        """
        Initialize Kill Zone detector.

        Args:
            timezone_str: Timezone for kill zones (default ET)
        """
        self.timezone = pytz.timezone(timezone_str)
        self.kill_zones = ICT_KILL_ZONES.copy()

    def get_active_kill_zones(self, timestamp: datetime) -> List[KillZone]:
        """
        Get all active kill zones at the given timestamp.

        Args:
            timestamp: Datetime to check (will be converted to ET)

        Returns:
            List of currently active KillZone objects
        """
        # Convert to ET if needed
        if timestamp.tzinfo is None:
            # Assume UTC if naive
            timestamp = pytz.UTC.localize(timestamp)

        et_time = timestamp.astimezone(self.timezone)
        current_time = et_time.time()

        active_zones = []
        for zone in self.kill_zones:
            if self._is_time_in_zone(current_time, zone.start_time, zone.end_time):
                zone_copy = KillZone(
                    name=zone.name,
                    start_time=zone.start_time,
                    end_time=zone.end_time,
                    description=zone.description,
                    is_active=True,
                    session_type=zone.session_type
                )
                active_zones.append(zone_copy)

        return active_zones

    def is_in_kill_zone(self, timestamp: datetime, zone_name: Optional[str] = None) -> bool:
        """
        Check if timestamp falls within any kill zone (or specific one).

        Args:
            timestamp: Datetime to check
            zone_name: Optional specific zone name to check

        Returns:
            True if in kill zone, False otherwise
        """
        active_zones = self.get_active_kill_zones(timestamp)

        if zone_name:
            return any(z.name == zone_name for z in active_zones)
        else:
            # Exclude "NY Lunch" as it's a zone to avoid
            return any(z.name != "NY Lunch" for z in active_zones)

    def time_to_next_kill_zone(self, timestamp: datetime) -> Tuple[Optional[KillZone], timedelta]:
        """
        Get the next kill zone and time until it starts.

        Args:
            timestamp: Current datetime

        Returns:
            Tuple of (next KillZone, timedelta until start)
        """
        # Convert to ET
        if timestamp.tzinfo is None:
            timestamp = pytz.UTC.localize(timestamp)

        et_time = timestamp.astimezone(self.timezone)
        current_time = et_time.time()
        current_date = et_time.date()

        next_zone = None
        min_delta = timedelta(days=1)  # Max possible delta

        for zone in self.kill_zones:
            # Skip NY Lunch (avoid zone)
            if zone.name == "NY Lunch":
                continue

            # Calculate time until this zone starts
            zone_datetime = datetime.combine(current_date, zone.start_time)
            zone_datetime = self.timezone.localize(zone_datetime)

            # If zone already passed today, check tomorrow
            if zone_datetime <= et_time:
                zone_datetime += timedelta(days=1)

            delta = zone_datetime - et_time

            if delta < min_delta:
                min_delta = delta
                next_zone = zone

        return next_zone, min_delta

    def apply_smc_sessions(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply SMC session detection to price data.

        Uses smartmoneyconcepts.sessions() for standard kill zones.

        Args:
            df: DataFrame with datetime index

        Returns:
            DataFrame with session columns added
        """
        if smc is None:
            # Fallback - just add manual session columns
            return self._apply_manual_sessions(df)

        df_copy = df.copy()

        # Apply SMC sessions for standard zones
        smc_sessions = [
            ("Asian kill zone", "00:00", "08:30"),
            ("London open kill zone", "02:00", "05:00"),
            ("New York kill zone", "08:30", "16:00"),
            ("London close kill zone", "10:00", "12:00"),
        ]

        for session_name, start, end in smc_sessions:
            try:
                session_data = smc.sessions(
                    df_copy,
                    session=session_name,
                    start_time=start,
                    end_time=end,
                    time_zone="America/New_York"
                )
                df_copy[f'{session_name.replace(" ", "_")}'] = session_data
            except Exception as e:
                print(f"Warning: Could not apply {session_name}: {e}")

        # Add custom Silver Bullet session
        df_copy['silver_bullet'] = self._detect_silver_bullet(df_copy)

        return df_copy

    def _detect_silver_bullet(self, df: pd.DataFrame) -> pd.Series:
        """
        Detect Silver Bullet session (10:00-11:00 ET).

        Args:
            df: DataFrame with datetime index

        Returns:
            Boolean series indicating Silver Bullet periods
        """
        silver_bullet = pd.Series(False, index=df.index)

        for idx, row in df.iterrows():
            if isinstance(idx, pd.Timestamp):
                dt = idx.to_pydatetime()
            else:
                dt = row['datetime'] if 'datetime' in row else idx

            # Convert to ET
            if dt.tzinfo is None:
                dt = pytz.UTC.localize(dt)
            et_time = dt.astimezone(self.timezone)

            # Check if in Silver Bullet window
            if time(10, 0) <= et_time.time() <= time(11, 0):
                silver_bullet[idx] = True

        return silver_bullet

    def _apply_manual_sessions(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Manually apply session detection without SMC.

        Fallback method when smartmoneyconcepts is not available.

        Args:
            df: DataFrame with datetime index

        Returns:
            DataFrame with session columns added
        """
        df_copy = df.copy()

        for zone in self.kill_zones:
            col_name = zone.name.lower().replace(" ", "_")
            df_copy[col_name] = False

            for idx, row in df.iterrows():
                if isinstance(idx, pd.Timestamp):
                    dt = idx.to_pydatetime()
                else:
                    dt = row['datetime'] if 'datetime' in row else idx

                # Convert to ET
                if dt.tzinfo is None:
                    dt = pytz.UTC.localize(dt)
                et_time = dt.astimezone(self.timezone)

                # Check if in this zone
                if self._is_time_in_zone(et_time.time(), zone.start_time, zone.end_time):
                    df_copy.loc[idx, col_name] = True

        return df_copy

    def _is_time_in_zone(self, current: time, start: time, end: time) -> bool:
        """
        Check if a time falls within a zone.

        Handles zones that cross midnight.

        Args:
            current: Current time
            start: Zone start time
            end: Zone end time

        Returns:
            True if current is within zone
        """
        if start <= end:
            # Normal case (doesn't cross midnight)
            return start <= current <= end
        else:
            # Crosses midnight
            return current >= start or current <= end

    def get_session_statistics(self, df: pd.DataFrame, zone_name: str) -> dict:
        """
        Get trading statistics for a specific kill zone.

        Args:
            df: DataFrame with price data and session columns
            zone_name: Name of the kill zone

        Returns:
            Dictionary with session statistics
        """
        col_name = zone_name.lower().replace(" ", "_")

        if col_name not in df.columns:
            # Apply sessions first
            df = self.apply_smc_sessions(df)

        if col_name not in df.columns:
            return {"error": f"Kill zone {zone_name} not found"}

        # Filter for this session
        session_data = df[df[col_name] == True]

        if len(session_data) == 0:
            return {"error": f"No data for {zone_name}"}

        stats = {
            "zone_name": zone_name,
            "total_candles": len(session_data),
            "avg_range": (session_data['high'] - session_data['low']).mean(),
            "avg_volume": session_data['volume'].mean() if 'volume' in session_data.columns else 0,
            "volatility": session_data['close'].pct_change().std() if len(session_data) > 1 else 0,
            "high": session_data['high'].max(),
            "low": session_data['low'].min(),
        }

        return stats