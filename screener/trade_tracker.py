"""
Track entries and exits from the screener's top-10 list.
Entry = first time a ticker appears.

Exit rules:
- Swing Trade: exits the moment it drops off the top-10 list (short hold, days to weeks).
- Position Trade: does NOT exit just for dropping off the list. It exits only when
  either (a) price falls 20%+ below entry (stop-loss, checked every run), or
  (b) it has been held 30+ days AND is off the list.

Persists to docs/data/canada_trades.json so the dashboard can read it.
"""

import json
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

TRADES_PATH = os.path.join(os.path.dirname(__file__), '..', 'docs', 'data', 'canada_trades.json')

MIN_HOLD_DAYS = 30
STOP_LOSS_PCT = -20


def update_trades(current_stocks: list[dict], run_date: str = None):
    """Compare current top 10 to last run, record entries and exits, save trades file."""
    if run_date is None:
        run_date = datetime.now().strftime('%Y-%m-%d')

    trades = _load_trades()
    active = {t['ticker']: t for t in trades.get('active', [])}
    completed = trades.get('completed', [])

    current_tickers = {s.get('symbol', s.get('ticker', '')): s for s in current_stocks}

    still_active = []
    for ticker, entry in active.items():
        in_current_list = ticker in current_tickers

        if in_current_list:
            current_price = current_tickers[ticker].get('signals', {}).get('price')
        else:
            current_price = _fetch_current_price(ticker)

        ret_pct = _return_pct(entry.get('entry_price'), current_price)

        entry_date = datetime.strptime(entry['entry_date'], '%Y-%m-%d')
        run_date_dt = datetime.strptime(run_date, '%Y-%m-%d')
        days_held = (run_date_dt - entry_date).days

        exit_reason = _check_exit(entry.get('strategy'), in_current_list, days_held, ret_pct)

        if exit_reason:
            exit_price = current_price if current_price is not None else entry.get('entry_price')

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
                'exit_reason':   exit_reason,
            })
            logger.info(f"Exit ({exit_reason}): {ticker} at ${exit_price:.2f} ({ret_pct:+.1f}% over {days_held} days)" if ret_pct is not None else f"Exit ({exit_reason}): {ticker}")
        else:
            updated_entry = dict(entry)
            updated_entry['last_price']   = current_price
            updated_entry['last_checked'] = run_date
            updated_entry['on_list']      = in_current_list
            still_active.append(updated_entry)

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
                'last_price':    price,
                'last_checked':  run_date,
                'on_list':       True,
            })
            logger.info(f"Entry: {ticker} at ${price} score={score}")

    _save_trades({'active': still_active, 'completed': completed})
    logger.info(f"Trades updated: {len(still_active)} active, {len(completed)} completed")


def _fetch_current_price(ticker: str):
    """Look up a ticker's latest price via yfinance. Returns None if the lookup fails."""
    try:
        import yfinance as yf
        info = yf.Ticker(ticker).fast_info
        return getattr(info, 'last_price', None)
    except Exception:
        return None


def _return_pct(entry_price, current_price):
    """Percent return from entry_price to current_price, or None if either is missing."""
    if entry_price and current_price:
        return ((current_price - entry_price) / entry_price) * 100
    return None


def _check_exit(strategy: str, in_current_list: bool, days_held: int, ret_pct) -> str | None:
    """Decide whether an active position should exit this run, and why.

    Position Trade: only exits on a 20%+ stop-loss, or after 30+ days off the list.
    Everything else (Swing Trade, etc.): exits as soon as it drops off the list.
    """
    if strategy == 'Position Trade':
        if ret_pct is not None and ret_pct <= STOP_LOSS_PCT:
            return 'stop_loss'
        if not in_current_list and days_held >= MIN_HOLD_DAYS:
            return 'dropped_off_list'
        return None
    else:
        return 'dropped_off_list' if not in_current_list else None


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
