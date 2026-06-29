from datetime import date, timedelta


def _last_trading_day():
    """Return the most recent trading day as a formatted string."""
    today = date.today()
    if today.weekday() == 5:
        day = today - timedelta(days=1)
    elif today.weekday() == 6:
        day = today - timedelta(days=2)
    else:
        day = today
    return day.strftime("%A, %B %d, %Y")


def format_email(top_stocks, previous_position_symbols=None, previous_swing_symbols=None):
    """Build the plain-text email body. Position Trades first, then Swing Trades."""
    report_date = _last_trading_day()
    lines = []

    lines.append("CANADIAN SMALL-CAP STOCK SCREENER")
    lines.append(f"Report Date: {report_date}")
    lines.append("=" * 60)
    lines.append("")

    if not top_stocks:
        lines.append("No stocks passed the screening criteria today.")
        return "\n".join(lines)

    position_trades = [s for s in top_stocks if s.get("strategy") == "Position Trade"]
    swing_trades = [s for s in top_stocks if s.get("strategy") == "Swing Trade"]
    watch_list = [s for s in top_stocks if s.get("strategy") == "Watch List"]

    # Delta section — Position Trades only
    current_position_symbols = [s["symbol"] for s in position_trades]
    if previous_position_symbols is not None:
        new_positions = [s for s in current_position_symbols if s not in previous_position_symbols]
        dropped_positions = [s for s in previous_position_symbols if s not in current_position_symbols]
        if new_positions or dropped_positions:
            lines.append("POSITION TRADE CHANGES")
            lines.append("-" * 40)
            if new_positions:
                lines.append(f"  NEW:     {', '.join(new_positions)}")
            if dropped_positions:
                lines.append(f"  DROPPED: {', '.join(dropped_positions)}")
            lines.append("")

    # ── POSITION TRADES ──────────────────────────────────────────
    if position_trades:
        lines.append("POSITION TRADES  (hold 1 month – 1 year)")
        lines.append("=" * 60)
        lines.append("")
        for i, stock in enumerate(position_trades, 1):
            lines += _format_position_trade(i, stock)

    # ── SWING TRADES ─────────────────────────────────────────────
    if swing_trades or (previous_swing_symbols and any(s not in [x["symbol"] for x in swing_trades] for s in previous_swing_symbols)):
        lines.append("SWING TRADES  (hold days – 2 weeks)")
        lines.append("=" * 60)
        lines.append("")

        # Show exited signals at the top so you know if something you were watching fell off
        if previous_swing_symbols is not None:
            current_swing_symbols = [s["symbol"] for s in swing_trades]
            exited = [s for s in previous_swing_symbols if s not in current_swing_symbols]
            if exited:
                lines.append("  ⚠  EXITED SIGNAL (no longer showing breakout signals):")
                lines.append(f"     {', '.join(exited)}")
                lines.append("     If you hold any of these, consider reviewing your exit.")
                lines.append("")

        for i, stock in enumerate(swing_trades, 1):
            lines += _format_swing_trade(i, stock)

    # ── WATCH LIST ───────────────────────────────────────────────
    if watch_list:
        lines.append("WATCH LIST  (signals present but not yet strong enough)")
        lines.append("=" * 60)
        lines.append("")
        for i, stock in enumerate(watch_list, 1):
            lines += _format_swing_trade(i, stock)  # same compact format

    lines.append("─" * 60)
    lines.append("Generated automatically by the Canadian Small-Cap Stock Screener.")
    lines.append("Not financial advice. Always do your own research before investing.")

    return "\n".join(lines)


def _format_position_trade(rank, stock):
    """Full write-up for a Position Trade: signals + sector + company description + catalyst."""
    symbol = stock.get("symbol", "")
    name = stock.get("name", symbol)
    price = stock.get("price", 0)
    score = stock.get("composite_score", 0)
    signals = stock.get("signals", {})
    fundamentals = stock.get("fundamentals", {})
    sentiment_score = stock.get("sentiment_score", 0)
    headlines = stock.get("headlines", [])

    lines = []
    lines.append(f"#{rank}  {symbol} — {name}")
    lines.append(f"    Strategy: Position Trade  |  Score: {score:.0f}/100  |  Price: ${price:.2f}")

    # Sector
    sector = fundamentals.get("sector", "")
    industry = fundamentals.get("industry", "")
    if sector and sector != "Unknown":
        sector_line = f"    Sector: {sector}"
        if industry and industry != "Unknown" and industry != sector:
            sector_line += f" — {industry}"
        lines.append(sector_line)

    lines.append("")

    # Company description (from Yahoo's longBusinessSummary, trimmed to 2 sentences)
    description = fundamentals.get("description", "")
    if description:
        lines.append(f"    About: {description}")
        lines.append("")

    # Catalyst
    catalyst = _build_catalyst(signals, fundamentals, sentiment_score, headlines)
    if catalyst:
        lines.append(f"    Why now: {catalyst}")
        lines.append("")

    # Signal bullets
    reasons = _build_reasons(signals, fundamentals, sentiment_score)
    lines.append("    Signals:")
    for reason in reasons:
        lines.append(f"      • {reason}")
    lines.append("")

    if headlines:
        lines.append("    Recent News:")
        for h in headlines[:2]:
            lines.append(f"      - {h}")
        lines.append("")

    lines.append("-" * 60)
    lines.append("")
    return lines


