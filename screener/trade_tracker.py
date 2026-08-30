"""
Track entries and exits from the screener's top-10 list.
Entry = first time a ticker appears. Exit = first time it drops off.
Persists to docs/data/canada_trades.json so the dashboard can read it.
"""

import json
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

TRADES_PATH = os.path.join(os.path.dirname(__file__), '..', 'docs', 'data', 'canada_trades.json')


def update_trades(current_stocks: list[dict], run_date: str = None):
    """Compare current top 10 to last run, record entries and exits, save trades file."""
    if run_date is None:
        run_date = datetime.now().strftime('%Y-%m-%d')

    trades = _load_trades()
    active = {t['ticker']: t for t in trades.get('active', [])}
    completed = trades.get('completed', [])

    current_tickers = {s.get('symbol', s.get('ticker', '')): s for s in current_stocks}

    # Detect exits — tickers in active but not in current run
    still_active = []
    for ticker, entry in active.items():
        if ticker not in current_tickers:
            # This ticker dropped off — record exit
            exit_price = entry.get('entry_price')  # fallback if we can't get current price
            try:
                import yfinance as yf
                info = yf.Ticker(ticker).fast_info
                exit_price = getattr(info, 'last_price', None) or exit_price
            except Exception:
                pass

            if exit_price and entry.get('entry_price'):
                ret_pct = ((exit_price - entry['entry_price']) / entry['entry_price']) * 100
            else:
                ret_pct = None

            entry_date = datetime.strptime(entry['entry_date'], '%Y-%m-%d')
            exit_date  = datetime.strptime(run_date, '%Y-%m-%d')
            days_held  = (exit_date - entry_date).days

            # Find the highest-scoring signal
            signals = entry.get('entry_signals', {})
            top_signal = max(signals, key=lambda k: signals[k]) if signals else None

            completed.append({
                'ticker':        ticker,
                'name':          entry.get('name', ''),
                'screener':      'canada',
                'strategy':      entry.get('strategy', ''),
                'exchange':      entry.get('exchange', ''),
                'entry_date':    entry['entry_date'],
                'exit_date':     run_date,
                'entry_price':   entry.get('entry_price'),
                'exit_price':    round(exit_price, 4) if exit_price else None,
                'return_pct':    round(ret_pct, 2) if ret_pct is not None else None,
                'days_held':     days_held,
                'entry_score':   entry.get('entry_score'),
                'entry_signals': entry.get('entry_signals', {}),
                'entry_details': entry.get('entry_details', {}),
                'top_signal':    top_signal,
            })
            logger.info(f"Exit: {ticker} at ${exit_price:.2f} ({ret_pct:+.1f}% over {days_held} days)" if ret_pct is not None else f"Exit: {ticker}")
        else:
            still_active.append(entry)

    # Detect entries — tickers in current run but not previously active
    for ticker, stock in current_tickers.items():
        if ticker not in active:
            signals  = stock.get('signals', {})
            fundam   = stock.get('fundamentals', {})
            score    = int(stock.get('composite_score', 0))
            price    = signals.get('price')

            still_active.append({
                'ticker':        ticker,
                'name':          stock.get('name', ''),
                'screener':      'canada',
                'strategy':      stock.get('strategy', ''),
                'exchange':      'TSX' if stock.get('is_tsx') else 'TSX-V',
                'entry_date':    run_date,
                'entry_price':   price,
                'entry_score':   score,
                'entry_signals': {'composite_score': score},
                'entry_details': {
                    'composite_score': (
                        f"Score {score}/100 — RSI {signals.get('rsi', 0):.1f}, "
                        f"volume {signals.get('volume_ratio', 0):.1f}x avg"
                    ),
                },
            })
            logger.info(f"Entry: {ticker} at ${price} score={score}")

    _save_trades({'active': still_active, 'completed': completed})
    logger.info(f"Trades updated: {len(still_active)} active, {len(completed)} completed")


def _load_trades() -> dict:
    """Load the existing trades file, or return empty structure."""
    try:
        if os.path.exists(TRADES_PATH):
            with open(TRADES_PATH) as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Could not load trades file: {e}")
    return {'active': [], 'completed': []}


def _save_trades(trades: dict):
    """Write the trades file to docs/data/canada_trades.json."""
    os.makedirs(os.path.dirname(TRADES_PATH), exist_ok=True)
    with open(TRADES_PATH, 'w') as f:
        json.dump(trades, f, indent=2, default=str)
