"""
technical_indicators.py
------------------------
Computes RSI(14), MACD(12,26,9), 20/50/200-DMA, and volume-based
signals for a price DataFrame. Uses the `ta` library when available
(preferred, as specified in the project brief); otherwise falls back
to hand-written implementations of the identical Wilder/standard
formulas so the pipeline never breaks in a restricted environment.
"""

import numpy as np
import pandas as pd

try:
    from ta.momentum import RSIIndicator
    from ta.trend import MACD as TA_MACD
    HAS_TA = True
except ImportError:
    HAS_TA = False


def add_moving_averages(df: pd.DataFrame, windows=(20, 50, 200)) -> pd.DataFrame:
    out = df.copy()
    for w in windows:
        out[f"DMA{w}"] = out["Close"].rolling(window=w, min_periods=max(2, w // 3)).mean()
    return out


def _rsi_manual(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50)


def add_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    out = df.copy()
    if HAS_TA:
        out["RSI"] = RSIIndicator(close=out["Close"], window=period).rsi()
    else:
        out["RSI"] = _rsi_manual(out["Close"], period)
    return out


def _macd_manual(close: pd.Series, fast=12, slow=26, signal=9):
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    hist = macd_line - signal_line
    return macd_line, signal_line, hist


def add_macd(df: pd.DataFrame, fast=12, slow=26, signal=9) -> pd.DataFrame:
    out = df.copy()
    if HAS_TA:
        macd_obj = TA_MACD(close=out["Close"], window_fast=fast, window_slow=slow, window_sign=signal)
        out["MACD"] = macd_obj.macd()
        out["MACD_Signal"] = macd_obj.macd_signal()
        out["MACD_Hist"] = macd_obj.macd_diff()
    else:
        macd_line, signal_line, hist = _macd_manual(out["Close"], fast, slow, signal)
        out["MACD"], out["MACD_Signal"], out["MACD_Hist"] = macd_line, signal_line, hist
    return out


def add_all_indicators(df: pd.DataFrame, rsi_period=14, dma_windows=(20, 50, 200),
                        macd_params=(12, 26, 9)) -> pd.DataFrame:
    out = add_moving_averages(df, dma_windows)
    out = add_rsi(out, rsi_period)
    out = add_macd(out, *macd_params)
    out["Vol_Avg20"] = out["Volume"].rolling(20, min_periods=5).mean()
    return out


def flag_crossovers_and_zones(df: pd.DataFrame, ob=70, os_=30) -> pd.DataFrame:
    """Adds boolean flags for the exact events the strategy trades on."""
    out = df.copy()

    # RSI regime flags
    out["RSI_Oversold"] = out["RSI"] < os_
    out["RSI_Overbought"] = out["RSI"] > ob
    # RSI recovery cross: was below 30 yesterday, now back above 30
    out["RSI_Bull_Cross"] = (out["RSI"].shift(1) < os_) & (out["RSI"] >= os_)
    out["RSI_Bear_Cross"] = (out["RSI"].shift(1) > ob) & (out["RSI"] <= ob)

    # MACD crossovers
    macd_diff = out["MACD"] - out["MACD_Signal"]
    macd_diff_prev = macd_diff.shift(1)
    out["MACD_Bull_Cross"] = (macd_diff_prev < 0) & (macd_diff >= 0)
    out["MACD_Bear_Cross"] = (macd_diff_prev > 0) & (macd_diff <= 0)

    # Trend filter
    out["Above_DMA50"] = out["Close"] > out["DMA50"]
    out["Golden_Cross"] = (out["DMA50"].shift(1) < out["DMA200"].shift(1)) & (out["DMA50"] >= out["DMA200"])
    out["Death_Cross"] = (out["DMA50"].shift(1) > out["DMA200"].shift(1)) & (out["DMA50"] <= out["DMA200"])

    return out
