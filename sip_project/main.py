"""
main.py
--------
End-to-end pipeline for the SIP:
"Role of Technical Analysis in Short-Term Investment Decisions:
A Study of Selected NIFTY Stocks Using Fundamental Filters"

Run:  python main.py
Outputs land in outputs/charts, outputs/tables.
"""

import os
import sys
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src import config, data_loader, technical_indicators as ti
from src import fundamental_analysis as fa
from src import scoring_model as sm
from src import backtester as bt
from src import visualization as viz


def main():
    print("=" * 70)
    print("SIP PIPELINE: Technical + Fundamental Analysis of NIFTY Stocks")
    print("=" * 70)

    # 1. DATA
    print("\n[1/6] Loading price history ...")
    raw = data_loader.load_all()
    for tkr, df in raw.items():
        print(f"   {tkr:<14} {df.shape[0]} bars | {df.attrs.get('source')}")

    # 2. INDICATORS
    print("\n[2/6] Computing technical indicators ...")
    indicators = {}
    for tkr, df in raw.items():
        d = ti.add_all_indicators(df, rsi_period=config.RSI_PERIOD,
                                   dma_windows=(config.DMA_SHORT, config.DMA_MEDIUM, config.DMA_LONG),
                                   macd_params=(config.MACD_FAST, config.MACD_SLOW, config.MACD_SIGNAL))
        d = ti.flag_crossovers_and_zones(d, ob=config.RSI_OVERBOUGHT, os_=config.RSI_OVERSOLD)
        indicators[tkr] = d
        d.to_csv(os.path.join(config.TABLE_DIR, f"indicators_{tkr.replace('.', '_')}.csv"))

    # 3. BACKTEST
    print("\n[3/6] Running rule-based backtests ...")
    bt_results = bt.run_all_backtests(indicators)
    portfolio_summary = bt.summarize_portfolio(bt_results)
    portfolio_summary.to_csv(os.path.join(config.TABLE_DIR, "backtest_summary.csv"), index=False)

    all_trades = pd.concat([r["trades"] for r in bt_results.values() if not r["trades"].empty],
                            ignore_index=True) if any(not r["trades"].empty for r in bt_results.values()) else pd.DataFrame()
    all_trades.to_csv(os.path.join(config.TABLE_DIR, "all_trades.csv"), index=False)
    print(portfolio_summary.to_string(index=False))

    # 4. FUNDAMENTALS + SCORING
    print("\n[4/6] Scoring fundamentals + technicals ...")
    fund_df = fa.get_fundamentals()
    score_df = sm.build_score_table(fund_df, indicators)
    score_df.to_csv(os.path.join(config.TABLE_DIR, "investment_scores.csv"))
    print(score_df[["Overall_Score", "Rank", "Recommendation"]].to_string())

    # 5. CHARTS
    print("\n[5/6] Rendering charts ...")
    for tkr, name in config.NIFTY_STOCKS.items():
        trades_df = bt_results[tkr]["trades"]
        viz.plot_technical_dashboard(
            indicators[tkr], trades_df, tkr, name,
            os.path.join(config.CHART_DIR, f"{tkr.replace('.', '_')}_technical.png"))
        viz.plot_strategy_vs_buyhold(
            trades_df, indicators[tkr], tkr, name,
            os.path.join(config.CHART_DIR, f"{tkr.replace('.', '_')}_strategy_vs_buyhold.png"))

    viz.plot_score_heatmap(score_df, os.path.join(config.CHART_DIR, "score_heatmap.png"))
    viz.plot_ranking_bar(score_df, os.path.join(config.CHART_DIR, "ranking_bar.png"))
    viz.plot_portfolio_dashboard(portfolio_summary, score_df,
                                  os.path.join(config.CHART_DIR, "portfolio_dashboard.png"))

    # 6. TOP-LEVEL FINDINGS
    print("\n[6/6] Key findings ...")
    best_stock = portfolio_summary.iloc[0]
    worst_stock = portfolio_summary.iloc[-1]
    outperform = (portfolio_summary["Strategy_vs_BuyHold_Pct"] > 0).sum()

    findings = {
        "Best_Performing_Stock": best_stock["Ticker"],
        "Best_Stock_Strategy_Return_Pct": best_stock["Total_Return_Pct"],
        "Worst_Performing_Stock": worst_stock["Ticker"],
        "Worst_Stock_Strategy_Return_Pct": worst_stock["Total_Return_Pct"],
        "Stocks_Where_Strategy_Beat_BuyHold": f"{outperform}/{len(portfolio_summary)}",
        "Avg_Win_Rate_Pct": round(portfolio_summary["Win_Rate_Pct"].mean(), 1),
        "Total_Trades_Generated": int(portfolio_summary["Trades"].sum()),
        "Top_Ranked_Investment": score_df.index[0],
        "Top_Ranked_Score": score_df["Overall_Score"].iloc[0],
    }
    pd.Series(findings).to_csv(os.path.join(config.TABLE_DIR, "key_findings.csv"))
    for k, v in findings.items():
        print(f"   {k}: {v}")

    print("\nDone. See outputs/charts and outputs/tables.")
    return dict(raw=raw, indicators=indicators, bt_results=bt_results,
                portfolio_summary=portfolio_summary, score_df=score_df,
                fund_df=fund_df, findings=findings)


if __name__ == "__main__":
    main()
