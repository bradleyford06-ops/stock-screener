import smtplib
import os
import json
import argparse
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

RECIPIENT = "bradleyford5@hotmail.com"
SENDER = os.getenv("GMAIL_ADDRESS")
APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")


def send_email(subject, body, recipient=RECIPIENT):
    """Send a plain-text email via Gmail SMTP using an app password from .env."""
    if not SENDER or not APP_PASSWORD:
        raise EnvironmentError("GMAIL_ADDRESS and GMAIL_APP_PASSWORD must be set in .env")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = SENDER
    msg["To"] = recipient
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SENDER, APP_PASSWORD)
        server.sendmail(SENDER, recipient, msg.as_string())

    logger.info(f"Email sent to {recipient}")


def send_report(top_stocks, previous_symbols=None):
    """Format and send the screener report email."""
    from email_report.formatter import format_email
    body = format_email(top_stocks, previous_symbols)
    today = datetime.now().strftime("%b %d")
    subject = f"Small-Cap Stock Screener — {today}"
    send_email(subject, body)
    return body


def send_test_email():
    """Send a test email with fake data to verify email delivery is working."""
    fake_stocks = [
        {
            "symbol": "TST.V",
            "name": "Test Resources Inc",
            "strategy": "Swing Trade",
            "price": 0.85,
            "composite_score": 72.5,
            "signals": {
                "rsi": 63.2,
                "volume_ratio": 4.1,
                "near_52w_high": True,
                "golden_cross": True,
                "bb_breakout": False,
                "momentum_10d": 12.5,
            },
            "fundamentals": {
                "revenue_growth": 0.35,
                "cash": 5000000,
                "total_debt": 1000000,
            },
            "sentiment_score": 0.42,
            "headlines": [
                "Test Resources reports strong Q3 results",
                "Analysts upgrade TST.V on exploration success",
            ],
        }
    ]
    body = send_report(fake_stocks)
    print("Test email sent successfully.")
    print("\n--- Email Preview ---")
    print(body)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true", help="Send a test email")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    if args.test:
        send_test_email()
