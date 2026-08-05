"""
config.py
---------
Central configuration for the SIP project.
Edit this file to change the stock universe, date range, indicator
parameters, backtest rules, or fundamental-scoring weights without
touching any other module.
"""

from datetime import datetime, timedelta

# ----------------------------------------------------------------------
# 1. STOCK UNIVERSE
#    Six NIFTY-50 constituents chosen to span four sectors so the study
#    is not biased toward one industry's technical behaviour:
#    Energy/Conglomerate, IT Services (x2), Private Banking (x2), FMCG.
# ----------------------------------------------------------------------
NIFTY_STOCKS = {
    "RELIANCE.NS": "Reliance Industries Ltd",
    "TCS.NS":       "Tata Consultancy Services Ltd",
    "HDFCBANK.NS":  "HDFC Bank Ltd",
    "INFY.NS":      "Infosys Ltd",
    "ICICIBANK.NS": "ICICI Bank Ltd",
    "ITC.NS":       "ITC Ltd",
}

SECTOR_MAP = {
    "RELIANCE.NS": "Energy / Conglomerate",
    "TCS.NS":       "Information Technology",
    "HDFCBANK.NS":  "Private Sector Banking",
    "INFY.NS":      "Information Technology",
    "ICICIBANK.NS": "Private Sector Banking",
    "ITC.NS":       "FMCG",
}

# ----------------------------------------------------------------------
# 2. DATA WINDOW
# ----------------------------------------------------------------------
END_DATE = datetime(2026, 6, 30)              # last trading day used
LOOKBACK_YEARS = 2
START_DATE = END_DATE - timedelta(days=int(365.25 * LOOKBACK_YEARS))
INTERVAL = "1d"

# ----------------------------------------------------------------------
# 3. TECHNICAL INDICATOR PARAMETERS
# ----------------------------------------------------------------------
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30

MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

DMA_SHORT = 20
DMA_MEDIUM = 50
DMA_LONG = 200

# ----------------------------------------------------------------------
# 4. BACKTEST / TRADING RULES
# ----------------------------------------------------------------------
INITIAL_CAPITAL_PER_TRADE = 100000          # INR, notional per signal
STOP_LOSS_PCT = -0.05                       # -5%
TARGET_PCT = 0.10                           # +10%
MAX_HOLDING_DAYS = 60                       # safety exit if neither hits
TRANSACTION_COST_PCT = 0.0015               # 15 bps round-trip (brokerage+STT+slippage)
SIGNAL_CONFLUENCE_DAYS = 7                  # RSI-cross and MACD-cross must both fire within this many sessions

# BUY when: RSI crosses back above 30 from oversold territory,
#           AND MACD line crosses above signal line (bullish crossover),
#           AND Close > 50-DMA (medium-term uptrend confirmation)
# SELL when: RSI > 70 (overbought) OR MACD bearish crossover
#            OR stop-loss / target hit (whichever first)

# ----------------------------------------------------------------------
# 5. FUNDAMENTAL SCORING MODEL WEIGHTS  (sum = 100%)
# ----------------------------------------------------------------------
SCORE_WEIGHTS = {
    "PE":         0.20,
    "ROE":        0.20,
    "DEBT_EQUITY": 0.15,
    "REVENUE_GROWTH": 0.15,
    "EPS_GROWTH": 0.15,
    "TECHNICAL":  0.15,
}
assert abs(sum(SCORE_WEIGHTS.values()) - 1.0) < 1e-9, "Weights must sum to 100%"

# ----------------------------------------------------------------------
# 6. OUTPUT PATHS
# ----------------------------------------------------------------------
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
CHART_DIR = os.path.join(BASE_DIR, "outputs", "charts")
TABLE_DIR = os.path.join(BASE_DIR, "outputs", "tables")
REPORT_DIR = os.path.join(BASE_DIR, "outputs", "report")

for _d in (DATA_DIR, CHART_DIR, TABLE_DIR, REPORT_DIR):
    os.makedirs(_d, exist_ok=True)
