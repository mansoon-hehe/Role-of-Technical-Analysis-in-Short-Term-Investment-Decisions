"""
visualization.py
------------------
All chart-generation logic. Uses `mplfinance` for candlesticks when
available (as specified in the project brief); otherwise falls back to
a hand-built OHLC candlestick renderer using only matplotlib so the
pipeline still produces publication-quality output in restricted
environments.
"""

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D

try:
    import mplfinance as mpf
    HAS_MPF = True
except ImportError:
    HAS_MPF = False

plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "axes.edgecolor": "#333333",
    "axes.grid": True,
    "grid.alpha": 0.25,
    "font.size": 10,
    "axes.titleweight": "bold",
})

UP_COLOR = "#1f9d55"
DOWN_COLOR = "#d64545"
BUY_COLOR = "#0b7a0b"
SELL_COLOR = "#b32424"


def _draw_candles(ax, df: pd.DataFrame):
    dates_num = mdates.date2num(df.index.to_pydatetime())
    width = 0.6 * (dates_num[1] - dates_num[0]) if len(dates_num) > 1 else 0.6
    for x, (_, row) in zip(dates_num, df.iterrows()):
        color = UP_COLOR if row["Close"] >= row["Open"] else DOWN_COLOR
        ax.plot([x, x], [row["Low"], row["High"]], color=color, linewidth=0.6, zorder=2)
        rect = Rectangle(
            (x - width / 2, min(row["Open"], row["Close"])),
            width, max(abs(row["Close"] - row["Open"]), 0.01),
            facecolor=color, edgecolor=color, zorder=3,
        )
        ax.add_patch(rect)
    ax.xaxis_date()


def plot_technical_dashboard(ind_df: pd.DataFrame, trades_df: pd.DataFrame,
                              ticker: str, name: str, out_path: str, months_shown=9):
    """Candlestick + DMAs + buy/sell arrows (top), RSI (middle), MACD (bottom)."""
    df = ind_df.tail(int(21 * months_shown)).copy()

    fig, (ax1, ax2, ax3) = plt.subplots(
        3, 1, figsize=(14, 11), sharex=True,
        gridspec_kw={"height_ratios": [3, 1, 1]},
    )

    # ---- Panel 1: Candles + DMAs + volume shading + signals ----
    _draw_candles(ax1, df)
    ax1.plot(df.index, df["DMA20"], color="#2b6cb0", linewidth=1.3, label="20-DMA")
    ax1.plot(df.index, df["DMA50"], color="#d69e2e", linewidth=1.3, label="50-DMA")
    ax1.plot(df.index, df["DMA200"], color="#805ad5", linewidth=1.3, label="200-DMA")

    if trades_df is not None and not trades_df.empty:
        window_start = df.index.min()
        tdf = trades_df[trades_df["Entry_Date"] >= window_start]
        for _, tr in tdf.iterrows():
            ax1.annotate("BUY", xy=(tr["Entry_Date"], tr["Entry_Price"]),
                         xytext=(0, -28), textcoords="offset points",
                         ha="center", fontsize=8, fontweight="bold", color="white",
                         arrowprops=dict(facecolor=BUY_COLOR, edgecolor=BUY_COLOR,
                                          arrowstyle="-|>", lw=1.5),
                         bbox=dict(boxstyle="round,pad=0.2", fc=BUY_COLOR, ec="none"))
            if tr["Exit_Date"] >= window_start:
                ax1.annotate("SELL", xy=(tr["Exit_Date"], tr["Exit_Price"]),
                             xytext=(0, 28), textcoords="offset points",
                             ha="center", fontsize=8, fontweight="bold", color="white",
                             arrowprops=dict(facecolor=SELL_COLOR, edgecolor=SELL_COLOR,
                                              arrowstyle="-|>", lw=1.5),
                             bbox=dict(boxstyle="round,pad=0.2", fc=SELL_COLOR, ec="none"))

    ax1.set_title(f"{name} ({ticker.replace('.NS','')}) — Price Action, Moving Averages & Trade Signals")
    ax1.set_ylabel("Price (₹)")
    ax1.legend(loc="upper left", fontsize=8, ncol=4, frameon=False)

    # ---- Panel 2: RSI ----
    ax2.plot(df.index, df["RSI"], color="#2b6cb0", linewidth=1.2)
    ax2.axhline(70, color=DOWN_COLOR, linestyle="--", linewidth=1)
    ax2.axhline(30, color=UP_COLOR, linestyle="--", linewidth=1)
    ax2.fill_between(df.index, 70, 100, color=DOWN_COLOR, alpha=0.08)
    ax2.fill_between(df.index, 0, 30, color=UP_COLOR, alpha=0.08)
    ax2.set_ylim(0, 100)
    ax2.set_ylabel("RSI (14)")
    ax2.set_title("Relative Strength Index — Overbought (>70) / Oversold (<30) Zones", fontsize=10)

    # ---- Panel 3: MACD ----
    colors = np.where(df["MACD_Hist"] >= 0, UP_COLOR, DOWN_COLOR)
    ax3.bar(df.index, df["MACD_Hist"], color=colors, width=0.8, alpha=0.6, label="Histogram")
    ax3.plot(df.index, df["MACD"], color="#2b6cb0", linewidth=1.2, label="MACD")
    ax3.plot(df.index, df["MACD_Signal"], color="#d69e2e", linewidth=1.2, label="Signal")
    ax3.axhline(0, color="#333333", linewidth=0.8)
    ax3.set_ylabel("MACD")
    ax3.set_title("MACD (12,26,9) — Trend Momentum", fontsize=10)
    ax3.legend(loc="upper left", fontsize=8, ncol=3, frameon=False)

    ax3.xaxis.set_major_formatter(mdates.DateFormatter("%b-%y"))
    plt.setp(ax3.get_xticklabels(), rotation=0)

    fig.tight_layout()
    fig.savefig(out_path, dpi=160, bbox_inches="tight")
    plt.close(fig)


