import yfinance as yf
import pandas as pd
import time
import logging
from screener.cache import get_cached, save_cache

logger = logging.getLogger(__name__)


def fetch_stock_data(symbol, period="6mo"):
    """Download OHLCV price history and key info for one stock from Yahoo Finance (with caching)."""
    # Check cache first
    history, info = get_cached(symbol)
    if history is not None:
        return history, info

    try:
        ticker = yf.Ticker(symbol)
        history = ticker.history(period=period)
        if history.empty:
            return None, None
        info = ticker.info
        if not info or len(info) < 3:
            return None, None
        save_cache(symbol, history, info)
        return history, info
    except Exception as e:
        logger.warning(f"Failed to fetch {symbol}: {e}")
        return None, None


def fetch_all_tickers(tickers_csv, delay=0.3, cache_only=False):
    """Load ticker list from CSV and fetch price data for each, with rate-limit delays."""
    df = pd.read_csv(tickers_csv)
    results = {}
    total = len(df)
    cached_count = 0

    for i, row in df.iterrows():
        symbol = row["symbol"]

        # Check cache before logging (avoid spam for cached tickers)
        from screener.cache import get_cached
        cached_h, cached_i = get_cached(symbol)
        if cached_h is not None:
            results[symbol] = {"history": cached_h, "info": cached_i, "exchange": row.get("exchange", "")}
            cached_count += 1
            continue

        if cache_only:
            continue  # skip symbols not in cache

        logger.info(f"Fetching {symbol} ({i+1}/{total})")
        history, info = fetch_stock_data(symbol)
        if history is not None and info is not None:
            results[symbol] = {"history": history, "info": info, "exchange": row.get("exchange", "")}
        time.sleep(delay)

    logger.info(f"Fetched {len(results)} of {total} tickers ({cached_count} from cache)")
    return results
