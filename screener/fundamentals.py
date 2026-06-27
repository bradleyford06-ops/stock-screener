import logging

logger = logging.getLogger(__name__)


def extract_fundamentals(info):
    """Pull key fundamental metrics from Yahoo Finance info dict."""
    try:
        fundamentals = {}

        # Revenue and growth
        fundamentals["revenue"] = info.get("totalRevenue") or 0
        fundamentals["revenue_growth"] = info.get("revenueGrowth") or 0  # decimal, e.g. 0.25 = 25%

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
        fundamentals["name"] = info.get("longName") or info.get("shortName") or ""
        fundamentals["market_cap"] = info.get("marketCap") or 0

        return fundamentals

    except Exception as e:
        logger.warning(f"Fundamentals extraction error: {e}")
        return {}


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
