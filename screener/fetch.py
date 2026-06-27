import yfinance as yf
import pandas as pd
import time
import logging

logger = logging.getLogger(__name__)


def fetch_stock_data(symbol, period="6mo"):
    """Download OHLCV price history and key info for one stock from Yahoo Finance."""
    try:
        ticker = yf.Ticker(symbol)
        history = ticker.history(period=period)
        if history.empty:
            return None, None
        info = ticker.info
        return history, info
    except Exception as e:
        logger.warning(f"Failed to fetch {symbol}: {e}")
        return None, None


def fetch_all_tickers(tickers_csv, delay=0.3):
    """Load ticker list from CSV and fetch price data for each, with rate-limit delays."""
    df = pd.read_csv(tickers_csv)
    results = {}
    total = len(df)
    for i, row in df.iterrows():
        symbol = row["symbol"]
        logger.info(f"Fetching {symbol} ({i+1}/{total})")
        history, info = fetch_stock_data(symbol)
        if history is not None and info is not None:
            results[symbol] = {"history": history, "info": info, "exchange": row.get("exchange", "")}
        time.sleep(delay)
    logger.info(f"Fetched {len(results)} of {total} tickers successfully")
    return results
