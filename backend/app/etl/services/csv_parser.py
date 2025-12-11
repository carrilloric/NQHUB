"""
CSV Parser Service

Parses Databento CSV files and prepares data for database insertion.
"""
from pathlib import Path
from typing import Iterator, List, Dict
from datetime import datetime, timezone, date
import csv
import logging
import re
import zipfile
import zstandard as zstd

logger = logging.getLogger(__name__)

# Batch size for yielding records
BATCH_SIZE = 10_000


def parse_csv_file(csv_path: Path) -> Iterator[List[Dict]]:
    """
    Parse a Databento CSV file and yield batches of tick data.

    Databento CSV format:
    ts_event,ts_recv,rtype,publisher_id,instrument_id,action,side,price,size,flags,ts_in_delta,sequence

    Args:
        csv_path: Path to the CSV file

    Yields:
        Batches of dictionaries ready for bulk insert

    Raises:
        Exception: If parsing fails
    """
    # Extract symbol from filename (e.g., "NQZ4_2024-10-15.csv" -> "NQZ4")
    symbol = extract_symbol_from_filename(csv_path.name)

    logger.info(f"Parsing CSV file: {csv_path.name} (symbol: {symbol})")

    try:
        batch = []
        total_rows = 0
        error_count = 0

        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)

            for row in reader:
                try:
                    # Convert row to tick dictionary
                    tick = parse_tick_row(row, symbol)
                    batch.append(tick)
                    total_rows += 1

                    # Yield batch when it reaches BATCH_SIZE
                    if len(batch) >= BATCH_SIZE:
                        logger.info(f"Yielding batch of {len(batch)} records (total: {total_rows}, errors: {error_count})")
                        yield batch
                        batch = []

                except Exception as e:
                    error_count += 1
                    # Log detailed error for first few failures
                    if error_count <= 3:
                        logger.error(
                            f"Failed to parse row {total_rows + 1}: {str(e)}\n"
                            f"Row sample: {dict(list(row.items())[:5])}"
                        )
                    elif error_count == 4:
                        logger.error(f"Suppressing further parse errors (total errors: {error_count}+)")
                    # Skip invalid rows but continue processing
                    continue

            # Yield remaining records
            if batch:
                logger.info(f"Yielding final batch of {len(batch)} records (total: {total_rows}, errors: {error_count})")
                yield batch

        logger.info(f"Completed parsing {csv_path.name}: {total_rows} successful records, {error_count} errors")

    except FileNotFoundError:
        logger.error(f"CSV file not found: {csv_path}")
        raise Exception(f"CSV file not found: {csv_path}")
    except Exception as e:
        logger.error(f"Failed to parse CSV file {csv_path}: {str(e)}")
        raise


def parse_timestamp(ts_string: str) -> datetime:
    """
    Parse timestamp from either ISO 8601 format or nanoseconds.

    Args:
        ts_string: Timestamp as string (ISO 8601 or nanoseconds)

    Returns:
        datetime object with UTC timezone

    Raises:
        ValueError: If timestamp format is not recognized
    """
    # Try ISO 8601 format first (e.g., "2024-06-18T00:00:01.326828655Z")
    if 'T' in ts_string or '-' in ts_string:
        try:
            # Remove 'Z' suffix if present and parse
            ts_clean = ts_string.rstrip('Z')
            dt = datetime.fromisoformat(ts_clean)
            # Ensure UTC timezone
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            pass

    # Try nanoseconds format (integer string)
    try:
        nanoseconds = int(ts_string)
        return nanoseconds_to_datetime(nanoseconds)
    except ValueError:
        raise ValueError(f"Unable to parse timestamp: {ts_string}")


