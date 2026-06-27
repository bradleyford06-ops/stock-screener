from datetime import datetime


def format_email(top_stocks, previous_symbols=None):
    """Build the plain-text email body from the ranked top-10 stock list."""
    today = datetime.now().strftime("%A, %B %d, %Y")
    lines = []

    lines.append(f"CANADIAN SMALL-CAP STOCK SCREENER")
    lines.append(f"Report Date: {today}")
    lines.append("=" * 60)
    lines.append("")

    if not top_stocks:
        lines.append("No stocks passed the screening criteria today.")
        return "\n".join(lines)

    # Delta tracking
    current_symbols = [s["symbol"] for s in top_stocks]
    if previous_symbols is not None:
        new_entries = [s for s in current_symbols if s not in previous_symbols]
        dropped = [s for s in previous_symbols if s not in current_symbols]
        if new_entries or dropped:
            lines.append("CHANGES SINCE LAST REPORT")
            lines.append("-" * 40)
            if new_entries:
                lines.append(f"  NEW:     {', '.join(new_entries)}")
            if dropped:
                lines.append(f"  DROPPED: {', '.join(dropped)}")
            lines.append("")

    lines.append("TOP OPPORTUNITIES")
    lines.append("-" * 60)
    lines.append("")

    for i, stock in enumerate(top_stocks[:10], 1):
        symbol = stock.get("symbol", "")
        name = stock.get("name", symbol)
        strategy = stock.get("strategy", "Unknown")
        price = stock.get("price", 0)
        composite_score = stock.get("composite_score", 0)
        signals = stock.get("signals", {})
        fundamentals = stock.get("fundamentals", {})
        sentiment_score = stock.get("sentiment_score", 0)
        headlines = stock.get("headlines", [])

        lines.append(f"#{i}  {symbol} — {name}")
        lines.append(f"    Strategy: {strategy}")
        lines.append(f"    Price: ${price:.4f}  |  Score: {composite_score:.1f}/100")
        lines.append("")

        # Plain-English signal summary
        reasons = _build_reasons(signals, fundamentals, sentiment_score)
        lines.append("    Why this stock was flagged:")
        for reason in reasons:
            lines.append(f"      • {reason}")
        lines.append("")

        if headlines:
            lines.append("    Recent News:")
            for h in headlines[:3]:
                lines.append(f"      - {h}")
            lines.append("")

        lines.append("-" * 60)
        lines.append("")

    lines.append("This report was generated automatically by the Canadian Small-Cap Stock Screener.")
    lines.append("Not financial advice. Always do your own research before investing.")

    return "\n".join(lines)


def _build_reasons(signals, fundamentals, sentiment_score):
    """Translate raw signal data into plain-English bullet points."""
    reasons = []

    rsi = signals.get("rsi")
    if rsi and 55 <= rsi <= 75:
        reasons.append(f"RSI is {rsi} — showing strong upward momentum without being overbought")

    volume_ratio = signals.get("volume_ratio", 0)
    if volume_ratio >= 3:
        reasons.append(f"Volume is {volume_ratio:.1f}x the 20-day average — unusual buying interest")

    if signals.get("near_52w_high"):
        reasons.append("Price is near its 52-week high — breaking through resistance")

    if signals.get("golden_cross"):
        reasons.append("50-day moving average is above the 200-day — a classic bullish setup")

    if signals.get("bb_breakout"):
        reasons.append("Price broke above its Bollinger Band upper limit — a strong breakout signal")

    momentum = signals.get("momentum_10d", 0)
    if momentum >= 10:
        reasons.append(f"Up {momentum:.1f}% over the past 10 days")

    growth = fundamentals.get("revenue_growth", 0)
    if growth >= 0.25:
        reasons.append(f"Revenue growing at {growth*100:.0f}% year-over-year")

    cash = fundamentals.get("cash", 0)
    debt = fundamentals.get("total_debt", 0)
    if cash > 0 and (debt == 0 or cash > debt):
        reasons.append("Strong cash position with low debt — well-funded")

    if sentiment_score >= 0.3:
        reasons.append("Recent news sentiment is strongly positive")
    elif sentiment_score >= 0.1:
        reasons.append("Recent news coverage is moderately positive")

    if not reasons:
        reasons.append("Multiple technical and fundamental signals aligned")

    return reasons
