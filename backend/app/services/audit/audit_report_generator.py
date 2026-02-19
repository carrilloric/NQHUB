"""
Audit Report Generator

Generates markdown reports for validating detected patterns against ATAS.
"""
from datetime import datetime
from typing import List
import pytz
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.patterns import DetectedOrderBlock
from app.schemas.audit import OrderBlockAuditItem, AuditOrderBlocksResponse


class AuditReportGenerator:
    """
    Generates audit reports for pattern validation

    Currently supports:
    - Order Blocks (Fase 1)

    Future:
    - FVGs (Fase 2)
    - Session Levels (Fase 3)
    - All Patterns (Fase 4)
    """

    def __init__(self, db: Session):
        self.db = db

    def generate_order_blocks_audit(
        self,
        symbol: str,
        timeframe: str,
        snapshot_time: datetime  # UTC
    ) -> AuditOrderBlocksResponse:
        """
        Generate audit report for Order Blocks at a specific timestamp

        Args:
            symbol: Trading symbol (e.g., "NQZ5")
            timeframe: Candle timeframe (e.g., "5min")
            snapshot_time: Snapshot timestamp (UTC naive or aware)

        Returns:
            AuditOrderBlocksResponse with markdown report and OB details
        """
        # Ensure snapshot_time is UTC aware
        if snapshot_time.tzinfo is None:
            snapshot_time = snapshot_time.replace(tzinfo=pytz.UTC)

        # Query ACTIVE Order Blocks at snapshot_time
        active_obs = self.db.query(DetectedOrderBlock).filter(
            and_(
                DetectedOrderBlock.symbol == symbol,
                DetectedOrderBlock.timeframe == timeframe,
                DetectedOrderBlock.formation_time <= snapshot_time,
                DetectedOrderBlock.status == "ACTIVE"
            )
        ).order_by(DetectedOrderBlock.formation_time.desc()).all()

        # Convert to audit items
        audit_items: List[OrderBlockAuditItem] = []
        for ob in active_obs:
            audit_items.append(self._ob_to_audit_item(ob))

        # Generate markdown report
        report_markdown = self._generate_markdown_report(
            symbol=symbol,
            timeframe=timeframe,
            snapshot_time=snapshot_time,
            audit_items=audit_items
        )

        # Format snapshot time in EST
        eastern = pytz.timezone('America/New_York')
        snapshot_time_est_obj = snapshot_time.astimezone(eastern)
        snapshot_time_est = snapshot_time_est_obj.strftime('%b %d, %Y %H:%M:%S %Z')

        return AuditOrderBlocksResponse(
            report_markdown=report_markdown,
            total_obs=len(audit_items),
            snapshot_time_est=snapshot_time_est,
            snapshot_time_utc=snapshot_time.strftime('%Y-%m-%d %H:%M:%S UTC'),
            symbol=symbol,
            timeframe=timeframe,
            order_blocks=audit_items
        )

    def _ob_to_audit_item(self, ob: DetectedOrderBlock) -> OrderBlockAuditItem:
        """Convert DetectedOrderBlock to OrderBlockAuditItem"""
        eastern = pytz.timezone('America/New_York')

        # Ensure formation_time is aware
        formation_time_utc = ob.formation_time
        if formation_time_utc.tzinfo is None:
            formation_time_utc = formation_time_utc.replace(tzinfo=pytz.UTC)

        # Convert to EST
        formation_time_est_obj = formation_time_utc.astimezone(eastern)
        formation_time_est = formation_time_est_obj.strftime('%b %d, %Y %H:%M:%S %Z')
        formation_time_utc_str = formation_time_utc.strftime('%Y-%m-%d %H:%M:%S UTC')

        return OrderBlockAuditItem(
            ob_id=ob.ob_id,
            ob_type=ob.ob_type,
            formation_time_est=formation_time_est,
            formation_time_utc=formation_time_utc_str,
            zone_low=ob.ob_low,
            zone_high=ob.ob_high,
            body_midpoint=ob.ob_body_midpoint,
            range_midpoint=ob.ob_range_midpoint,
            status=ob.status,
            quality=ob.quality,
            impulse_move=ob.impulse_move,
            impulse_direction=ob.impulse_direction,
            candle_direction=ob.candle_direction,
            ob_open=ob.ob_open,
            ob_close=ob.ob_close,
            ob_volume=ob.ob_volume
        )

    def _generate_markdown_report(
        self,
        symbol: str,
        timeframe: str,
        snapshot_time: datetime,
        audit_items: List[OrderBlockAuditItem]
    ) -> str:
        """Generate markdown formatted audit report"""
        eastern = pytz.timezone('America/New_York')
        snapshot_time_est_obj = snapshot_time.astimezone(eastern)
        snapshot_time_est = snapshot_time_est_obj.strftime('%b %d, %Y %H:%M:%S %Z')

        report = f"""# 🔍 AUDIT REPORT - Order Blocks

**Symbol:** {symbol} | **Timeframe:** {timeframe} | **Timestamp:** {snapshot_time_est}

---

## 📦 Order Blocks Activos ({len(audit_items)})

"""

        if not audit_items:
            report += "**No hay Order Blocks activos en este timestamp.**\n"
            report += "\nEsto significa que todos los OBs han sido invalidados (BROKEN) o probados (TESTED).\n"
            return report

        # Add each OB
        for i, item in enumerate(audit_items, 1):
            # Determine candle color for ATAS instructions
            candle_color = "🟢 ALCISTA (verde)" if item.candle_direction == "BULLISH" else "🔴 BAJISTA (roja)"

            # Determine expected behavior
            if "BULLISH" in item.ob_type:
                expected_behavior = "SOPORTE"
                expected_action = "rebote alcista"
            else:
                expected_behavior = "RESISTENCIA"
                expected_action = "rebote bajista"

            # Format impulse with sign
            impulse_sign = "+" if item.impulse_move > 0 else ""

            report += f"""### OB #{item.ob_id} - {item.ob_type} @ {item.formation_time_est}

| Campo | Valor |
|-------|-------|
| **Zona** | {item.zone_low:,.2f} - {item.zone_high:,.2f} |
| **Body Midpoint (50%)** | {item.body_midpoint:,.2f} |
| **Range Midpoint (50%)** | {item.range_midpoint:,.2f} |
| **Status** | {item.status} |
| **Quality** | {item.quality} |
| **Impulse** | {impulse_sign}{item.impulse_move:.2f} pts ({item.impulse_direction}) |
| **Candle Direction** | {item.candle_direction} |
| **OHLC** | O: {item.ob_open:,.2f} / H: {item.zone_high:,.2f} / L: {item.zone_low:,.2f} / C: {item.ob_close:,.2f} |
| **Volume** | {item.ob_volume:,.0f} contratos |

**✅ Para validar en ATAS:**

1. **Abrir chart {timeframe} en ATAS**
   - Symbol: {symbol}
   - Timeframe: {timeframe}

2. **Buscar vela de formación: {item.formation_time_est}**
   - Vela {candle_color}
   - Low: ~{item.zone_low:,.2f}
   - High: ~{item.zone_high:,.2f}
   - Open: ~{item.ob_open:,.2f}
   - Close: ~{item.ob_close:,.2f}

3. **Verificar impulso después del OB:**
   - Dirección: {item.impulse_direction}
   - Magnitud: ~{abs(item.impulse_move):.2f} puntos en las siguientes 3 velas
   - El precio debe haber hecho un movimiento {item.impulse_direction.lower()} energético

4. **Expectativa ICT:**
   - Este OB debe actuar como **{expected_behavior}**
   - Si el precio regresa a esta zona (${item.zone_low:,.2f} - ${item.zone_high:,.2f}), esperar {expected_action}
   - El nivel más importante es el **50% Body Midpoint: {item.body_midpoint:,.2f}**

---

"""

        # Add summary section
        report += f"""## 📊 Resumen del Audit

- **Total OBs Activos**: {len(audit_items)}
- **Timestamp Auditado**: {snapshot_time_est}
- **Symbol**: {symbol}
- **Timeframe**: {timeframe}

### Distribución por Tipo:
"""

        # Count by type
        type_counts = {}
        for item in audit_items:
            type_counts[item.ob_type] = type_counts.get(item.ob_type, 0) + 1

        for ob_type, count in sorted(type_counts.items(), key=lambda x: -x[1]):
            report += f"- **{ob_type}**: {count}\n"

        # Count by quality
        report += "\n### Distribución por Quality:\n"
        quality_counts = {}
        for item in audit_items:
            quality_counts[item.quality] = quality_counts.get(item.quality, 0) + 1

        for quality in ["HIGH", "MEDIUM", "LOW"]:
            count = quality_counts.get(quality, 0)
            if count > 0:
                report += f"- **{quality}**: {count}\n"

        report += f"""
---

**Generado**: {datetime.now(eastern).strftime('%Y-%m-%d %H:%M:%S %Z')}
**Sistema**: NQHUB Audit Module v1.0
"""

        return report
