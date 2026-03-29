#!/usr/bin/env python3
"""
NQ Data Loader CLI

Script de línea de comandos para cargar datos históricos de NQ
desde archivos locales (Parquet/CSV de Databento) a TimescaleDB.

Uso:
    # Cargar un archivo
    python scripts/load_data.py --file /data/nq_2024_tbbo.parquet

    # Cargar directorio completo
    python scripts/load_data.py --dir /data/nq_2024/

    # Generar candles después de cargar ticks
    python scripts/load_data.py --build-candles --start 2024-01-01 --end 2024-12-31

    # Todo en uno
    python scripts/load_data.py --dir /data/nq_2024/ --build-candles

    # Cargar + generar candles para un símbolo específico
    python scripts/load_data.py --dir /data/nq_2024/ --build-candles --symbol NQH4
"""
import sys
import asyncio
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.research.data.loader import NQDataLoader
from app.research.data.candle_builder import CandleBuilder
from app.core.database import get_session

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('load_data.log')
    ]
)
logger = logging.getLogger(__name__)


async def load_file(filepath: str):
    """Load a single file."""
    logger.info(f"=== Loading single file: {filepath} ===")

    loader = NQDataLoader()
    try:
        count = await loader.load_file(filepath)
        logger.info(f"✅ Successfully loaded {count} ticks from {filepath}")
        return count
    except Exception as e:
        logger.error(f"❌ Failed to load file: {e}")
        raise


async def load_directory(dirpath: str):
    """Load all files in a directory."""
    logger.info(f"=== Loading directory: {dirpath} ===")

    loader = NQDataLoader()
    try:
        results = await loader.load_directory(dirpath)

        # Print summary
        total = sum(results.values())
        logger.info(f"\n{'='*60}")
        logger.info(f"LOAD SUMMARY")
        logger.info(f"{'='*60}")
        logger.info(f"Total files: {len(results)}")
        logger.info(f"Total ticks loaded: {total:,}")
        logger.info(f"\nPer-file breakdown:")
        for filename, count in sorted(results.items()):
            status = "✅" if count > 0 else "❌"
            logger.info(f"  {status} {filename}: {count:,} ticks")

        return results
    except Exception as e:
        logger.error(f"❌ Failed to load directory: {e}")
        raise


async def build_candles(
    start_date: str,
    end_date: str = None,
    symbol: str = None,
    timeframes: list = None
):
    """Build candles for date range."""
    start = datetime.fromisoformat(start_date)
    end = datetime.fromisoformat(end_date) if end_date else datetime.now()

    logger.info(f"=== Building candles ===")
    logger.info(f"Date range: {start.date()} to {end.date()}")
    logger.info(f"Symbol: {symbol or 'ALL'}")
    logger.info(f"Timeframes: {timeframes or 'ALL'}")

    builder = CandleBuilder()

    try:
        if timeframes:
            # Build specific timeframes
            results = {}
            for tf in timeframes:
                count = await builder.build_candles(tf, start, end, symbol)
                results[tf] = count
        else:
            # Build all timeframes
            results = await builder.build_all_timeframes(start, end, symbol)

        # Print summary
        logger.info(f"\n{'='*60}")
        logger.info(f"CANDLE BUILD SUMMARY")
        logger.info(f"{'='*60}")
        logger.info(f"Date range: {start.date()} to {end.date()}")
        logger.info(f"Symbol: {symbol or 'ALL'}")
        logger.info(f"\nCandles generated per timeframe:")
        for timeframe, count in sorted(results.items()):
            status = "✅" if count > 0 else "⚠️"
            logger.info(f"  {status} {timeframe:8s}: {count:,} candles")

        total = sum(results.values())
        logger.info(f"\nTotal candles: {total:,}")

        return results
    except Exception as e:
        logger.error(f"❌ Failed to build candles: {e}")
        raise


async def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Load NQ historical data from local files to TimescaleDB',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Load single file
  python scripts/load_data.py --file /data/nq_2024_tbbo.parquet

  # Load directory
  python scripts/load_data.py --dir /data/nq_2024/

  # Build candles for date range
  python scripts/load_data.py --build-candles --start 2024-01-01 --end 2024-12-31

  # Load + build candles in one command
  python scripts/load_data.py --dir /data/nq_2024/ --build-candles --start 2024-01-01

  # Specific symbol and timeframes
  python scripts/load_data.py --dir /data/nq_2024/ --build-candles --symbol NQH4 --timeframes 1min 5min 15min
        """
    )

    # Loading options
    parser.add_argument(
        '--file',
        type=str,
        help='Path to single Parquet or CSV file to load'
    )
    parser.add_argument(
        '--dir',
        type=str,
        help='Path to directory with Parquet/CSV files to load'
    )

    # Candle building options
    parser.add_argument(
        '--build-candles',
        action='store_true',
        help='Build candles after loading ticks (or standalone if no --file/--dir)'
    )
    parser.add_argument(
        '--start',
        type=str,
        help='Start date for candle building (ISO format: YYYY-MM-DD)'
    )
    parser.add_argument(
        '--end',
        type=str,
        help='End date for candle building (ISO format: YYYY-MM-DD). Defaults to today.'
    )
    parser.add_argument(
        '--symbol',
        type=str,
        help='Symbol filter (e.g., NQH4). If not provided, processes all symbols.'
    )
    parser.add_argument(
        '--timeframes',
        type=str,
        nargs='+',
        choices=['30s', '1min', '5min', '15min', '1h', '4h', '1d', '1w'],
        help='Specific timeframes to build (default: all)'
    )

    args = parser.parse_args()

    # Validate arguments
    if not any([args.file, args.dir, args.build_candles]):
        parser.error("Must specify at least one of: --file, --dir, or --build-candles")

    if args.build_candles and not args.start:
        parser.error("--build-candles requires --start date")

    try:
        # Load ticks if requested
        if args.file:
            await load_file(args.file)
        elif args.dir:
            await load_directory(args.dir)

        # Build candles if requested
        if args.build_candles:
            await build_candles(
                start_date=args.start,
                end_date=args.end,
                symbol=args.symbol,
                timeframes=args.timeframes
            )

        logger.info("\n✅ All operations completed successfully!")

    except KeyboardInterrupt:
        logger.warning("\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ Operation failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
