"""
Tests for NQ Data Loader and Candle Builder

Tests the complete pipeline:
- Loading TBBO files (Parquet/CSV) → TimescaleDB
- Generating candles for 8 timeframes
- Duplicate handling with upsert
- CLI functionality

As specified in AUT-329.
"""
import pytest
import pandas as pd
import tempfile
import subprocess
from pathlib import Path
from datetime import datetime, timedelta, timezone
from sqlalchemy import text

from app.research.data.loader import NQDataLoader
from app.research.data.candle_builder import CandleBuilder


@pytest.fixture
async def clean_test_data(async_db):
    """Clean test data before and after each test."""
    # Clean before test
    await async_db.execute(text("DELETE FROM market_data_ticks WHERE symbol LIKE 'TEST%'"))
    for tf in ['30s', '1min', '5min', '15min', '1hr', '4hr', 'daily', 'weekly']:
        await async_db.execute(text(f"DELETE FROM candlestick_{tf} WHERE symbol LIKE 'TEST%'"))
    await async_db.commit()

    yield

    # Clean after test
    await async_db.execute(text("DELETE FROM market_data_ticks WHERE symbol LIKE 'TEST%'"))
    for tf in ['30s', '1min', '5min', '15min', '1hr', '4hr', 'daily', 'weekly']:
        await async_db.execute(text(f"DELETE FROM candlestick_{tf} WHERE symbol LIKE 'TEST%'"))
    await async_db.commit()


def create_synthetic_tbbo_file(filepath: Path, num_ticks: int = 100, symbol: str = "TEST-NQ"):
    """
    Create synthetic TBBO Parquet file for testing.

    Args:
        filepath: Path where to save the file
        num_ticks: Number of ticks to generate
        symbol: Symbol name
    """
    # Generate synthetic tick data
    base_time = datetime(2024, 1, 1, 9, 30, 0, tzinfo=timezone.utc)
    base_price = 20000.0

    data = {
        'ts_event': [base_time + timedelta(seconds=i) for i in range(num_ticks)],
        'ts_recv': [base_time + timedelta(seconds=i, milliseconds=10) for i in range(num_ticks)],
        'symbol': [symbol] * num_ticks,
        'price': [base_price + (i % 20) * 0.25 for i in range(num_ticks)],  # Price oscillates
        'size': [1 + (i % 10) for i in range(num_ticks)],
        'side': ['B' if i % 2 == 0 else 'A' for i in range(num_ticks)],
        'action': ['T'] * num_ticks,
        'bid_px_00': [base_price + (i % 20) * 0.25 - 0.25 for i in range(num_ticks)],
        'ask_px_00': [base_price + (i % 20) * 0.25 + 0.25 for i in range(num_ticks)],
        'bid_sz_00': [5] * num_ticks,
        'ask_sz_00': [5] * num_ticks,
        'bid_ct_00': [2] * num_ticks,
        'ask_ct_00': [2] * num_ticks,
        'rtype': [32] * num_ticks,  # TBBO rtype
        'publisher_id': [1] * num_ticks,
        'instrument_id': [12345] * num_ticks,
        'sequence': list(range(num_ticks)),
        'flags': [0] * num_ticks,
        'ts_in_delta': [100] * num_ticks,
        'depth': [0] * num_ticks,
    }

    df = pd.DataFrame(data)

    # Save as Parquet
    if filepath.suffix == '.parquet':
        df.to_parquet(filepath, index=False)
    else:
        df.to_csv(filepath, index=False)

    return df


@pytest.mark.asyncio
async def test_load_file_inserts_ticks(async_db, clean_test_data):
    """
    Test: Cargar archivo parquet de 100 ticks → 100 registros en DB
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "test_data.parquet"
        create_synthetic_tbbo_file(file_path, num_ticks=100, symbol="TEST-NQ-001")

        loader = NQDataLoader(session=async_db)
        count = await loader.load_file(str(file_path))

        assert count == 100, f"Expected 100 ticks loaded, got {count}"

        # Verify in database
        result = await async_db.execute(
            text("SELECT COUNT(*) FROM market_data_ticks WHERE symbol = 'TEST-NQ-001'")
        )
        db_count = result.scalar()
        assert db_count == 100, f"Expected 100 ticks in DB, got {db_count}"


@pytest.mark.asyncio
async def test_load_file_handles_duplicates(db_session, clean_test_data):
    """
    Test: Cargar mismo archivo 2 veces → sigue siendo 100 (upsert)
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "test_data.parquet"
        create_synthetic_tbbo_file(file_path, num_ticks=100, symbol="TEST-NQ-002")

        loader = NQDataLoader(session=db_session)

        # First load
        count1 = await loader.load_file(str(file_path))
        assert count1 == 100

        # Second load (duplicates)
        count2 = await loader.load_file(str(file_path))
        assert count2 == 0, f"Expected 0 new ticks (all duplicates), got {count2}"

        # Verify total in database
        result = await db_session.execute(
            text("SELECT COUNT(*) FROM market_data_ticks WHERE symbol = 'TEST-NQ-002'")
        )
        db_count = result.scalar()
        assert db_count == 100, f"Expected 100 ticks in DB (no duplicates), got {db_count}"


