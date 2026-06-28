import logging
import yfinance as yf

logger = logging.getLogger(__name__)


def _calculate_revenue_growth(symbol):
    """Compute revenue growth from actual annual income statement data (more reliable than Yahoo's field)."""
    try:
        ticker = yf.Ticker(symbol)
        financials = ticker.financials  # annual income statement, columns = fiscal year dates

        if financials is None or financials.empty:
            return 0.0

        # Look for a revenue row — Yahoo uses different labels
        revenue_labels = ["Total Revenue", "Revenue", "Net Revenue"]
        revenue_row = None
        for label in revenue_labels:
            if label in financials.index:
                revenue_row = financials.loc[label]
                break

        if revenue_row is None or len(revenue_row) < 2:
            return 0.0

        # Most recent year vs prior year (columns are sorted newest first)
        recent = float(revenue_row.iloc[0])
        prior = float(revenue_row.iloc[1])

        if prior <= 0 or recent <= 0:
            return 0.0

        growth = (recent - prior) / abs(prior)

        # Cap at ±5x to filter out distortions from near-zero base years
        return round(max(min(growth, 5.0), -1.0), 4)

    except Exception as e:
        logger.debug(f"Revenue growth calc failed for {symbol}: {e}")
        return 0.0


def extract_fundamentals(symbol, info):
    """Pull key fundamental metrics from Yahoo Finance info dict and income statement."""
    try:
        fundamentals = {}

        # Revenue growth — calculated from actual statements, not Yahoo's field
        fundamentals["revenue_growth"] = _calculate_revenue_growth(symbol)

        # Cash and debt
        fundamentals["cash"] = info.get("totalCash") or 0
        fundamentals["total_debt"] = info.get("totalDebt") or 0
        fundamentals["debt_to_equity"] = info.get("debtToEquity") or 0

        # Profitability
        fundamentals["profit_margin"] = info.get("profitMargins") or 0
        fundamentals["operating_cashflow"] = info.get("operatingCashflow") or 0

        # Valuation
        fundamentals["pe_ratio"] = info.get("trailingPE") or 0
        fundamentals["pb_ratio"] = info.get("priceToBook") or 0

        # Company basics
        fundamentals["sector"] = info.get("sector") or "Unknown"
        fundamentals["industry"] = info.get("industry") or "Unknown"
        fundamentals["name"] = info.get("longName") or info.get("shortName") or symbol
        fundamentals["market_cap"] = info.get("marketCap") or 0
        fundamentals["revenue"] = info.get("totalRevenue") or 0

        # Company description — trim to first 2 sentences for email brevity
        full_desc = info.get("longBusinessSummary") or ""
        if full_desc:
            sentences = full_desc.replace("  ", " ").split(". ")
            short_desc = ". ".join(sentences[:2]).strip()
            if not short_desc.endswith("."):
                short_desc += "."
            fundamentals["description"] = short_desc
        else:
            fundamentals["description"] = ""

        return fundamentals

    except Exception as e:
        logger.warning(f"Fundamentals extraction error for {symbol}: {e}")
        return {"name": symbol, "revenue_growth": 0, "cash": 0, "total_debt": 0,
                "debt_to_equity": 0, "operating_cashflow": 0, "market_cap": 0}


def score_fundamentals(fundamentals):
    """Score fundamentals from 0-100. Higher = stronger financial position."""
    score = 0

    # Revenue growth (up to 30 points)
    growth = fundamentals.get("revenue_growth", 0)
    if growth >= 0.50:
        score += 30
    elif growth >= 0.25:
        score += 20
    elif growth >= 0.10:
        score += 10
    elif growth > 0:
        score += 5

    # Cash position vs debt (up to 30 points)
    cash = fundamentals.get("cash", 0)
    debt = fundamentals.get("total_debt", 0)
    if debt == 0 and cash > 0:
        score += 30
    elif cash > 0 and debt > 0:
        ratio = cash / debt
        if ratio >= 2.0:
            score += 25
        elif ratio >= 1.0:
            score += 15
        elif ratio >= 0.5:
            score += 5

    # Operating cash flow positive (20 points)
    if fundamentals.get("operating_cashflow", 0) > 0:
        score += 20

    # Reasonable debt-to-equity (20 points)
    de = fundamentals.get("debt_to_equity", 0)
    if de == 0:
        score += 20
    elif de < 50:
        score += 15
    elif de < 100:
        score += 5

    return min(score, 100)
