"""Generate docs/data/canada.json from the snapshot database for the dashboard."""

import sqlite3
import json
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

DB_PATH     = os.path.join(os.path.dirname(__file__), '..', 'data', 'snapshots.db')
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), '..', 'docs', 'data', 'canada.json')


def export_dashboard_json(top_stocks: list[dict] = None):
    """Build canada.json from the current top_stocks and full snapshot history."""
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    history  = _load_history()
    previous = _load_previous_run()

    current = []
    if top_stocks:
        for rank, stock in enumerate(top_stocks, start=1):
            signals  = stock.get('signals', {})
            fundam   = stock.get('fundamentals', {})
            current.append({
                'rank':                    rank,
                'ticker':                  stock.get('symbol', ''),
                'name':                    stock.get('name', ''),
                'score':                   int(stock.get('composite_score', 0)),
                'price':                   signals.get('price'),
                'market_cap':              fundam.get('market_cap'),
                'strategy':                stock.get('strategy', ''),
                'exchange':                'TSX' if stock.get('is_tsx') else 'TSX-V',
                'scores': {
                    'composite_score': int(stock.get('composite_score', 0)),
                },
                'details': {
                    'composite_score': (
                        f"Technical score {int(stock.get('composite_score', 0))}/100 — "
                        f"RSI {signals.get('rsi', 0):.0f}, "
                        f"volume {signals.get('volume_ratio', 0):.1f}x avg. "
                        f"{stock.get('strategy', '')} signal."
                    ),
                },
            })

    payload = {
        'last_updated': datetime.now().strftime('%Y-%m-%d'),
        'current':  current,
        'previous': previous,
        'history':  history,
    }

    with open(OUTPUT_PATH, 'w') as f:
        json.dump(payload, f, indent=2, default=str)

    logger.info(f'Dashboard JSON written to {OUTPUT_PATH}')


def _load_history() -> list[dict]:
    """Pull all snapshot rows, newest first."""
    try:
        if not os.path.exists(DB_PATH):
            return []
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.execute("""
            SELECT run_date, ticker, rank, total_score, price_at_recommendation,
                   strategy, exchange, details_json
            FROM snapshots
            ORDER BY run_date DESC, rank ASC
        """)
        rows = []
        for r in cursor.fetchall():
            details = json.loads(r[7]) if r[7] else {}
            rows.append({
                'run_date':                r[0],
                'ticker':                  r[1],
                'name':                    details.get('name', ''),
                'rank':                    r[2],
                'score':                   r[3],
                'price_at_recommendation': r[4],
                'strategy':                r[5] or details.get('strategy', ''),
                'exchange':                r[6],
            })
        conn.close()
        return rows
    except Exception as e:
        logger.warning(f'History load failed: {e}')
        return []


def _load_previous_run() -> list[dict]:
    """Return the tickers from the second-most-recent run (for delta display)."""
    try:
        if not os.path.exists(DB_PATH):
            return []
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.execute("""
            SELECT ticker FROM snapshots
            WHERE run_date = (
                SELECT DISTINCT run_date FROM snapshots
                ORDER BY run_date DESC
                LIMIT 1 OFFSET 1
            )
            ORDER BY rank ASC
        """)
        tickers = [{'ticker': row[0]} for row in cursor.fetchall()]
        conn.close()
        return tickers
    except Exception as e:
        logger.warning(f'Previous run load failed: {e}')
        return []
