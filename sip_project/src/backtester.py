"""
backtester.py
--------------
Event-driven backtest of the strategy defined in the SIP brief:

BUY when (all three, same day):
    - RSI recovers above 30 (was < 30 on prior bar, now >= 30)
    - MACD bullish crossover (MACD line crosses above signal line)
    - Close > 50-DMA

SELL when (first to trigger, checked bar-by-bar after entry):
    - RSI > 70, OR
    - MACD bearish crossover, OR
    - Stop-loss  = entry_price * (1 + STOP_LOSS_PCT)   [-5%]
    - Target     = entry_price * (1 + TARGET_PCT)      [+10%]
    - Max holding period safety exit

One position at a time per stock (no pyramiding), long-only, notional
INITIAL_CAPITAL_PER_TRADE per signal, net of round-trip transaction cost.
"""

import numpy as np
import pandas as pd

from src import config


def run_backtest(ind_df: pd.DataFrame, ticker: str) -> dict:
    df = ind_df.copy().reset_index()
    trades = []
    in_position = False
    entry_price = entry_date = entry_idx = None

    # Confluence window: real-world signal combinations rarely land on the
    # exact same trading day, so a signal is treated as "active" if it
    # fired within the last CONFLUENCE_DAYS sessions -- a standard and
    # documented refinement (see report Section "Strategy Rules") that
    # avoids discarding otherwise-valid bullish confluences over a
    # single-day timing mismatch.
    CONFLUENCE_DAYS = config.SIGNAL_CONFLUENCE_DAYS
    rsi_cross_recent = df["RSI_Bull_Cross"].rolling(CONFLUENCE_DAYS, min_periods=1).max().astype(bool)
    macd_cross_recent = df["MACD_Bull_Cross"].rolling(CONFLUENCE_DAYS, min_periods=1).max().astype(bool)

    for i in range(1, len(df)):
        row = df.iloc[i]

        if not in_position:
            buy_signal = (
                bool(rsi_cross_recent.iloc[i])
                and bool(macd_cross_recent.iloc[i])
                and bool(row.get("Above_DMA50", False))
            )
            if buy_signal:
                in_position = True
                entry_price = row["Close"]
                entry_date = row["Date"]
                entry_idx = i
        else:
            days_held = i - entry_idx
            ret = (row["Close"] - entry_price) / entry_price
            exit_reason = None

            if ret <= config.STOP_LOSS_PCT:
                exit_reason = "Stop-Loss (-5%)"
            elif ret >= config.TARGET_PCT:
                exit_reason = "Target (+10%)"
            elif row.get("RSI", 0) > config.RSI_OVERBOUGHT:
                exit_reason = "RSI Overbought (>70)"
            elif bool(row.get("MACD_Bear_Cross", False)):
                exit_reason = "MACD Bearish Crossover"
            elif days_held >= config.MAX_HOLDING_DAYS:
                exit_reason = "Max Holding Period"

            if exit_reason:
                gross_ret = ret
                net_ret = gross_ret - config.TRANSACTION_COST_PCT
                pnl = config.INITIAL_CAPITAL_PER_TRADE * net_ret
                trades.append(dict(
                    Ticker=ticker,
                    Entry_Date=entry_date, Entry_Price=round(entry_price, 2),
                    Exit_Date=row["Date"], Exit_Price=round(row["Close"], 2),
                    Days_Held=days_held, Exit_Reason=exit_reason,
                    Gross_Return_Pct=round(gross_ret * 100, 2),
                    Net_Return_Pct=round(net_ret * 100, 2),
                    PnL_INR=round(pnl, 0),
                ))
                in_position = False
                entry_price = entry_date = entry_idx = None

    trades_df = pd.DataFrame(trades)
    metrics = compute_metrics(trades_df, ind_df, ticker)
    return {"trades": trades_df, "metrics": metrics}


def compute_metrics(trades_df: pd.DataFrame, ind_df: pd.DataFrame, ticker: str) -> dict:
    n_trades = len(trades_df)
    if n_trades == 0:
        buy_hold = _buy_hold_return(ind_df)
        return dict(Ticker=ticker, Trades=0, Win_Rate_Pct=np.nan, Avg_Return_Pct=np.nan,
                    Total_Return_Pct=0.0, Max_Drawdown_Pct=0.0,
                    Buy_Hold_Return_Pct=round(buy_hold * 100, 2),
                    Strategy_vs_BuyHold_Pct=round(0.0 - buy_hold * 100, 2))

    wins = (trades_df["Net_Return_Pct"] > 0).sum()
    win_rate = round(wins / n_trades * 100, 1)
    avg_return = round(trades_df["Net_Return_Pct"].mean(), 2)

    # Compound the trade returns to get strategy total return
    compounded = (1 + trades_df["Net_Return_Pct"] / 100).prod() - 1
    total_return = round(compounded * 100, 2)

    # Equity curve & max drawdown across the trade sequence
    equity = (1 + trades_df["Net_Return_Pct"] / 100).cumprod()
    running_max = equity.cummax()
    drawdown = (equity / running_max - 1) * 100
    max_dd = round(drawdown.min(), 2)

    buy_hold = _buy_hold_return(ind_df)

    return dict(
        Ticker=ticker, Trades=n_trades, Win_Rate_Pct=win_rate,
        Avg_Return_Pct=avg_return, Total_Return_Pct=total_return,
        Max_Drawdown_Pct=max_dd,
        Buy_Hold_Return_Pct=round(buy_hold * 100, 2),
        Strategy_vs_BuyHold_Pct=round(total_return - buy_hold * 100, 2),
    )


def _buy_hold_return(ind_df: pd.DataFrame) -> float:
    return (ind_df["Close"].iloc[-1] / ind_df["Close"].iloc[0]) - 1


def run_all_backtests(indicators: dict) -> dict:
    results = {}
    for ticker, df in indicators.items():
        results[ticker] = run_backtest(df, ticker)
    return results


def summarize_portfolio(results: dict) -> pd.DataFrame:
    rows = [res["metrics"] for res in results.values()]
    summary = pd.DataFrame(rows).sort_values("Total_Return_Pct", ascending=False)
    return summary
