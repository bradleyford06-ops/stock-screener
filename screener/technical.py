import pandas as pd
import ta
import logging

logger = logging.getLogger(__name__)


def compute_technicals(history):
    """Calculate RSI, moving averages, volume ratio, and breakout signals from price history."""
    try:
        df = history.copy()

        # Drop rows where both Close and Volume are NaN (incomplete intraday bars)
        df = df.dropna(subset=["Close"])
        if df.empty:
            return {}

        close = df["Close"]
        volume = df["Volume"].fillna(0)

        signals = {}

        # RSI (14-day)
        rsi_series = ta.momentum.RSIIndicator(close, window=14).rsi()
        rsi_val = rsi_series.dropna()
        signals["rsi"] = round(float(rsi_val.iloc[-1]), 2) if not rsi_val.empty else None

        # 50-day and 200-day moving averages
        if len(close) >= 50:
            ma50_val = close.rolling(50).mean().dropna()
            signals["ma50"] = round(float(ma50_val.iloc[-1]), 4) if not ma50_val.empty else None
        else:
            signals["ma50"] = None

        if len(close) >= 200:
            ma200_val = close.rolling(200).mean().dropna()
            signals["ma200"] = round(float(ma200_val.iloc[-1]), 4) if not ma200_val.empty else None
        else:
            signals["ma200"] = None

        # Golden cross: 50-day MA above 200-day MA
        if signals.get("ma50") and signals.get("ma200"):
            signals["golden_cross"] = signals["ma50"] > signals["ma200"]
        else:
            signals["golden_cross"] = False

        # Current price — last valid close
        signals["price"] = round(float(close.iloc[-1]), 4)

        # 52-week high — price breaking resistance
        high_52w = close.tail(252).max()
        signals["near_52w_high"] = signals["price"] >= high_52w * 0.95

        # Volume surge: most recent completed day vs 20-day average
        recent_volume = volume.iloc[-1]
        avg_vol_20 = volume.iloc[-21:-1].mean() if len(volume) > 21 else volume.mean()
        if avg_vol_20 > 0:
            signals["volume_ratio"] = round(float(recent_volume / avg_vol_20), 2)
        else:
            signals["volume_ratio"] = 0.0

        signals["volume_surge"] = signals["volume_ratio"] >= 3.0

        # Price momentum: % change over last 10 trading days
        if len(close) >= 10:
            signals["momentum_10d"] = round(float((close.iloc[-1] / close.iloc[-10] - 1) * 100), 2)
        else:
            signals["momentum_10d"] = 0.0

        # Bollinger band breakout (price above upper band)
        if len(close) >= 20:
            bb = ta.volatility.BollingerBands(close, window=20, window_dev=2)
            upper_band = bb.bollinger_hband().dropna()
            if not upper_band.empty:
                signals["bb_breakout"] = signals["price"] >= float(upper_band.iloc[-1])
            else:
                signals["bb_breakout"] = False
        else:
            signals["bb_breakout"] = False

        return signals

    except Exception as e:
        logger.warning(f"Technical analysis error: {e}")
        return {}