def _format_swing_trade(rank, stock):
    """Compact format for Swing Trade / Watch List: just the key signals."""
    symbol = stock.get("symbol", "")
    name = stock.get("name", symbol)
    price = stock.get("price", 0)
    score = stock.get("composite_score", 0)
    strategy = stock.get("strategy", "")
    signals = stock.get("signals", {})
    fundamentals = stock.get("fundamentals", {})
    sentiment_score = stock.get("sentiment_score", 0)

    lines = []
    lines.append(f"#{rank}  {symbol} — {name}")
    lines.append(f"    Strategy: {strategy}  |  Score: {score:.0f}/100  |  Price: ${price:.2f}")
    lines.append("")

    reasons = _build_reasons(signals, fundamentals, sentiment_score)
    for reason in reasons:
        lines.append(f"      • {reason}")
    lines.append("")

    lines.append("-" * 60)
    lines.append("")
    return lines


def _build_catalyst(signals, fundamentals, sentiment_score, headlines):
    """Write a one-sentence plain-English catalyst summary for Position Trades."""
    parts = []

    growth = fundamentals.get("revenue_growth", 0)
    momentum = signals.get("momentum_10d", 0)
    volume_ratio = signals.get("volume_ratio", 0)
    bb_breakout = signals.get("bb_breakout", False)

    if growth >= 0.50:
        parts.append(f"revenue is growing at {growth*100:.0f}% year-over-year")
    if momentum >= 15:
        parts.append(f"price is up {momentum:.0f}% in the past 10 trading days")
    if volume_ratio >= 3:
        parts.append(f"volume is {volume_ratio:.1f}x above average suggesting institutional interest")
    if bb_breakout:
        parts.append("price has broken above its statistical resistance band")
    if sentiment_score >= 0.3 and headlines:
        parts.append(f"recent news is positive: \"{headlines[0]}\"")

    if not parts:
        return ""

    if len(parts) == 1:
        return parts[0].capitalize() + "."
    return ", and ".join([parts[0].capitalize()] + parts[1:]) + "."


def _build_reasons(signals, fundamentals, sentiment_score):
    """Translate raw signals into plain-English bullet points."""
    reasons = []

    rsi = signals.get("rsi")
    if rsi is not None:
        if 60 <= rsi <= 70:
            reasons.append(f"RSI is {rsi} — strong upward momentum, not yet overbought")
        elif 55 <= rsi < 60:
            reasons.append(f"RSI is {rsi} — momentum building")
        elif 70 < rsi <= 78:
            reasons.append(f"RSI is {rsi} — momentum is hot, watch for pullback")

    volume_ratio = signals.get("volume_ratio", 0)
    if volume_ratio >= 5:
        reasons.append(f"Volume is {volume_ratio:.1f}x the 20-day average — strong unusual buying")
    elif volume_ratio >= 3:
        reasons.append(f"Volume is {volume_ratio:.1f}x the 20-day average — notable buying interest")

    if signals.get("bb_breakout"):
        reasons.append("Price broke above its Bollinger Band — pushing through statistical resistance")

    momentum = signals.get("momentum_10d", 0)
    if momentum >= 20:
        reasons.append(f"Up {momentum:.1f}% over the past 10 trading days")
    elif momentum >= 10:
        reasons.append(f"Up {momentum:.1f}% over the past 10 days")

    if signals.get("near_52w_high"):
        reasons.append("Price is near its 52-week high — breaking through long-term resistance")

    if signals.get("golden_cross"):
        reasons.append("50-day moving average is above the 200-day — classic long-term bullish setup")

    growth = fundamentals.get("revenue_growth", 0)
    if growth >= 0.50:
        reasons.append(f"Revenue growing {growth*100:.0f}% year-over-year")
    elif growth >= 0.25:
        reasons.append(f"Revenue growing {growth*100:.0f}% year-over-year")

    cash = fundamentals.get("cash", 0)
    debt = fundamentals.get("total_debt", 0)
    if debt == 0 and cash > 0:
        reasons.append("No debt — fully funded with cash on hand")
    elif cash > 0 and debt > 0 and cash > debt * 1.5:
        reasons.append("Strong cash position — cash significantly exceeds debt")

    if sentiment_score >= 0.3:
        reasons.append("Recent news sentiment is strongly positive")

    if not reasons:
        reasons.append("Multiple technical and fundamental signals aligned")

    return reasons
