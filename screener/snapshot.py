"""Snapshot logging — saves each run's top 10 for quarterly performance review."""

import sqlite3
import json
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "snapshots.db")


def init_db():
    """Create the snapshots database and table if they don't exist."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_date TEXT NOT NULL,
            ticker TEXT NOT NULL,
            rank INTEGER NOT NULL,
            total_score INTEGER NOT NULL,
            market_cap INTEGER,
            price_at_recommendation REAL,
            strategy TEXT,
            exchange TEXT,
            scores_json TEXT,
            details_json TEXT
        )
    """)
    conn.commit()
    conn.close()
    logger.info("Snapshot database ready")


def save_snapshot(top_stocks: list[dict], run_date: str = None):
    """Save this run's top 10 results to the database for future performance review."""
    if run_date is None:
        run_date = datetime.now().strftime("%Y-%m-%d")

    init_db()
    conn = sqlite3.connect(DB_PATH)

    for rank, stock in enumerate(top_stocks, start=1):
        signals = stock.get("signals", {})
        fundamentals = stock.get("fundamentals", {})

        scores_json = json.dumps({
            "composite_score": stock.get("composite_score", 0),
            "fundamental_score": stock.get("fundamental_score", 0),
            "sentiment_score": round(stock.get("sentiment_score", 0), 3),
        })

        details_json = json.dumps({
            "name": stock.get("name", ""),
            "strategy": stock.get("strategy", ""),
            "rsi": signals.get("rsi"),
            "volume_ratio": signals.get("volume_ratio"),
            "revenue_growth": fundamentals.get("revenue_growth"),
        })

        conn.execute("""
            INSERT INTO snapshots
            (run_date, ticker, rank, total_score, market_cap, price_at_recommendation, strategy, exchange, scores_json, details_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            run_date,
            stock.get("symbol", ""),
            rank,
            int(stock.get("composite_score", 0)),
            fundamentals.get("market_cap"),
            signals.get("price"),
            stock.get("strategy", ""),
            "TSX" if stock.get("is_tsx") else "TSX-V",
            scores_json,
            details_json,
        ))

    conn.commit()
    conn.close()
    logger.info(f"Saved snapshot for {run_date} — {len(top_stocks)} stocks logged")


def get_previous_tickers(strategy_filter: str = None) -> list[str]:
    """Return the tickers from the most recent previous run for delta comparison."""
    try:
        init_db()
        conn = sqlite3.connect(DB_PATH)
        if strategy_filter:
            cursor = conn.execute("""
                SELECT ticker FROM snapshots
                WHERE run_date = (
                    SELECT DISTINCT run_date FROM snapshots
                    ORDER BY run_date DESC
                    LIMIT 1 OFFSET 1
                ) AND strategy = ?
            """, (strategy_filter,))
        else:
            cursor = conn.execute("""
                SELECT ticker FROM snapshots
                WHERE run_date = (
                    SELECT DISTINCT run_date FROM snapshots
                    ORDER BY run_date DESC
                    LIMIT 1 OFFSET 1
                )
            """)
        tickers = [row[0] for row in cursor.fetchall()]
        conn.close()
        return tickers
    except Exception as error:
        logger.warning(f"Could not load previous tickers: {error}")
        return []


def get_quarterly_performance_data() -> list[dict]:
    """Pull all snapshots for the quarterly lookback report."""
    try:
        init_db()
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.execute("""
            SELECT run_date, ticker, rank, total_score, price_at_recommendation, strategy, exchange
            FROM snapshots
            ORDER BY run_date ASC, rank ASC
        """)
        rows = cursor.fetchall()
        conn.close()
        return [
            {
                "run_date": r[0], "ticker": r[1], "rank": r[2],
                "score": r[3], "price_at_recommendation": r[4],
                "strategy": r[5], "exchange": r[6],
            }
            for r in rows
        ]
    except Exception as error:
        logger.warning(f"Could not load performance data: {error}")
        return []
