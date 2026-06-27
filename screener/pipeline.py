import logging
import json
import os
from screener.fetch import fetch_all_tickers
from screener.filters import passes_basic_filters
from screener.technical import compute_technicals
from screener.fundamentals import extract_fundamentals, score_fundamentals
from screener.sentiment import score_sentiment
from screener.scoring import build_composite_score, determine_strategy, rank_candidates

logger = logging.getLogger(__name__)

LAST_REPORT_PATH = os.path.join(os.path.dirname(__file__), "..", ".claude", "memory", "last_report.json")


def load_previous_symbols():
    """Load the list of symbols from the last report for delta tracking."""
    try:
        if os.path.exists(LAST_REPORT_PATH):
            with open(LAST_REPORT_PATH) as f:
                data = json.load(f)
                return [s["symbol"] for s in data.get("top_stocks", [])]
    except Exception:
        pass
    return None


def save_report(top_stocks):
    """Persist the current report so we can compute deltas next run."""
    os.makedirs(os.path.dirname(LAST_REPORT_PATH), exist_ok=True)
    with open(LAST_REPORT_PATH, "w") as f:
        json.dump({"top_stocks": top_stocks}, f, indent=2, default=str)


def run_screener(tickers_csv, skip_sentiment=False):
    """Run the full screening pipeline and return ranked top-10 opportunities."""
    logger.info("Starting screening pipeline...")

    # Step 1: Fetch all ticker data
    all_data = fetch_all_tickers(tickers_csv)
    logger.info(f"Fetched data for {len(all_data)} tickers")

    candidates = []

    for symbol, data in all_data.items():
        history = data["history"]
        info = data["info"]

        # Step 2: Basic filters (market cap, volume)
        if not passes_basic_filters(symbol, info, history):
            continue

        # Step 3: Technical analysis
        signals = compute_technicals(history)
        if not signals:
            continue

        # Step 4: Fundamentals
        fundamentals = extract_fundamentals(symbol, info)
        fundamental_score = score_fundamentals(fundamentals)

        # Step 5: Sentiment (optional — slow due to FinBERT)
        if skip_sentiment:
            sentiment_score, headlines = 0.0, []
        else:
            sentiment_score, headlines = score_sentiment(symbol, fundamentals.get("name", symbol))

        # Step 6: Strategy label
        strategy = determine_strategy(signals, fundamental_score, sentiment_score)
        if strategy is None:
            continue  # not strong enough to flag

        # Step 7: Composite score
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
        })

    logger.info(f"{len(candidates)} candidates passed all filters")

    # Step 8: Rank and take top 10
    ranked = rank_candidates(candidates)
    top_10 = ranked[:10]

    save_report(top_10)
    return top_10