def parse_tick_row(row: Dict[str, str], symbol: str | None) -> Dict:
    """
    Parse a single CSV row into a tick dictionary.

    Args:
        row: CSV row as dictionary
        symbol: Extracted symbol from filename (used as fallback, may be None)

    Returns:
        Dictionary with fields matching market_data_ticks table
    """
    # Convert timestamps - try ISO 8601 format first, fallback to nanoseconds
    ts_event = parse_timestamp(row['ts_event'])
    ts_recv = parse_timestamp(row['ts_recv'])

    # Prefer symbol from CSV column, fallback to filename extraction
    if 'symbol' in row and row['symbol']:
        symbol = row['symbol'].strip()
    elif symbol is None:
        raise ValueError("Symbol not found in CSV content or filename")

    # Parse price and size
    price = float(row['price'])
    size = int(row['size'])

    # Parse optional fields
    side = row.get('side', 'A')  # A=Ask, B=Bid, T=Trade
    action = row.get('action', '')  # A=Add, C=Cancel, M=Modify, T=Trade

    # Databento metadata
    rtype = int(row.get('rtype', 0))
    publisher_id = int(row.get('publisher_id', 0))
    instrument_id = int(row.get('instrument_id', 0))
    sequence = int(row.get('sequence', 0))
    flags = int(row.get('flags', 0))
    ts_in_delta = int(row.get('ts_in_delta', 0))

    # Order book fields (may be in CSV with _00 suffix or without)
    # Try with _00 suffix first (Databento format), fallback to without suffix
    bid_px = None
    if 'bid_px_00' in row and row['bid_px_00']:
        bid_px = float(row['bid_px_00'])
    elif 'bid_px' in row and row['bid_px']:
        bid_px = float(row['bid_px'])

    ask_px = None
    if 'ask_px_00' in row and row['ask_px_00']:
        ask_px = float(row['ask_px_00'])
    elif 'ask_px' in row and row['ask_px']:
        ask_px = float(row['ask_px'])

    bid_sz = None
    if 'bid_sz_00' in row and row['bid_sz_00']:
        bid_sz = int(row['bid_sz_00'])
    elif 'bid_sz' in row and row['bid_sz']:
        bid_sz = int(row['bid_sz'])

    ask_sz = None
    if 'ask_sz_00' in row and row['ask_sz_00']:
        ask_sz = int(row['ask_sz_00'])
    elif 'ask_sz' in row and row['ask_sz']:
        ask_sz = int(row['ask_sz'])

    bid_ct = None
    if 'bid_ct_00' in row and row['bid_ct_00']:
        bid_ct = int(row['bid_ct_00'])
    elif 'bid_ct' in row and row['bid_ct']:
        bid_ct = int(row['bid_ct'])

    ask_ct = None
    if 'ask_ct_00' in row and row['ask_ct_00']:
        ask_ct = int(row['ask_ct_00'])
    elif 'ask_ct' in row and row['ask_ct']:
        ask_ct = int(row['ask_ct'])

    return {
        'ts_event': ts_event,
        'ts_recv': ts_recv,
        'symbol': symbol,
        'is_spread': False,  # TODO: Detect spread symbols
        'is_rollover_period': False,  # Will be updated by rollover detection
        'price': price,
        'size': size,
        'side': side,
        'action': action,
        'bid_px': bid_px,
        'ask_px': ask_px,
        'bid_sz': bid_sz,
        'ask_sz': ask_sz,
        'bid_ct': bid_ct,
        'ask_ct': ask_ct,
        'rtype': rtype,
        'publisher_id': publisher_id,
        'instrument_id': instrument_id,
        'sequence': sequence,
        'flags': flags,
        'ts_in_delta': ts_in_delta,
        'depth': None  # Not in basic Databento CSV
    }


def nanoseconds_to_datetime(nanoseconds: int) -> datetime:
    """
    Convert nanoseconds timestamp to Python datetime.

    Args:
        nanoseconds: Timestamp in nanoseconds since epoch

    Returns:
        datetime object with UTC timezone
    """
    seconds = nanoseconds / 1_000_000_000
    return datetime.fromtimestamp(seconds, tz=timezone.utc)


def extract_symbol_from_filename(filename: str) -> str | None:
    """
    Extract symbol from CSV filename.

    Expected formats:
    - NQZ4_2024-10-15.csv -> NQZ4
    - ESH5_20250115.csv -> ESH5
    - databento_NQM4.csv -> NQM4
    - glbx-mdp3-20240718.tbbo.NQU4.csv -> NQU4
    - glbx-mdp3-20240619.tbbo.csv -> None (symbol not in filename)

    Args:
        filename: Name of the CSV file

    Returns:
        Extracted symbol or None if not found
    """
    # Try to match common patterns
    patterns = [
        r'^([A-Z]{2,3}[FGHJKMNQUVXZ]\d{1,2})_',      # NQZ4_ or ESH25_
        r'_([A-Z]{2,3}[FGHJKMNQUVXZ]\d{1,2})',       # databento_NQZ4
        r'\.([A-Z]{2,3}[FGHJKMNQUVXZ]\d{1,2})\.csv', # .NQU4.csv
        r'^([A-Z]{2,3}[FGHJKMNQUVXZ]\d{1,2})',       # NQZ4.csv
    ]

    for pattern in patterns:
        match = re.search(pattern, filename)
        if match:
            symbol = match.group(1)
            logger.info(f"Extracted symbol '{symbol}' from filename '{filename}'")
            return symbol

    # Not found - this is OK, will read from CSV content
    logger.debug(f"No symbol found in filename '{filename}', will read from CSV content")
    return None


