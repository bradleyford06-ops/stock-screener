import logging

logger = logging.getLogger(__name__)


def score_technicals(signals):
    """Score technical signals from 0-100. Higher = stronger breakout setup."""
    if not signals:
        return 0

    score = 0

    # RSI momentum sweet spot: 50-70 is trending up without being overbought (30 pts)
    rsi = signals.get("rsi")
    if rsi is not None:
        if 55 <= rsi <= 70:
            score += 30
        elif 50 <= rsi < 55:
            score += 20
        elif 70 < rsi <= 80:
            score += 10

    # Volume surge 3x+ average (25 pts)
    volume_ratio = signals.get("volume_ratio", 0)
    if volume_ratio >= 5:
        score += 25
    elif volume_ratio >= 3:
        score += 20
    elif volume_ratio >= 2:
        score += 10

    # Near 52-week high / breaking resistance (20 pts)
    if signals.get("near_52w_high"):
        score += 20

    # Golden cross: 50-day MA above 200-day MA (15 pts)
    if signals.get("golden_cross"):
        score += 15

    # Bollinger band breakout (10 pts)
    if signals.get("bb_breakout"):
        score += 10

    return min(score, 100)


def determine_strategy(signals, fundamental_score, sentiment_score):
    """Label a stock as Swing Trade, Position Trade, or None based on signal profile."""
    tech_score = score_technicals(signals)

    # Position Trade: strong technicals + fundamentals
    if tech_score >= 30 and fundamental_score >= 40:
        return "Position Trade"

    # Swing Trade: technical breakout signals dominate
    if tech_score >= 40:
        return "Swing Trade"

    # Position Trade with strong fundamentals even if technicals are moderate
    if fundamental_score >= 60 and tech_score >= 10:
        return "Position Trade"

    # Show best available even on quiet days — always surface something
    if fundamental_score >= 50 or tech_score >= 20:
        return "Watch List"

    return None


def build_composite_score(signals, fundamental_score, sentiment_score):
    """Combine technical, fundamental, and sentiment scores into one ranking score (0-100)."""
    tech_score = score_technicals(signals)

    # Weights: technical 50%, fundamental 30%, sentiment 20%
    composite = (tech_score * 0.50) + (fundamental_score * 0.30) + (max(sentiment_score, -1) * 50 * 0.20)
    return round(composite, 2)


def rank_candidates(candidates):
    """Sort candidate stocks by composite score, highest first."""
    return sorted(candidates, key=lambda x: x.get("composite_score", 0), reverse=True)
