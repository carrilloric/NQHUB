"""
NQ Data Loader

Carga archivos TBBO de Databento (Parquet o CSV) a TimescaleDB.
NO conecta a la API de Databento — lee archivos locales.

Este módulo es un thin wrapper sobre app.etl.services.tick_loader
para cumplir con la interfaz especificada en AUT-329.
"""
import logging
from pathlib import Path
from typing import Dict, List
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession

from app.etl.services.tick_loader import load_ticks_batch, get_tick_count
from app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class NQDataLoader:
    """
    Carga archivos TBBO de Databento (Parquet o CSV) a TimescaleDB.
    NO conecta a la API de Databento — lee archivos locales.
    """

    def __init__(self, session: AsyncSession = None):
        """
        Initialize data loader.

        Args:
            session: Optional async database session. If not provided,
                     will create new session for each operation.
        """
        self.session = session

    async def load_file(self, filepath: str) -> int:
        """
        Lee archivo TBBO local y carga ticks a TimescaleDB.

        Schema TBBO: ts_recv, ts_event, price, size, bid_px_00, ask_px_00,
                     bid_sz_00, ask_sz_00, side, action, oflow (JSONB)

        Args:
            filepath: Ruta al archivo Parquet o CSV

        Returns:
            Número de registros cargados

        Raises:
            FileNotFoundError: Si el archivo no existe
            ValueError: Si el formato del archivo no es soportado
            Exception: Si la carga falla
        """
        file_path = Path(filepath)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        logger.info(f"Loading file: {filepath}")

        # Read file based on extension
        if file_path.suffix == '.parquet':
            df = pd.read_parquet(file_path)
        elif file_path.suffix == '.csv':
            df = pd.read_csv(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}. Use .parquet or .csv")

        # Convert DataFrame to dict records
        ticks = self._prepare_ticks_from_dataframe(df)

        logger.info(f"Parsed {len(ticks)} ticks from {file_path.name}")

        # Load to database
        if self.session:
            inserted, duplicates = await load_ticks_batch(self.session, ticks)
            logger.info(f"Loaded {inserted} ticks ({duplicates} duplicates skipped)")
            return inserted
        else:
            async with AsyncSessionLocal() as session:
                inserted, duplicates = await load_ticks_batch(session, ticks)
                logger.info(f"Loaded {inserted} ticks ({duplicates} duplicates skipped)")
                return inserted

    async def load_directory(self, dirpath: str) -> Dict[str, int]:
        """
        Carga todos los archivos del directorio.

        Maneja duplicados (upsert por ts_event).

        Args:
            dirpath: Ruta al directorio con archivos TBBO

        Returns:
            Dictionary {filename: records_loaded}

        Raises:
            NotADirectoryError: Si la ruta no es un directorio
        """
        dir_path = Path(dirpath)

        if not dir_path.is_dir():
            raise NotADirectoryError(f"Not a directory: {dirpath}")

        logger.info(f"Loading all files from directory: {dirpath}")

        results = {}

        # Find all parquet and csv files
        files = list(dir_path.glob('*.parquet')) + list(dir_path.glob('*.csv'))

        if not files:
            logger.warning(f"No .parquet or .csv files found in {dirpath}")
            return results

        logger.info(f"Found {len(files)} files to process")

        for file_path in sorted(files):
            try:
                count = await self.load_file(str(file_path))
                results[file_path.name] = count
            except Exception as e:
                logger.error(f"Failed to load {file_path.name}: {str(e)}")
                results[file_path.name] = 0
                continue

        total_loaded = sum(results.values())
        logger.info(f"Directory load complete: {total_loaded} total ticks from {len(files)} files")

        return results

    def _prepare_ticks_from_dataframe(self, df: pd.DataFrame) -> List[Dict]:
        """
        Convert DataFrame to list of tick dictionaries compatible with tick_loader.

        Maps Databento TBBO schema to market_data_ticks schema.

        Args:
            df: DataFrame with TBBO data

        Returns:
            List of tick dictionaries
        """
        # Expected columns from Databento TBBO
        # ts_recv, ts_event, rtype, publisher_id, instrument_id,
        # action, side, depth, price, size, flags, ts_in_delta,
        # sequence, bid_px_00, ask_px_00, bid_sz_00, ask_sz_00,
        # bid_ct_00, ask_ct_00, symbol

        ticks = []

        for _, row in df.iterrows():
            tick = {
                'ts_event': pd.to_datetime(row['ts_event']),
                'ts_recv': pd.to_datetime(row.get('ts_recv', row['ts_event'])),
                'symbol': row.get('symbol', 'UNKNOWN'),
                'is_spread': '-' in str(row.get('symbol', '')),  # Detect calendar spreads
                'is_rollover_period': False,  # Will be detected by active_contract_detector
                'price': float(row['price']),
                'size': int(row['size']),
                'side': row.get('side', 'U'),  # B=Buy, A=Ask, U=Unknown
                'action': row.get('action', 'T'),  # T=Trade, A=Add, C=Cancel, M=Modify
                'bid_px': float(row.get('bid_px_00', 0)) if pd.notna(row.get('bid_px_00')) else None,
                'ask_px': float(row.get('ask_px_00', 0)) if pd.notna(row.get('ask_px_00')) else None,
                'bid_sz': int(row.get('bid_sz_00', 0)) if pd.notna(row.get('bid_sz_00')) else None,
                'ask_sz': int(row.get('ask_sz_00', 0)) if pd.notna(row.get('ask_sz_00')) else None,
                'bid_ct': int(row.get('bid_ct_00', 0)) if pd.notna(row.get('bid_ct_00')) else None,
                'ask_ct': int(row.get('ask_ct_00', 0)) if pd.notna(row.get('ask_ct_00')) else None,
                'rtype': int(row.get('rtype', 0)) if pd.notna(row.get('rtype')) else None,
                'publisher_id': int(row.get('publisher_id', 0)) if pd.notna(row.get('publisher_id')) else None,
                'instrument_id': int(row.get('instrument_id', 0)) if pd.notna(row.get('instrument_id')) else None,
                'sequence': int(row.get('sequence', 0)) if pd.notna(row.get('sequence')) else None,
                'flags': int(row.get('flags', 0)) if pd.notna(row.get('flags')) else None,
                'ts_in_delta': int(row.get('ts_in_delta', 0)) if pd.notna(row.get('ts_in_delta')) else None,
                'depth': int(row.get('depth', 0)) if pd.notna(row.get('depth')) else None,
            }

            ticks.append(tick)

        return ticks

    async def get_loaded_tick_count(self, symbol: str = None) -> int:
        """
        Get count of ticks currently in database.

        Args:
            symbol: Optional symbol filter

        Returns:
            Count of ticks
        """
        if self.session:
            count = await get_tick_count(self.session, symbol)
            return count
        else:
            async with AsyncSessionLocal() as session:
                count = await get_tick_count(session, symbol)
                return count