def extract_symbol_from_csv_content(zip_file: zipfile.ZipFile, file_info: zipfile.ZipInfo, max_rows: int = 10) -> str | None:
    """
    Extract symbol by reading the CSV content from within a ZIP file.

    This is the authoritative source for symbol detection.
    Reads the first few rows to find the symbol column.
    Supports both plain CSV and zstandard-compressed (.zst) files.

    Args:
        zip_file: ZipFile object containing the CSV
        file_info: ZipInfo object for the specific file
        max_rows: Maximum rows to read (default: 10)

    Returns:
        Extracted symbol or None if not found
    """
    try:
        is_compressed = file_info.filename.endswith('.csv.zst')

        # Open and read CSV from ZIP
        with zip_file.open(file_info.filename) as f:
            if is_compressed:
                # Decompress .zst file in memory using streaming decompressor
                logger.debug(f"Decompressing .zst file to extract symbol: {file_info.filename}")
                dctx = zstd.ZstdDecompressor()

                # Read enough compressed data to get actual rows (not just header)
                # .zst files can have high compression ratios, read up to 1MB compressed to get data rows
                compressed_data = f.read(1_000_000)  # Read up to 1MB compressed
                decompressed = dctx.decompress(compressed_data, max_output_size=10_000_000)  # Allow up to 10MB decompressed
                content = decompressed.decode('utf-8')
            else:
                # Read first 8KB for uncompressed CSV
                content = f.read(8192).decode('utf-8')

            # Parse CSV content
            reader = csv.DictReader(content.splitlines())

            # Check if symbol column exists
            if 'symbol' not in reader.fieldnames:
                logger.debug(f"No 'symbol' column in CSV: {file_info.filename}")
                return None

            # Read first row to get symbol
            for row in reader:
                if 'symbol' in row and row['symbol']:
                    symbol = row['symbol'].strip()
                    logger.info(f"Extracted symbol '{symbol}' from CSV content: {file_info.filename}")
                    return symbol
                break  # Only check first data row

        logger.debug(f"No symbol found in CSV content: {file_info.filename}")
        return None

    except Exception as e:
        logger.warning(f"Failed to extract symbol from CSV content {file_info.filename}: {e}")
        return None


def extract_date_from_filename(filename: str) -> date | None:
    """
    Extract date from CSV filename.

    Expected formats:
    - glbx-mdp3-20240715.tbbo.csv -> date(2024, 7, 15)
    - data_20250103.csv -> date(2025, 1, 3)
    - NQZ4_2024-10-15.csv -> date(2024, 10, 15)

    Args:
        filename: Name of the CSV file

    Returns:
        date object or None if no date found
    """
    # Try to match YYYYMMDD format (20240715)
    pattern_yyyymmdd = r'(\d{4})(\d{2})(\d{2})'
    match = re.search(pattern_yyyymmdd, filename)

    if match:
        year = int(match.group(1))
        month = int(match.group(2))
        day = int(match.group(3))

        try:
            date_obj = date(year, month, day)
            logger.info(f"Extracted date '{date_obj.isoformat()}' from filename '{filename}'")
            return date_obj
        except (ValueError, IndexError):
            pass

    # Try to match YYYY-MM-DD format (2024-10-15)
    pattern_dash = r'(\d{4})-(\d{2})-(\d{2})'
    match = re.search(pattern_dash, filename)

    if match:
        year = int(match.group(1))
        month = int(match.group(2))
        day = int(match.group(3))

        try:
            date_obj = date(year, month, day)
            logger.info(f"Extracted date '{date_obj.isoformat()}' from filename '{filename}'")
            return date_obj
        except (ValueError, IndexError):
            pass

    logger.debug(f"Could not extract date from filename '{filename}'")
    return None


def count_csv_rows(csv_path: Path) -> int:
    """
    Count total rows in CSV file (excluding header).

    Args:
        csv_path: Path to CSV file

    Returns:
        Number of data rows
    """
    try:
        with open(csv_path, 'r') as f:
            # Subtract 1 for header row
            return sum(1 for _ in f) - 1
    except Exception as e:
        logger.error(f"Failed to count rows in {csv_path}: {str(e)}")
        return 0
