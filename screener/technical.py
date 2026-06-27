import pandas as pd
import ta
import logging

logger = logging.getLogger(__name__)


def compute_technicals(history):
    """Calculate RSI, moving averages, volume ratio, and breakout signals from price history."""
    try:
        df = history.copy()
        close = df["Close"]
        volume = df["Volume"]

        signals = {}

        # RSI (14-day)
        rsi_series = ta.momentum.RSIIndicator(close, window=14).rsi()
        signals["rsi"] = round(float(rsi_series.iloc[-1]), 2) if not rsi_series.empty else None

        # 50-day and 200-day moving averages
        if len(close) >= 50:
            signals["ma50"] = round(float(close.rolling(50).mean().iloc[-1]), 4)
        else:
            signals["ma50"] = None

        if len(close) >= 200:
            signals["ma200"] = round(float(close.rolling(200).mean().iloc[-1]), 4)
        else:
            signals["ma200"] = None

        # Golden cross: 50-day MA above 200-day MA
        if signals["ma50"] and signals["ma200"]:
            signals["golden_cross"] = signals["ma50"] > signals["ma200"]
        else:
            signals["golden_cross"] = False

        # Current price
        signals["price"] = round(float(close.iloc[-1]), 4)

        # 52-week high — price breaking resistance
        high_52w = close.tail(252).max()
        signals["near_52w_high"] = signals["price"] >= high_52w * 0.95

        # Volume surge: today vs 20-day average
        avg_vol_20 = volume.tail(21).iloc[:-1].mean()
        today_vol = volume.iloc[-1]
        if avg_vol_20 > 0:
            signals["volume_ratio"] = round(float(today_vol / avg_vol_20), 2)
        else:
            signals["volume_ratio"] = 0.0

        signals["volume_surge"] = signals["volume_ratio"] >= 3.0

        # Price momentum: % change over last 10 days
        if len(close) >= 10:
            signals["momentum_10d"] = round(float((close.iloc[-1] / close.iloc[-10] - 1) * 100), 2)
        else:
            signals["momentum_10d"] = 0.0

        # Bollinger band breakout (price above upper band)
        bb = ta.volatility.BollingerBands(close, window=20, window_dev=2)
        upper_band = bb.bollinger_hband().iloc[-1]
        signals["bb_breakout"] = signals["price"] >= upper_band

        return signals

    except Exception as e:
        logger.warning(f"Technical analysis error: {e}")
        return {}
