# Canadian Small-Cap Stock Screener

## What This Project Does
Screens the TSX and TSX-V stock exchanges for small-cap stocks (market cap under $1 billion CAD) that show strong technical breakout signals, positive news sentiment, and quality backing. Delivers a ranked top-10 opportunity list by email every Monday, Wednesday, and Friday at 8AM ET.

## Vision & Product Lead
Bradley Ford — makes all investment and product decisions. Not a developer.

## Technical Lead
Claude — responsible for all code, architecture, and technical decisions.

## Two Strategies This Screener Identifies
- **Swing Trades:** Targeting 5%+ gain, holding days to weeks. Flagged based on technical breakout signals.
- **Position Trades:** Targeting 100%+ gain (multi-baggers), holding weeks to months. Flagged based on technicals + fundamentals + smart money signals.

## Tech Stack
- Language: Python 3 (via Anaconda)
- Data: yfinance (Yahoo Finance API, free)
- Technical Analysis: pandas-ta
- News Sentiment: FinBERT (financial-domain sentiment model)
- Filings: SEDAR+ (Canadian securities filings — private placements, insider activity)
- Email: SMTP via Gmail or SendGrid
- Scheduling: Cron job or Claude scheduled task
- Storage: SQLite (local cache, prevents redundant API calls)
- Ticker Universe: Static CSV of TSX/TSX-V tickers, updated monthly

## Screening Criteria
**Must pass all:**
- Market cap < $1 billion CAD
- Listed on TSX or TSX-V
- Minimum average daily volume (to filter illiquid stocks)

**Scored and ranked:**
- Technical: price breaking resistance, volume surge (3x+ average), RSI momentum, moving average alignment (50-day above 200-day)
- Fundamentals: revenue growth, cash position, debt levels
- Smart money: insider buying from SEDAR+ filings, quality of private placement investors
- News sentiment: positive recent coverage, scored by FinBERT on full article body

## Email Delivery
- **To:** bradleyford5@hotmail.com
- **Schedule:** 8AM ET on Monday, Wednesday, Friday
- **Format:** Top 10 opportunities, medium summary
  - Each stock: plain-English explanation of why it was flagged
  - Strategy label: Swing Trade or Position Trade
  - Delta section: new additions since last report, stocks that dropped off

## Key Directories
- `data/` — SQLite cache, ticker CSV, raw data files
- `screener/` — core screening logic
- `screener/technical.py` — technical analysis functions
- `screener/sentiment.py` — news fetching and FinBERT scoring
- `screener/filings.py` — SEDAR+ filing parser
- `screener/scoring.py` — composite ranking logic
- `email_report/` — email formatting and delivery
- `scheduler/` — cron/scheduling setup
- `docs/` — decisions log and project notes
- `.claude/memory/sessions/` — session history

## Commands
- Run screener manually: `python main.py`
- Run screener and send email: `python main.py --send`
- Update ticker list: `python update_tickers.py`
- Test email without running screener: `python email_report/send.py --test`
- View last report: `cat .claude/memory/last_report.json`

## Conventions
- All dollar amounts in CAD unless noted
- Use descriptive variable names — no single-letter variables
- Every function needs a one-line plain-English comment explaining what it does
- Log errors clearly so non-technical user can understand what went wrong
- Never hardcode API keys — always use environment variables or a `.env` file

## Hard Rules
- NEVER commit `.env` files or API keys to git
- NEVER send email to any address other than bradleyford5@hotmail.com without explicit approval
- NEVER delete cached data without confirming with Bradley first
- ALWAYS test email formatting before enabling scheduled sends

## Current Work Context
**Status:** Both screeners running. Live dashboard at https://bradleyford06-ops.github.io/stock-screener/ — Canadian tab populated, US tab waiting for first successful run (Wednesday Sept 3).

**Next steps:**
1. Fix Position Trade exit logic in `screener/trade_tracker.py` — add 30-day minimum hold + -20% stop-loss before a Position Trade can exit
2. Fix Canadian screener market cap filter — sub-$50M stocks appearing in results (check `screener/filters.py`)
3. After Wednesday Sept 3: check US screener first run logs and review picks

**Phase:** Dashboard (Phase 2) complete. Performance tracking live but exits not yet strategy-aware. US screener built, first live run pending.

**Companion project:** `bradleyford06-ops/us-stock-screener` — US Small-Cap screener, same dashboard, runs Wednesdays 8AM ET.
