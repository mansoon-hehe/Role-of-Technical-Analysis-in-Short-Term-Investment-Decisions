# Role of Technical Analysis in Short-Term Investment Decisions
### A Study of Selected NIFTY Stocks Using Fundamental Filters
**MBA Summer Internship Project — Equity Research / Quantitative Finance**

A fully automated Python pipeline that combines **technical analysis**, **fundamental screening**,
**rule-based backtesting**, and **data visualization** to produce a ranked, data-driven investment
recommendation across six NIFTY-50 stocks: **Reliance, TCS, HDFC Bank, Infosys, ICICI Bank, and ITC**.

📄 **Full report:** [`outputs/report/SIP_Dissertation_Report.docx`](outputs/report/SIP_Dissertation_Report.docx)

---

## What this project does

1. **Downloads** 2 years of daily OHLCV price data via `yfinance`.
2. **Computes** RSI(14), MACD(12,26,9), and 20/50/200-day moving averages.
3. **Backtests** a mechanical strategy:
   - **BUY:** RSI recovers above 30 + MACD bullish crossover + price above 50-DMA
   - **SELL:** RSI > 70, OR MACD bearish crossover, OR -5% stop-loss, OR +10% target
4. **Screens** the same universe on PE, ROE, Debt/Equity, Revenue Growth, EPS Growth, Market Cap.
5. **Scores** every stock with a weighted composite Overall Investment Score (0–100) and
   recommendation (BUY / ACCUMULATE / HOLD / AVOID).
6. **Renders** publication-quality charts: candlesticks with buy/sell arrows, RSI/MACD panels,
   a fundamental score heatmap, a ranking chart, and a 4-panel portfolio dashboard.
7. **Writes** a full MBA-dissertation-quality Word report with per-company analyst commentary.

## Quick start

```bash
pip install -r requirements.txt
python main.py
```

Outputs land in `outputs/charts/` (15 PNGs) and `outputs/tables/` (8 CSVs). Runtime: under a minute.

## Project structure

```
├── README.md
├── requirements.txt
├── main.py                       # pipeline entry point
├── build_report.js               # generates the Word dissertation report (Node + docx)
├── src/
│   ├── config.py                 # universe, indicator params, strategy rules, scoring weights
│   ├── data_loader.py            # yfinance download + calibrated fallback simulator
│   ├── technical_indicators.py   # RSI, MACD, DMA, crossover/zone detection
│   ├── fundamental_analysis.py   # sourced fundamental data
│   ├── scoring_model.py          # percentile scoring + weighted Overall Investment Score
│   ├── backtester.py             # rule-based strategy engine + performance metrics
│   └── visualization.py          # all chart generation
├── data/                         # cached OHLCV CSVs
└── outputs/
    ├── charts/
    ├── tables/
    └── report/SIP_Dissertation_Report.docx
```

## Key design notes

- **Graceful degradation:** every module falls back to a hand-written implementation
  (RSI/MACD formulas, a custom candlestick renderer) if `ta` / `mplfinance` aren't installed,
  so the pipeline never breaks in a constrained environment.
- **Single source of config:** all thresholds, weights, and the stock universe live in
  `src/config.py` — re-run the whole study on a different stock list or parameter set by
  editing one file.
- **Data provenance is explicit:** `data_loader.py` labels every dataset with its actual source
  (`"yfinance (live NSE data)"` vs. a calibrated-fallback label) so results are always auditable.
  See **Appendix A** of the report for the full disclosure on how this specific report copy's
  demo data was generated in a network-restricted authoring sandbox.

## Requirements

See `requirements.txt`. Core stack: `yfinance`, `pandas`, `numpy`, `matplotlib`, `mplfinance`, `ta`.

## Disclaimer

This project is an academic exercise prepared for an MBA Summer Internship Project. Nothing
here constitutes investment advice. Past/backtested performance is not indicative of future results.
