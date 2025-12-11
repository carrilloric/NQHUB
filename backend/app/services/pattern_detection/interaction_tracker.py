"""
Pattern Interaction Tracker

Tracks and classifies interactions with patterns using R0-R4, P1-P5 taxonomy.
Based on REBOTE_Y_PENETRACION_CRITERIOS.md
"""
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.patterns import PatternInteraction, DetectedFVG, DetectedLiquidityPool, DetectedOrderBlock


@dataclass
class InteractionResult:
    """Result of interaction classification"""
    interaction_type: str  # R0_CLEAN_BOUNCE, R1_SHALLOW_TOUCH, P4_FALSE_BREAKOUT, etc.
    penetration_pts: float
    penetration_pct: float
    confidence: float
    description: str


class PatternInteractionTracker:
    """
    Pattern Interaction Tracker

    Classifies how price interacts with pattern zones using 10-type taxonomy:

    Bounces (R0-R4):
    - R0: Clean bounce (0-1 pt penetration)
    - R1: Shallow touch (1-3 pts, wick only)
    - R2: Light rejection (3-10 pts, close outside)
    - R3: Medium rejection (10-25% penetration)
    - R4: Deep rejection (25-50% penetration)

    Penetrations (P1-P5):
    - P1: Shallow (25-50%)
    - P2: Deep (50-75%)
    - P3: Full (75-100%)
    - P4: False breakout (break + return)
    - P5: Break and retest (polarity change)
    """

    def __init__(self, db: Session):
        self.db = db

    def classify_interaction(
        self,
        candle_high: float,
        candle_low: float,
        candle_close: float,
        zone_low: float,
        zone_high: float,
        from_direction: str = "BELOW"  # or "ABOVE"
    ) -> InteractionResult:
        """
        Classify interaction with a pattern zone

        Args:
            candle_high: Candle high price
            candle_low: Candle low price
            candle_close: Candle close price
            zone_low: Pattern zone low
            zone_high: Pattern zone high
            from_direction: Approach direction ("BELOW" or "ABOVE")

        Returns:
            InteractionResult with classified type
        """
        zone_size = zone_high - zone_low

        # Check if candle touches zone
        touches_zone = candle_high >= zone_low and candle_low <= zone_high

        if not touches_zone:
            return InteractionResult(
                interaction_type="NO_INTERACTION",
                penetration_pts=0.0,
                penetration_pct=0.0,
                confidence=0.0,
                description="Price did not touch the zone"
            )

        # Calculate penetration
        if from_direction == "BELOW":
            # Testing zone as support/resistance from below
            penetration_pts = max(0, candle_high - zone_low)
            if zone_size > 0:
                penetration_pct = (penetration_pts / zone_size) * 100
            else:
                penetration_pct = 0

            # Check if close is outside zone
            close_outside = candle_close < zone_low

        else:  # from_direction == "ABOVE"
            # Testing zone from above
            penetration_pts = max(0, zone_high - candle_low)
            if zone_size > 0:
                penetration_pct = (penetration_pts / zone_size) * 100
            else:
                penetration_pct = 0

            close_outside = candle_close > zone_high

        # Classify based on penetration and close location

        # R0: Clean Bounce (0-1 pt)
        if penetration_pts <= 1.0:
            return InteractionResult(
                interaction_type="R0_CLEAN_BOUNCE",
                penetration_pts=penetration_pts,
                penetration_pct=penetration_pct,
                confidence=0.90,
                description="Perfect bounce with minimal penetration"
            )

        # R1: Shallow Touch (1-3 pts, wick only)
        elif penetration_pts <= 3.0 and close_outside:
            return InteractionResult(
                interaction_type="R1_SHALLOW_TOUCH",
                penetration_pts=penetration_pts,
                penetration_pct=penetration_pct,
                confidence=0.80,
                description="Shallow penetration, closed outside zone"
            )

        # R2: Light Rejection (3-10 pts or <25%, close outside)
        elif (penetration_pts <= 10.0 or penetration_pct < 25) and close_outside:
            return InteractionResult(
                interaction_type="R2_LIGHT_REJECTION",
                penetration_pts=penetration_pts,
                penetration_pct=penetration_pct,
                confidence=0.70,
                description="Light penetration with rejection"
            )

        # R3: Medium Rejection (25-50%, with rejection wick)
        elif penetration_pct >= 25 and penetration_pct < 50:
            wick_size = abs(candle_high - candle_close) if from_direction == "BELOW" else abs(candle_close - candle_low)
            has_rejection_wick = wick_size > zone_size * 0.3

            if has_rejection_wick:
                return InteractionResult(
                    interaction_type="R3_MEDIUM_REJECTION",
                    penetration_pts=penetration_pts,
                    penetration_pct=penetration_pct,
                    confidence=0.60,
                    description="Medium penetration with rejection wick"
                )

        # R4: Deep Rejection (50-75%)
        elif penetration_pct >= 50 and penetration_pct < 75 and close_outside:
            return InteractionResult(
                interaction_type="R4_DEEP_REJECTION",
                penetration_pts=penetration_pts,
                penetration_pct=penetration_pct,
                confidence=0.50,
                description="Deep penetration but still rejected"
            )

        # P1: Shallow Penetration (25-50%, close inside)
        elif penetration_pct >= 25 and penetration_pct < 50 and not close_outside:
            return InteractionResult(
                interaction_type="P1_SHALLOW_PENETRATION",
                penetration_pts=penetration_pts,
                penetration_pct=penetration_pct,
                confidence=0.40,
                description="Shallow penetration, closed inside"
            )

        # P2: Deep Penetration (50-75%)
        elif penetration_pct >= 50 and penetration_pct < 75:
            return InteractionResult(
                interaction_type="P2_DEEP_PENETRATION",
                penetration_pts=penetration_pts,
                penetration_pct=penetration_pct,
                confidence=0.30,
                description="Deep penetration into zone"
            )

        # P3: Full Penetration (75-100%)
        elif penetration_pct >= 75:
            return InteractionResult(
                interaction_type="P3_FULL_PENETRATION",
                penetration_pts=penetration_pts,
                penetration_pct=penetration_pct,
                confidence=0.20,
                description="Zone mostly filled/penetrated"
            )

        # Default: classify as light rejection
        return InteractionResult(
            interaction_type="R2_LIGHT_REJECTION",
            penetration_pts=penetration_pts,
            penetration_pct=penetration_pct,
            confidence=0.65,
            description="Default classification"
        )

    def track_fvg_interactions(
        self,
        fvg_id: int,
        timeframe: str = "5min"
    ) -> List[PatternInteraction]:
        """
        Track interactions with a specific FVG

        Args:
            fvg_id: FVG ID to track
            timeframe: Candle timeframe

        Returns:
            List of PatternInteraction records
        """
        # Get FVG
        fvg = self.db.query(DetectedFVG).filter(DetectedFVG.fvg_id == fvg_id).first()
        if not fvg:
            return []

        # Get candles after FVG formation
        table_name = f"candlestick_{timeframe}"
        query = text(f"""
            SELECT
                time_interval AT TIME ZONE 'America/New_York' as et_time,
                high, low, close
            FROM {table_name}
            WHERE symbol = :symbol
              AND time_interval > :formation_time
              AND time_interval <= :formation_time + INTERVAL '48 hours'
              -- Only candles that touch the FVG zone
              AND NOT (high < :zone_low OR low > :zone_high)
            ORDER BY time_interval
        """)

        result = self.db.execute(query, {
            "symbol": fvg.symbol,
            "formation_time": fvg.formation_time,
            "zone_low": fvg.fvg_start,
            "zone_high": fvg.fvg_end
        })

        # Classify each interaction
        interactions = []
        for row in result:
            from_direction = "BELOW" if fvg.fvg_type == "BULLISH" else "ABOVE"

            classification = self.classify_interaction(
                candle_high=row.high,
                candle_low=row.low,
                candle_close=row.close,
                zone_low=fvg.fvg_start,
                zone_high=fvg.fvg_end,
                from_direction=from_direction
            )

            if classification.interaction_type != "NO_INTERACTION":
                interaction = PatternInteraction(
                    pattern_type="FVG",
                    pattern_id=fvg_id,
                    interaction_time=row.et_time,
                    interaction_type=classification.interaction_type,
                    penetration_pts=classification.penetration_pts,
                    penetration_pct=classification.penetration_pct,
                    confidence=classification.confidence,
                    candle_high=row.high,
                    candle_low=row.low,
                    candle_close=row.close
                )
                interactions.append(interaction)

        return interactions

    def track_lp_interactions(
        self,
        lp_id: int,
        timeframe: str = "5min"
    ) -> List[PatternInteraction]:
        """Track interactions with a Liquidity Pool"""
        # Get LP
        lp = self.db.query(DetectedLiquidityPool).filter(DetectedLiquidityPool.lp_id == lp_id).first()
        if not lp:
            return []

        zone_low = lp.level - lp.tolerance
        zone_high = lp.level + lp.tolerance

        table_name = f"candlestick_{timeframe}"
        query = text(f"""
            SELECT
                time_interval AT TIME ZONE 'America/New_York' as et_time,
                high, low, close
            FROM {table_name}
            WHERE symbol = :symbol
              AND time_interval > :formation_time
              AND time_interval <= :formation_time + INTERVAL '48 hours'
              AND NOT (high < :zone_low OR low > :zone_high)
            ORDER BY time_interval
        """)

        result = self.db.execute(query, {
            "symbol": lp.symbol,
            "formation_time": lp.formation_time,
            "zone_low": zone_low,
            "zone_high": zone_high
        })

        interactions = []
        for row in result:
            # Determine direction based on pool type
            from_direction = "BELOW" if "H" in lp.pool_type else "ABOVE"  # Highs from below, Lows from above

            classification = self.classify_interaction(
                candle_high=row.high,
                candle_low=row.low,
                candle_close=row.close,
                zone_low=zone_low,
                zone_high=zone_high,
                from_direction=from_direction
            )

            if classification.interaction_type != "NO_INTERACTION":
                interaction = PatternInteraction(
                    pattern_type="LP",
                    pattern_id=lp_id,
                    interaction_time=row.et_time,
                    interaction_type=classification.interaction_type,
                    penetration_pts=classification.penetration_pts,
                    penetration_pct=classification.penetration_pct,
                    confidence=classification.confidence,
                    candle_high=row.high,
                    candle_low=row.low,
                    candle_close=row.close
                )
                interactions.append(interaction)

        return interactions

    def track_ob_interactions(
        self,
        ob_id: int,
        timeframe: str = "5min"
    ) -> List[PatternInteraction]:
        """Track interactions with an Order Block"""
        # Get OB
        ob = self.db.query(DetectedOrderBlock).filter(DetectedOrderBlock.ob_id == ob_id).first()
        if not ob:
            return []

        table_name = f"candlestick_{timeframe}"
        query = text(f"""
            SELECT
                time_interval AT TIME ZONE 'America/New_York' as et_time,
                high, low, close
            FROM {table_name}
            WHERE symbol = :symbol
              AND time_interval > :formation_time
              AND time_interval <= :formation_time + INTERVAL '48 hours'
              AND NOT (high < :zone_low OR low > :zone_high)
            ORDER BY time_interval
        """)

        result = self.db.execute(query, {
            "symbol": ob.symbol,
            "formation_time": ob.formation_time,
            "zone_low": ob.ob_low,
            "zone_high": ob.ob_high
        })

        interactions = []
        for row in result:
            from_direction = "BELOW" if "BULLISH" in ob.ob_type else "ABOVE"

            classification = self.classify_interaction(
                candle_high=row.high,
                candle_low=row.low,
                candle_close=row.close,
                zone_low=ob.ob_low,
                zone_high=ob.ob_high,
                from_direction=from_direction
            )

            if classification.interaction_type != "NO_INTERACTION":
                interaction = PatternInteraction(
                    pattern_type="OB",
                    pattern_id=ob_id,
                    interaction_time=row.et_time,
                    interaction_type=classification.interaction_type,
                    penetration_pts=classification.penetration_pts,
                    penetration_pct=classification.penetration_pct,
                    confidence=classification.confidence,
                    candle_high=row.high,
                    candle_low=row.low,
                    candle_close=row.close
                )
                interactions.append(interaction)

        return interactions

    def update_pattern_status(
        self,
        pattern_type: str,
        pattern_id: int,
        interactions: List[PatternInteraction]
    ):
        """
        Update pattern status based on interactions

        Args:
            pattern_type: FVG, LP, or OB
            pattern_id: Pattern ID
            interactions: List of interactions

        Updates status to FILLED, BROKEN, or keeps as UNMITIGATED/ACTIVE
        """
        if not interactions:
            return

        # Check for P3 (full penetration) or worse
        has_full_penetration = any(
            i.interaction_type in ["P3_FULL_PENETRATION", "P4_FALSE_BREAKOUT", "P5_BREAK_AND_RETEST"]
            for i in interactions
        )

        if pattern_type == "FVG":
            fvg = self.db.query(DetectedFVG).filter(DetectedFVG.fvg_id == pattern_id).first()
            if fvg and has_full_penetration:
                fvg.status = "FILLED"
                self.db.commit()

        elif pattern_type == "LP":
            lp = self.db.query(DetectedLiquidityPool).filter(DetectedLiquidityPool.lp_id == pattern_id).first()
            if lp and has_full_penetration:
                lp.status = "SWEPT"
                self.db.commit()

        elif pattern_type == "OB":
            ob = self.db.query(DetectedOrderBlock).filter(DetectedOrderBlock.ob_id == pattern_id).first()
            if ob and has_full_penetration:
                ob.status = "BROKEN"
                self.db.commit()
