import logging

logger = logging.getLogger(__name__)


def score_technicals(signals):
    """Score technical signals 0-100. Designed to spread widely — 90+ is rare and meaningful."""
    if not signals:
        return 0

    score = 0

    # RSI momentum (0-25 pts)
    rsi = signals.get("rsi")
    if rsi is not None:
        if 60 <= rsi <= 70:
            score += 25   # ideal momentum zone
        elif 55 <= rsi < 60:
            score += 15
        elif 70 < rsi <= 78:
            score += 10   # getting hot but still ok
        elif 50 <= rsi < 55:
            score += 5

    # Volume surge (0-30 pts) — the single strongest breakout signal
    volume_ratio = signals.get("volume_ratio", 0)
    if volume_ratio >= 10:
        score += 30
    elif volume_ratio >= 5:
        score += 22
    elif volume_ratio >= 3:
        score += 15
    elif volume_ratio >= 2:
        score += 7

    # Bollinger Band breakout (0-20 pts) — price pushing above statistical resistance
    if signals.get("bb_breakout"):
        score += 20

    # 10-day price momentum (0-15 pts)
    momentum = signals.get("momentum_10d", 0)
    if momentum >= 30:
        score += 15
    elif momentum >= 20:
        score += 12
    elif momentum >= 10:
        score += 8
    elif momentum >= 5:
        score += 4

    # Near 52-week high (0-10 pts)
    if signals.get("near_52w_high"):
        score += 10

    return min(score, 100)


def score_fundamentals(fundamentals):
    """Score fundamentals 0-100. Designed to spread widely."""
    score = 0

    # Revenue growth (0-35 pts)
    growth = fundamentals.get("revenue_growth", 0)
    if growth >= 1.0:       # 100%+ growth
        score += 35
    elif growth >= 0.50:    # 50%+
        score += 25
    elif growth >= 0.25:    # 25%+
        score += 15
    elif growth >= 0.10:    # 10%+
        score += 8
    elif growth > 0:
        score += 3

    # Cash vs debt (0-30 pts)
    cash = fundamentals.get("cash", 0)
    debt = fundamentals.get("total_debt", 0)
    if debt == 0 and cash > 0:
        score += 30
    elif cash > 0 and debt > 0:
        ratio = cash / debt
        if ratio >= 3.0:
            score += 28
        elif ratio >= 2.0:
            score += 22
        elif ratio >= 1.0:
            score += 14
        elif ratio >= 0.5:
            score += 6

    # Operating cash flow positive (0-20 pts)
    if fundamentals.get("operating_cashflow", 0) > 0:
        score += 20

    # Low debt-to-equity (0-15 pts)
    de = fundamentals.get("debt_to_equity", 0)
    if de == 0:
        score += 15
    elif de < 30:
        score += 10
    elif de < 75:
        score += 4

    return min(score, 100)


def determine_strategy(signals, fundamental_score, sentiment_score):
    """
    Assign strategy label based on signal profile.

    Swing Trade  — short-term breakout play (days to 2 weeks).
                   Requires strong RIGHT NOW technical signals.
    Position Trade — longer hold (1 month to 1 year).
                   Requires solid fundamentals + some technical confirmation.
    Watch List   — worth surfacing but signals are mixed or weak.
    """
    tech_score = score_technicals(signals)

    volume_ratio = signals.get("volume_ratio", 0)
    bb_breakout = signals.get("bb_breakout", False)
    momentum = signals.get("momentum_10d", 0)
    rsi = signals.get("rsi") or 0

    # Swing Trade: strong immediate breakout signals — volume surge, BB breakout, momentum
    swing_signal_count = sum([
        volume_ratio >= 3,
        bb_breakout,
        momentum >= 15,
        rsi >= 60,
    ])
    if tech_score >= 45 and swing_signal_count >= 2:
        return "Swing Trade"

    # Position Trade: strong fundamentals with at least moderate technical confirmation
    if fundamental_score >= 50 and tech_score >= 20:
        return "Position Trade"

    # Position Trade: exceptional fundamentals even with weak technicals
    if fundamental_score >= 70:
        return "Position Trade"

    # Watch List: something interesting but not yet a clear signal
    if tech_score >= 25 or fundamental_score >= 40:
        return "Watch List"

    return None


def build_composite_score(signals, fundamental_score, sentiment_score):
    """
    Combine signals into a 0-100 score with real spread.
    Weights: technical 55%, fundamental 35%, sentiment 10%.
    """
    tech_score = score_technicals(signals)
    sentiment_pts = max(min(sentiment_score, 1.0), -1.0) * 100 * 0.10
    composite = (tech_score * 0.55) + (fundamental_score * 0.35) + sentiment_pts
    return round(min(composite, 100), 1)


def rank_candidates(candidates):
    """Sort candidates by composite score, highest first."""
    return sorted(candidates, key=lambda x: x.get("composite_score", 0), reverse=True)