def plot_strategy_vs_buyhold(trades_df: pd.DataFrame, ind_df: pd.DataFrame,
                              ticker: str, name: str, out_path: str):
    fig, ax = plt.subplots(figsize=(10, 5.5))

    bh = ind_df["Close"] / ind_df["Close"].iloc[0] * 100
    ax.plot(bh.index, bh.values, color="#4a5568", linewidth=1.6, label="Buy & Hold")

    if trades_df is not None and not trades_df.empty:
        eq = [100.0]
        eq_dates = [ind_df.index[0]]
        for _, tr in trades_df.iterrows():
            eq.append(eq[-1] * (1 + tr["Net_Return_Pct"] / 100))
            eq_dates.append(tr["Exit_Date"])
        eq.append(eq[-1])
        eq_dates.append(ind_df.index[-1])
        ax.step(eq_dates, eq, color="#0b7a0b", linewidth=2.0, where="post",
                 label="Technical Strategy (compounded)")

    ax.set_title(f"{name} — Strategy vs. Buy & Hold (Base = 100)")
    ax.set_ylabel("Indexed Value")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(out_path, dpi=160, bbox_inches="tight")
    plt.close(fig)


def plot_score_heatmap(score_df: pd.DataFrame, out_path: str):
    cols = ["Score_PE", "Score_ROE", "Score_DE", "Score_RevGrowth", "Score_EPSGrowth", "Score_Technical"]
    labels = ["PE (20%)", "ROE (20%)", "Debt/Eq (15%)", "Rev Growth (15%)", "EPS Growth (15%)", "Technical (15%)"]
    data = score_df[cols].values
    tickers = [t.replace(".NS", "") for t in score_df.index]

    fig, ax = plt.subplots(figsize=(9, 5.5))
    im = ax.imshow(data, cmap="RdYlGn", vmin=0, vmax=100, aspect="auto")
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=30, ha="right")
    ax.set_yticks(range(len(tickers)))
    ax.set_yticklabels(tickers)
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            ax.text(j, i, f"{data[i,j]:.0f}", ha="center", va="center",
                     color="black", fontsize=9)
    ax.set_title("Fundamental + Technical Sub-Score Heatmap (0–100 percentile)")
    cbar = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.03)
    cbar.set_label("Score")
    fig.tight_layout()
    fig.savefig(out_path, dpi=160, bbox_inches="tight")
    plt.close(fig)


def plot_ranking_bar(score_df: pd.DataFrame, out_path: str):
    df = score_df.sort_values("Overall_Score", ascending=True)
    colors = ["#1f9d55" if r == "BUY" else "#68a63f" if r == "ACCUMULATE"
              else "#d69e2e" if r == "HOLD" else "#d64545" for r in df["Recommendation"]]

    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.barh([t.replace(".NS", "") for t in df.index], df["Overall_Score"], color=colors)
    for bar, score, rec in zip(bars, df["Overall_Score"], df["Recommendation"]):
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height() / 2,
                 f"{score:.1f}  ({rec})", va="center", fontsize=9)
    ax.set_xlim(0, 100)
    ax.set_xlabel("Overall Investment Score (0–100)")
    ax.set_title("Stock Ranking — Overall Investment Score")
    fig.tight_layout()
    fig.savefig(out_path, dpi=160, bbox_inches="tight")
    plt.close(fig)


def plot_portfolio_dashboard(portfolio_summary: pd.DataFrame, score_df: pd.DataFrame, out_path: str):
    fig, axes = plt.subplots(2, 2, figsize=(13, 9))

    # (1) Win rate by stock
    ax = axes[0, 0]
    ps = portfolio_summary.set_index("Ticker")
    tickers_short = [t.replace(".NS", "") for t in ps.index]
    ax.bar(tickers_short, ps["Win_Rate_Pct"], color="#2b6cb0")
    ax.set_title("Strategy Win Rate by Stock")
    ax.set_ylabel("Win Rate (%)")
    ax.set_ylim(0, 100)

    # (2) Total return: Strategy vs Buy&Hold
    ax = axes[0, 1]
    x = np.arange(len(ps))
    width = 0.35
    ax.bar(x - width / 2, ps["Total_Return_Pct"], width, label="Strategy", color="#0b7a0b")
    ax.bar(x + width / 2, ps["Buy_Hold_Return_Pct"], width, label="Buy & Hold", color="#4a5568")
    ax.set_xticks(x); ax.set_xticklabels(tickers_short)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_title("Total Return: Strategy vs Buy & Hold")
    ax.set_ylabel("Return (%)")
    ax.legend(frameon=False, fontsize=8)

    # (3) Max drawdown
    ax = axes[1, 0]
    ax.bar(tickers_short, ps["Max_Drawdown_Pct"], color="#d64545")
    ax.set_title("Maximum Drawdown by Stock (Strategy Equity Curve)")
    ax.set_ylabel("Max Drawdown (%)")

    # (4) Overall investment score
    ax = axes[1, 1]
    sd = score_df.reindex(ps.index) if set(ps.index).issubset(score_df.index) else score_df
    ax.bar([t.replace(".NS", "") for t in sd.index], sd["Overall_Score"], color="#805ad5")
    ax.set_title("Overall Investment Score")
    ax.set_ylabel("Score (0–100)")
    ax.set_ylim(0, 100)

    fig.suptitle("Portfolio-Level Performance Dashboard", fontsize=14, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(out_path, dpi=160, bbox_inches="tight")
    plt.close(fig)
