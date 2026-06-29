#!/usr/bin/env python3
"""
Canadian Small-Cap Stock Screener
Run: python main.py           — screen and print results
Run: python main.py --send    — screen and send email to bradleyford5@hotmail.com
Run: python main.py --no-sentiment  — skip FinBERT (faster, good for testing)
"""

import argparse
import logging
import os
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

TICKERS_CSV = os.path.join(os.path.dirname(__file__), "data", "tickers.csv")


def main():
    parser = argparse.ArgumentParser(description="Canadian Small-Cap Stock Screener")
    parser.add_argument("--send", action="store_true", help="Send results by email")
    parser.add_argument("--no-sentiment", action="store_true", help="Skip FinBERT sentiment (faster)")
    parser.add_argument("--cache-only", action="store_true", help="Only use cached data, skip Yahoo Finance")
    args = parser.parse_args()

    from dotenv import load_dotenv
    load_dotenv()

    from screener.pipeline import run_screener, load_previous_symbols
    from email_report.formatter import format_email

    logger.info("Running screener...")
    previous_position_symbols = load_previous_symbols(strategy_filter="Position Trade")
    previous_swing_symbols = load_previous_symbols(strategy_filter="Swing Trade")

    top_stocks = run_screener(TICKERS_CSV, skip_sentiment=args.no_sentiment, cache_only=args.cache_only)

    if not top_stocks:
        logger.warning("No stocks passed the screening criteria today.")
        sys.exit(0)

    report = format_email(top_stocks, previous_position_symbols, previous_swing_symbols)
    print("\n" + report)

    if args.send:
        from email_report.send import send_report
        logger.info("Sending email...")
        send_report(top_stocks, previous_position_symbols, previous_swing_symbols)
        logger.info("Email sent to bradleyford5@hotmail.com")


if __name__ == "__main__":
    main()
