"""One-time script to seed canada.json from last_report.json."""
import json, os
from datetime import datetime

LAST_REPORT = ".claude/memory/last_report.json"
OUTPUT      = "docs/data/canada.json"

os.makedirs("docs/data", exist_ok=True)

with open(LAST_REPORT) as f:
    data = json.load(f)

top_stocks = data.get("top_stocks", [])

current = []
for rank, stock in enumerate(top_stocks, start=1):
    signals  = stock.get("signals", {})
    fundam   = stock.get("fundamentals", {})
    score    = int(stock.get("composite_score", 0))
    current.append({
        "rank":       rank,
        "ticker":     stock.get("symbol", ""),
        "name":       stock.get("name", ""),
        "score":      score,
        "price":      signals.get("price"),
        "market_cap": fundam.get("market_cap"),
        "strategy":   stock.get("strategy", ""),
        "exchange":   "TSX" if stock.get("is_tsx") else "TSX-V",
        "scores": {
            "composite_score": score,
        },
        "details": {
            "composite_score": (
                f"Score {score}/100 — RSI {signals.get('rsi', 0):.1f}, "
                f"volume {signals.get('volume_ratio', 0):.1f}x avg, "
                f"10d momentum {signals.get('momentum_10d', 0):.1f}%. "
                f"{stock.get('strategy', '')} signal."
            ),
        },
    })

payload = {
    "last_updated": datetime.now().strftime("%Y-%m-%d"),
    "current":  current,
    "previous": [],
    "history":  [],
}

with open(OUTPUT, "w") as f:
    json.dump(payload, f, indent=2, default=str)

print(f"Written {len(current)} stocks to {OUTPUT}")
