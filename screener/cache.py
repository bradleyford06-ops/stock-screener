import sqlite3
import json
import os
import time
import logging

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "cache.db")
CACHE_TTL_HOURS = 4  # re-fetch data older than 4 hours


def get_connection():
    """Open (or create) the SQLite cache database."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS price_cache (
            symbol TEXT PRIMARY KEY,
            history_json TEXT,
            info_json TEXT,
            fetched_at REAL
        )
    """)
    conn.commit()
    return conn


def get_cached(symbol):
    """Return cached (history_df, info_dict) if fresh, else None."""
    import pandas as pd
    try:
        conn = get_connection()
        row = conn.execute(
            "SELECT history_json, info_json, fetched_at FROM price_cache WHERE symbol = ?",
            (symbol,)
        ).fetchone()
        conn.close()

        if row is None:
            return None, None

        age_hours = (time.time() - row[2]) / 3600
        if age_hours > CACHE_TTL_HOURS:
            return None, None

        history = pd.read_json(row[0])
        info = json.loads(row[1])
        return history, info

    except Exception as e:
        logger.debug(f"Cache read error for {symbol}: {e}")
        return None, None


def save_cache(symbol, history, info):
    """Store fetched data in the cache."""
    try:
        conn = get_connection()
        conn.execute(
            "INSERT OR REPLACE INTO price_cache (symbol, history_json, info_json, fetched_at) VALUES (?, ?, ?, ?)",
            (symbol, history.to_json(), json.dumps(info, default=str), time.time())
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.debug(f"Cache write error for {symbol}: {e}")
