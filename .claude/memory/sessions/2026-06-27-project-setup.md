# Session: Project Setup
Date: 2026-06-27
Project: Canadian Small-Cap Stock Screener
Goal: Define the full project scope and set up the working environment
Continuing from: first session

## Status at Start
- Last completed: N/A — first session
- Pending: N/A
- Blockers: None

## Work Log
- Interviewed Bradley to define full project requirements
- Defined two strategies: Swing Trades (5%+) and Position Trades (100%+ multi-baggers)
- Confirmed data sources: yfinance, SEDAR+, FinBERT for sentiment
- Confirmed email delivery: bradleyford5@hotmail.com, 8AM ET Mon/Wed/Fri
- Confirmed email format: Top 10, medium summary, plain English, delta tracking (new/dropped)
- Installed Node.js v26.4.0 via Homebrew
- Created global CLAUDE.md at ~/.claude/CLAUDE.md with safety rules and user profile
- Created project folder at /Users/bradleyford/Claude Code/stock-screener/
- Created project CLAUDE.md with full project spec
- Created .claude/settings.json with hard safety blocks (no rm -rf, no force push, etc.)
- Created /session-start and /session-end global commands
- Set up session memory folder structure
- Saved user profile and workflow preferences to memory system

## End of Session

Completed this session:
- Full project requirements defined and documented
- Global Claude Code environment configured (safety rules, user profile, session commands)
- Stock screener project folder created with complete CLAUDE.md spec
- Node.js installed
- Session management system live and working

Still pending:
- Build the actual screener (nothing coded yet — this session was all planning and setup)
- Install Python dependencies (yfinance, pandas-ta, transformers/FinBERT)
- Source or build the TSX/TSX-V ticker CSV
- Build core pipeline: fetch → analyze → score → rank → email

Files changed:
- ~/.claude/CLAUDE.md — created (global rules and user profile)
- /Users/bradleyford/Claude Code/stock-screener/CLAUDE.md — created (project spec)
- /Users/bradleyford/Claude Code/stock-screener/.claude/settings.json — created (safety blocks)
- ~/.claude/commands/session-start.md — created (session start command)
- ~/.claude/commands/session-end.md — created (session end command)
- ~/.claude/projects/.../memory/user_profile.md — created (Bradley's profile)
- ~/.claude/projects/.../memory/feedback_workflow.md — created (workflow preferences)

Decisions made:
- Static CSV for ticker universe (faster and more reliable than live scraping TMX)
- Email first, dashboard later (Phase 2)
- Risk management is a separate future project — not in scope here
- Two distinct strategy labels per stock: Swing Trade vs Position Trade
- SEDAR+ as primary source for private placement and insider data
- News sources chosen dynamically per stock by Claude based on what's most relevant

Blockers or warnings:
- FinBERT model is ~400MB — first run will be slow while it downloads
- yfinance has rate limits for bulk fetching — need to build in delays and caching
- SEDAR+ scraping needs to be tested — their site structure may require adaptation

Recommended first step next session:
Install Python dependencies and build the ticker CSV. Run: `pip install yfinance pandas pandas-ta transformers torch` then create `data/tickers.csv` with TSX and TSX-V small-cap listings. Start in the `stock-screener` folder and run `/session-start` to load this context.
