# Session — August 30, 2026

## End of Session

Completed this session:
- Built the US Small-Cap Screener from scratch (NYSE/NASDAQ, $200M–$2B market cap, 6-signal scoring system out of 100 points)
- Set up GitHub repo `bradleyford06-ops/us-stock-screener` with Gmail, recipient, and PAT secrets configured
- Fixed the US screener timeout bug — was checking 8,000+ tickers one-by-one (70+ min), replaced with Yahoo Finance EquityQuery screener API (under 15 min)
- Fixed SEC EDGAR Form 4 XML parser — was returning $0 for all insider purchase values; now correctly reads shares × price from nested XML tags
- Added error alert emails to both screeners — crashes send a plain-text email explaining what went wrong
- Added snapshot logging to Canadian screener to match US screener format (SQLite, persisted via GitHub Actions cache)
- Made the `stock-screener` repo public and enabled GitHub Pages at `https://bradleyford06-ops.github.io/stock-screener/`
- Built a 3-tab live dashboard (Canadian Stocks, US Stocks, Performance Record)
- Seeded dashboard with current Canadian picks from `last_report.json` so it shows data immediately
- Built Performance tab: summary stats strip, signal scorecard (win rate by signal), active positions table, completed trades table
- Built trade tracking system for both screeners — auto-detects entries (first appearance) and exits (dropped off list) each run
- Simplified both screener emails to short plain-text with dashboard link
- Sent one-time email to bradleyford5@hotmail.com with the dashboard link

Still pending:
- Exit logic for Position Trades is too aggressive — currently exits as soon as a stock drops off the top 10, which doesn't suit 1-month to 1-year holds. Agreed to build minimum hold period (30 days) + stop-loss (-20%) logic next session
- US screener has never completed a successful run — first real test is Wednesday Sept 3 at 8AM ET
- Canadian screener market cap filter bug — HC.V appeared at $13M cap, well outside the $200M–$1B range; filters need tightening
- Performance tab signal scorecard and completed trades will be empty until first exits happen
- History table on dashboard will be empty until snapshot DB accumulates data across runs

Files changed:
- `us-stock-screener/screener/universe.py` — replaced slow one-by-one ticker loop with Yahoo Finance EquityQuery screener API
- `us-stock-screener/screener/insider.py` — rewrote Form 4 XML parser to correctly extract purchase values from nested tags
- `us-stock-screener/screener/trade_tracker.py` — new file, tracks entries and exits, writes docs/data/us_trades.json
- `us-stock-screener/screener/dashboard_export.py` — new file, writes docs/data/us.json after each run
- `us-stock-screener/screener/snapshot.py` — existing, unchanged
- `us-stock-screener/email_report/send.py` — simplified to plain-text email with dashboard link
- `us-stock-screener/email_report/error_alert.py` — new file, crash notification email
- `us-stock-screener/main.py` — wired in dashboard export, trade tracker, updated send_report call
- `us-stock-screener/.github/workflows/weekly-screener.yml` — added cross-repo push of us.json and us_trades.json via DASHBOARD_PAT
- `stock-screener/docs/index.html` — new file, full 3-tab dashboard with performance tab
- `stock-screener/docs/data/canada.json` — new file, seeded with current top 10 picks
- `stock-screener/docs/data/canada_trades.json` — new file, seeded with 10 active positions
- `stock-screener/screener/trade_tracker.py` — new file, tracks Canadian entries/exits
- `stock-screener/screener/dashboard_export.py` — new file, writes docs/data/canada.json after each run
- `stock-screener/screener/snapshot.py` — new file, SQLite snapshot logging added to Canadian screener
- `stock-screener/screener/pipeline.py` — wired in snapshot, dashboard export, and trade tracker
- `stock-screener/email_report/send.py` — simplified to plain-text email with dashboard link
- `stock-screener/email_report/error_alert.py` — new file, crash notification email
- `stock-screener/.github/workflows/screener.yml` — added contents:write permission, snapshot DB caching, and dashboard JSON commit step
- `stock-screener/generate_dashboard_now.py` — one-time seed script, can be deleted later

Decisions made:
- Exit strategy for Position Trades: minimum 30-day hold + -20% stop-loss override (not thesis-based, not manual) — to be built next session
- Performance tracking: built Option A (win/loss record) and Option B (signal attribution scorecard) together in one tab
- Dashboard hosted on `stock-screener` repo via GitHub Pages; US screener pushes data cross-repo via Personal Access Token (DASHBOARD_PAT secret)
- Emails simplified to short plain-text with link rather than full HTML report
- Canadian screener uses a single composite score; US screener shows 6 individual signal scores — display differs accordingly on the dashboard

Blockers or warnings:
- US screener has not yet run successfully end-to-end in the cloud — Wednesday Sept 3 is the first live test
- If DASHBOARD_PAT token expires or is revoked, US data will stop updating on the dashboard
- Canadian market cap filter is not enforcing correctly — some very small stocks (sub-$50M) are appearing in results
- Snapshot DB for Canadian screener is cached in GitHub Actions but not committed to the repo — if the cache is evicted, history resets

Recommended first step next session:
Build Position Trade exit logic in `/Users/bradleyford/Claude Code/stock-screener/screener/trade_tracker.py` — add a check so Position Trade exits only trigger after a minimum 30-day hold OR if the price has dropped 20%+ from entry. Apply the same logic to `/Users/bradleyford/Claude Code/us-stock-screener/screener/trade_tracker.py`. Then fix the Canadian screener market cap filter in `screener/filters.py`.

Session duration: approximately 3 hours
