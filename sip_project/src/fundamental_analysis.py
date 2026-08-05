"""
fundamental_analysis.py
-------------------------
Fundamental data for the six-stock universe.

Figures below are REAL, sourced from public financial data providers
(stockanalysis.com / S&P Global Market Intelligence, screener.in,
valueresearchonline.com), captured between 27-Jun-2026 and 03-Aug-2026
(TTM / FY2026 basis, consolidated). Each row cites its data date.

For a production/live deployment, replace `get_fundamentals()` with a
call to a paid data API (e.g. screener.in API, Refinitiv, Bloomberg) or
scrape a fixed provider on a schedule -- the scoring model downstream
does not care where the numbers come from as long as the schema matches.
"""

import pandas as pd

FUNDAMENTALS = {
    # ticker:        PE,   ROE(%), D/E,  RevGrowth(%), EPSGrowth(%), MarketCap(INR Cr), AsOf
    "RELIANCE.NS": dict(pe=21.68, roe=9.14,  de=0.37, rev_growth=8.39,  eps_growth=34.63,
                         market_cap_cr=1_751_000, as_of="30-Jun-2026",
                         note="Analyst 3Y forward estimates used for growth (S&P Global)"),
    "TCS.NS":       dict(pe=18.19, roe=42.63, de=0.09, rev_growth=13.90, eps_growth=9.10,
                         market_cap_cr=855_895,  as_of="Jul-2026",
                         note="Rev growth = Q1 FY27 YoY; EPS growth = trailing 3Y avg (screener.in)"),
    "HDFCBANK.NS":  dict(pe=25.72, roe=13.82, de=1.89, rev_growth=3.84,  eps_growth=7.39,
                         market_cap_cr=1_507_000, as_of="Jun-2026",
                         note="Bank D/E reflects deposit-funded balance sheet, not comparable to non-financials"),
    "INFY.NS":      dict(pe=18.33, roe=32.68, de=0.11, rev_growth=5.10,  eps_growth=6.65,
                         market_cap_cr=613_000,  as_of="30-Jun-2026",
                         note="Growth = 3Y forward analyst consensus (SimplyWall.st/S&P Global)"),
    "ICICIBANK.NS": dict(pe=18.49, roe=18.23, de=1.02, rev_growth=19.34, eps_growth=6.23,
                         market_cap_cr=1_036_903, as_of="27-Jul-2026",
                         note="Bank D/E reflects deposit-funded balance sheet, not comparable to non-financials"),
    "ITC.NS":       dict(pe=18.27, roe=29.34, de=0.03, rev_growth=4.71,  eps_growth=-40.46,
                         market_cap_cr=524_000,  as_of="Jun-2026",
                         note="FY26 EPS decline driven by Hotels-business demerger (one-off), not core operating weakness"),
}


def get_fundamentals() -> pd.DataFrame:
    df = pd.DataFrame(FUNDAMENTALS).T
    df.index.name = "Ticker"
    for col in ["pe", "roe", "de", "rev_growth", "eps_growth", "market_cap_cr"]:
        df[col] = df[col].astype(float)
    return df


if __name__ == "__main__":
    print(get_fundamentals())
