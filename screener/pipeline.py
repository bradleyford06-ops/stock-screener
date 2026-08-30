import logging
import json
import os
from datetime import date, timedelta
from screener.fetch import fetch_all_tickers
from screener.filters import passes_basic_filters
from screener.technical import compute_technicals
from screener.fundamentals import extract_fundamentals, score_fundamentals
from screener.sentiment import score_sentiment
from screener.scoring import build_composite_score, determine_strategy, rank_candidates

logger = logging.getLogger(__name__)

LAST_REPORT_PATH = os.path.join(os.path.dirname(__file__), "..", ".claude", "memory", "last_report.json")
MIN_TSX_STOCKS = 3  # guarantee at least this many TSX (not TSX-V) stocks in each report


def last_trading_day():
    """Return the most recent trading day (skips weekends)."""
    today = date.today()
    if today.weekday() == 5:   # Saturday
        return today - timedelta(days=1)
    elif today.weekday() == 6:  # Sunday
        return today - timedelta(days=2)
    return today


def load_previous_symbols(strategy_filter="Position Trade"):
    """Load symbols from the last report, optionally filtered by strategy."""
    try:
        if os.path.exists(LAST_REPORT_PATH):
            with open(LAST_REPORT_PATH) as f:
                data = json.load(f)
                stocks = data.get("top_stocks", [])
                if strategy_filter:
                    stocks = [s for s in stocks if s.get("strategy") == strategy_filter]
                return [s["symbol"] for s in stocks]
    except Exception:
        pass
    return None


def save_report(top_stocks):
    """Persist the current report so we can compute deltas next run."""
    os.makedirs(os.path.dirname(LAST_REPORT_PATH), exist_ok=True)
    with open(LAST_REPORT_PATH, "w") as f:
        json.dump({"top_stocks": top_stocks}, f, indent=2, default=str)


def _is_tsx(symbol):
    """Return True if the symbol is a TSX (not TSX-V) listing."""
    return symbol.endswith(".TO")


def run_screener(tickers_csv, skip_sentiment=False, cache_only=False):
    """Run the full screening pipeline and return ranked top-10 opportunities."""
    logger.info("Starting screening pipeline...")

    all_data = fetch_all_tickers(tickers_csv, cache_only=cache_only)
    logger.info(f"Fetched data for {len(all_data)} tickers")

    candidates = []

    for symbol, data in all_data.items():
        history = data["history"]
        info = data["info"]

        if not passes_basic_filters(symbol, info, history):
            continue

        signals = compute_technicals(history)
        if not signals:
            continue

        fundamentals = extract_fundamentals(symbol, info)
        fundamental_score = score_fundamentals(fundamentals)

        if skip_sentiment:
            sentiment_score, headlines = 0.0, []
        else:
            sentiment_score, headlines = score_sentiment(symbol, fundamentals.get("name", symbol))

        strategy = determine_strategy(signals, fundamental_score, sentiment_score)
        if strategy is None:
            continue

        composite_score = build_composite_score(signals, fundamental_score, sentiment_score)

        candidates.append({
            "symbol": symbol,
            "name": fundamentals.get("name", symbol),
            "strategy": strategy,
            "price": signals.get("price", 0),
            "composite_score": composite_score,
            "signals": signals,
            "fundamentals": fundamentals,
            "fundamental_score": fundamental_score,
            "sentiment_score": sentiment_score,
            "headlines": headlines,
            "is_tsx": _is_tsx(symbol),
        })

    logger.info(f"{len(candidates)} candidates passed all filters")

    ranked = rank_candidates(candidates)
    top_10 = _enforce_tsx_minimum(ranked)

    save_report(top_10)

    from screener.snapshot import save_snapshot
    save_snapshot(top_10)

    from screener.dashboard_export import export_dashboard_json
    export_dashboard_json(top_10)

    from screener.trade_tracker import update_trades
    update_trades(top_10)

    return top_10


def _enforce_tsx_minimum(ranked):
    """
    Build a top-10 list that includes at least MIN_TSX_STOCKS TSX stocks.
    Pulls the best TSX stocks up into the list if needed, displacing lower-ranked TSX-V stocks.
    """
    top_10 = ranked[:10]
    tsx_count = sum(1 for s in top_10 if s["is_tsx"])

    if tsx_count >= MIN_TSX_STOCKS:
        return top_10

    # Need more TSX stocks — find the best TSX candidates outside top 10
    tsx_extras = [s for s in ranked[10:] if s["is_tsx"]]
    needed = MIN_TSX_STOCKS - tsx_count

    for extra in tsx_extras[:needed]:
        # Replace the lowest-ranked non-TSX stock in current top 10
        for i in range(len(top_10) - 1, -1, -1):
            if not top_10[i]["is_tsx"]:
                top_10[i] = extra
                break

    return top_10
