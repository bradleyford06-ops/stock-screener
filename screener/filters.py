import logging

logger = logging.getLogger(__name__)

MIN_MARKET_CAP_CAD = 50_000_000     # $50 million CAD
MAX_MARKET_CAP_CAD = 1_000_000_000  # $1 billion CAD
MIN_AVG_DAILY_VOLUME = 50_000        # minimum shares/day to avoid illiquid stocks
MIN_PRICE = 0.10                     # minimum share price — filters out most penny stocks
USD_TO_CAD = 1.36                    # approximate fallback; yfinance often returns CAD for TSX


def passes_basic_filters(symbol, info, history):
    """Return True if stock meets minimum market cap and volume requirements."""
    try:
        market_cap = info.get("marketCap", 0) or 0
        currency = info.get("currency", "CAD")

        # Convert USD market cap to CAD if needed
        if currency == "USD":
            market_cap_cad = market_cap * USD_TO_CAD
        else:
            market_cap_cad = market_cap

        if market_cap_cad < MIN_MARKET_CAP_CAD or market_cap_cad > MAX_MARKET_CAP_CAD:
            logger.debug(f"{symbol}: filtered out — market cap {market_cap_cad:,.0f} CAD")
            return False

        avg_volume = history["Volume"].tail(20).mean()
        if avg_volume < MIN_AVG_DAILY_VOLUME:
            logger.debug(f"{symbol}: filtered out — avg volume {avg_volume:,.0f}")
            return False

        # Minimum price filter — cuts out most penny stocks
        last_price = history["Close"].dropna().iloc[-1] if not history["Close"].dropna().empty else 0
        if last_price < MIN_PRICE:
            logger.debug(f"{symbol}: filtered out — price ${last_price:.4f} below minimum")
            return False

        return True

    except Exception as e:
        logger.warning(f"{symbol}: filter error — {e}")
        return False