@pytest.mark.asyncio
async def test_candle_builder_1min(db_session, clean_test_data):
    """
    Test: 60 ticks de 1 minuto → 1 candle con OHLCV correcto
    """
    # Create 60 ticks spanning exactly 1 minute
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "test_1min.parquet"
        create_synthetic_tbbo_file(file_path, num_ticks=60, symbol="TEST-NQ-003")

        # Load ticks
        loader = NQDataLoader(session=db_session)
        await loader.load_file(str(file_path))

        # Build 1min candles
        builder = CandleBuilder(session=db_session)
        start = datetime(2024, 1, 1, 9, 30, 0, tzinfo=timezone.utc)
        end = datetime(2024, 1, 1, 9, 31, 0, tzinfo=timezone.utc)

        count = await builder.build_candles('1min', start, end, symbol='TEST-NQ-003')

        assert count == 1, f"Expected 1 candle for 60 ticks in 1min, got {count}"

        # Verify candle exists
        result = await db_session.execute(
            text("SELECT COUNT(*) FROM candlestick_1min WHERE symbol = 'TEST-NQ-003'")
        )
        db_count = result.scalar()
        assert db_count == 1, f"Expected 1 candle in DB, got {db_count}"


@pytest.mark.asyncio
async def test_candle_builder_ohlc_correct(db_session, clean_test_data):
    """
    Test: open=primer tick, high=max, low=min, close=último tick
    """
    # Create ticks with specific prices to verify OHLC
    base_time = datetime(2024, 1, 1, 9, 30, 0, tzinfo=timezone.utc)
    prices = [100.0, 105.0, 95.0, 102.0]  # O=100, H=105, L=95, C=102

    data = {
        'ts_event': [base_time + timedelta(seconds=i*15) for i in range(4)],
        'ts_recv': [base_time + timedelta(seconds=i*15) for i in range(4)],
        'symbol': ['TEST-NQ-004'] * 4,
        'price': prices,
        'size': [1] * 4,
        'side': ['B'] * 4,
        'action': ['T'] * 4,
        'bid_px_00': [p - 0.25 for p in prices],
        'ask_px_00': [p + 0.25 for p in prices],
        'bid_sz_00': [5] * 4,
        'ask_sz_00': [5] * 4,
        'bid_ct_00': [2] * 4,
        'ask_ct_00': [2] * 4,
        'rtype': [32] * 4,
        'publisher_id': [1] * 4,
        'instrument_id': [12345] * 4,
        'sequence': list(range(4)),
        'flags': [0] * 4,
        'ts_in_delta': [100] * 4,
        'depth': [0] * 4,
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "test_ohlc.parquet"
        pd.DataFrame(data).to_parquet(file_path, index=False)

        # Load ticks
        loader = NQDataLoader(session=db_session)
        await loader.load_file(str(file_path))

        # Build 1min candles
        builder = CandleBuilder(session=db_session)
        start = datetime(2024, 1, 1, 9, 30, 0, tzinfo=timezone.utc)
        end = datetime(2024, 1, 1, 9, 31, 0, tzinfo=timezone.utc)

        await builder.build_candles('1min', start, end, symbol='TEST-NQ-004')

        # Verify OHLC values
        result = await db_session.execute(
            text("""
                SELECT open, high, low, close
                FROM candlestick_1min
                WHERE symbol = 'TEST-NQ-004'
            """)
        )
        row = result.fetchone()

        assert row is not None, "Candle not found in DB"
        assert row[0] == 100.0, f"Expected open=100.0, got {row[0]}"
        assert row[1] == 105.0, f"Expected high=105.0, got {row[1]}"
        assert row[2] == 95.0, f"Expected low=95.0, got {row[2]}"
        assert row[3] == 102.0, f"Expected close=102.0, got {row[3]}"


@pytest.mark.asyncio
async def test_candle_builder_oflow_jsonb(db_session, clean_test_data):
    """
    Test: Candle tiene campo oflow con delta calculado
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "test_oflow.parquet"
        create_synthetic_tbbo_file(file_path, num_ticks=60, symbol="TEST-NQ-005")

        # Load ticks
        loader = NQDataLoader(session=db_session)
        await loader.load_file(str(file_path))

        # Build 1min candles
        builder = CandleBuilder(session=db_session)
        start = datetime(2024, 1, 1, 9, 30, 0, tzinfo=timezone.utc)
        end = datetime(2024, 1, 1, 9, 31, 0, tzinfo=timezone.utc)

        await builder.build_candles('1min', start, end, symbol='TEST-NQ-005')

        # Verify oflow_detail and oflow_unit exist and are JSONB
        result = await db_session.execute(
            text("""
                SELECT delta, oflow_detail, oflow_unit
                FROM candlestick_1min
                WHERE symbol = 'TEST-NQ-005'
            """)
        )
        row = result.fetchone()

        assert row is not None, "Candle not found in DB"
        assert row[0] is not None, "Delta should not be NULL"
        assert row[1] is not None, "oflow_detail should not be NULL"
        assert row[2] is not None, "oflow_unit should not be NULL"
        assert isinstance(row[1], dict), "oflow_detail should be JSONB dict"
        assert isinstance(row[2], dict), "oflow_unit should be JSONB dict"


@pytest.mark.asyncio
async def test_build_all_timeframes(db_session, clean_test_data):
    """
    Test: Genera candles para los 8 timeframes sin error
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "test_all_tf.parquet"
        # Create ticks for 1 hour (enough for all timeframes)
        create_synthetic_tbbo_file(file_path, num_ticks=3600, symbol="TEST-NQ-006")

        # Load ticks
        loader = NQDataLoader(session=db_session)
        await loader.load_file(str(file_path))

        # Build all timeframes
        builder = CandleBuilder(session=db_session)
        start = datetime(2024, 1, 1, 9, 30, 0, tzinfo=timezone.utc)
        end = datetime(2024, 1, 1, 10, 30, 0, tzinfo=timezone.utc)

        results = await builder.build_all_timeframes(start, end, symbol='TEST-NQ-006')

        # Verify all 8 timeframes were processed
        expected_timeframes = ['30s', '1min', '5min', '15min', '1h', '4h', '1d', '1w']
        assert set(results.keys()) == set(expected_timeframes), \
            f"Expected {expected_timeframes}, got {list(results.keys())}"

        # Verify all succeeded (no zeros)
        for tf, count in results.items():
            assert count > 0, f"Timeframe {tf} generated 0 candles"


@pytest.mark.asyncio
async def test_cli_load_directory(clean_test_data):
    """
    Test: CLI script carga directorio sin error
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # Create multiple test files
        for i in range(3):
            file_path = tmp_path / f"test_file_{i}.parquet"
            create_synthetic_tbbo_file(file_path, num_ticks=50, symbol=f"TEST-NQ-CLI-{i}")

        # Run CLI script
        result = subprocess.run(
            [
                'python', 'backend/scripts/load_data.py',
                '--dir', str(tmp_path)
            ],
            capture_output=True,
            text=True
        )

        # Check exit code
        assert result.returncode == 0, f"CLI failed with error:\n{result.stderr}"

        # Check output contains success message
        assert "successfully" in result.stdout.lower() or "✅" in result.stdout, \
            f"Success message not found in output:\n{result.stdout}"


@pytest.mark.asyncio
async def test_loader_handles_csv_format(db_session, clean_test_data):
    """
    Test: Loader también maneja archivos CSV (no solo Parquet)
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "test_data.csv"
        create_synthetic_tbbo_file(file_path, num_ticks=100, symbol="TEST-NQ-CSV")

        loader = NQDataLoader(session=db_session)
        count = await loader.load_file(str(file_path))

        assert count == 100, f"Expected 100 ticks from CSV, got {count}"


@pytest.mark.asyncio
async def test_loader_rejects_invalid_format(db_session, clean_test_data):
    """
    Test: Loader rechaza formatos no soportados
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "test_data.txt"
        file_path.write_text("invalid data")

        loader = NQDataLoader(session=db_session)

        with pytest.raises(ValueError, match="Unsupported file format"):
            await loader.load_file(str(file_path))


@pytest.mark.asyncio
async def test_candle_builder_invalid_timeframe(db_session, clean_test_data):
    """
    Test: CandleBuilder rechaza timeframes inválidos
    """
    builder = CandleBuilder(session=db_session)
    start = datetime(2024, 1, 1, 9, 30, 0, tzinfo=timezone.utc)
    end = datetime(2024, 1, 1, 10, 30, 0, tzinfo=timezone.utc)

    with pytest.raises(ValueError, match="Invalid timeframe"):
        await builder.build_candles('invalid-tf', start, end)


@pytest.mark.asyncio
async def test_load_directory_empty(db_session, clean_test_data):
    """
    Test: load_directory maneja directorio vacío sin error
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        loader = NQDataLoader(session=db_session)
        results = await loader.load_directory(tmpdir)

        assert isinstance(results, dict), "Should return empty dict"
        assert len(results) == 0, "Should have no results for empty directory"
