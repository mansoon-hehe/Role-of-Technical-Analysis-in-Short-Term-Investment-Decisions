"""
scoring_model.py
------------------
Builds the Overall Investment Score for each stock by blending
fundamental quality/valuation with the current technical posture.

Methodology
-----------
1. Each raw fundamental metric is converted to a 0-100 percentile
   score WITHIN THE PEER UNIVERSE (cross-sectional ranking), because
   absolute ratios are not comparable across sectors (e.g. bank D/E
   vs. FMCG D/E) but relative ranking within the chosen set is.
2. PE and Debt/Equity are "lower is better" -> percentile is inverted.
3. ROE, Revenue Growth, EPS Growth are "higher is better" -> direct
   percentile.
4. The Technical score (0-100) is derived from the latest indicator
   snapshot: trend position (price vs DMA50/DMA200), RSI regime, and
   MACD momentum -- i.e. "does the chart currently support a
   short-term entry", which is the technical-analysis contribution
   the SIP topic asks for.
5. Overall Score = weighted sum per config.SCORE_WEIGHTS.
"""

import numpy as np
import pandas as pd

from src import config


def _percentile_score(series: pd.Series, higher_is_better: bool = True) -> pd.Series:
    ranks = series.rank(pct=True, method="average")
    if not higher_is_better:
        ranks = 1 - ranks
    return (ranks * 100).round(1)


def score_fundamentals(fund_df: pd.DataFrame) -> pd.DataFrame:
    out = fund_df.copy()
    out["Score_PE"] = _percentile_score(out["pe"], higher_is_better=False)
    out["Score_ROE"] = _percentile_score(out["roe"], higher_is_better=True)
    out["Score_DE"] = _percentile_score(out["de"], higher_is_better=False)
    out["Score_RevGrowth"] = _percentile_score(out["rev_growth"], higher_is_better=True)
    out["Score_EPSGrowth"] = _percentile_score(out["eps_growth"], higher_is_better=True)
    return out


def technical_snapshot_score(ind_df: pd.DataFrame) -> float:
    """0-100 score reflecting the *current* technical posture of one stock."""
    last = ind_df.iloc[-1]
    score = 50.0  # neutral baseline

    # Trend component (+/-25)
    if last["Close"] > last["DMA200"]:
        score += 12.5
    else:
        score -= 12.5
    if last["Close"] > last["DMA50"]:
        score += 12.5
    else:
        score -= 12.5

    # RSI component (+/-15): reward the "not overbought, not deeply
    # oversold, recovering" zone that the strategy is designed to buy.
    rsi = last["RSI"]
    if 30 <= rsi <= 60:
        score += 15
    elif rsi > 70:
        score -= 15
    elif rsi < 30:
        score -= 5   # oversold = risk, but also potential setup; mild penalty

    # MACD momentum component (+/-10)
    if last["MACD"] > last["MACD_Signal"]:
        score += 10
    else:
        score -= 10

    return float(np.clip(score, 0, 100))


def build_score_table(fund_df: pd.DataFrame, indicators: dict) -> pd.DataFrame:
    scored = score_fundamentals(fund_df)
    scored["Score_Technical"] = [technical_snapshot_score(indicators[t]) for t in scored.index]

    w = config.SCORE_WEIGHTS
    scored["Overall_Score"] = (
        scored["Score_PE"] * w["PE"]
        + scored["Score_ROE"] * w["ROE"]
        + scored["Score_DE"] * w["DEBT_EQUITY"]
        + scored["Score_RevGrowth"] * w["REVENUE_GROWTH"]
        + scored["Score_EPSGrowth"] * w["EPS_GROWTH"]
        + scored["Score_Technical"] * w["TECHNICAL"]
    ).round(1)

    scored["Rank"] = scored["Overall_Score"].rank(ascending=False, method="min").astype(int)
    scored = scored.sort_values("Overall_Score", ascending=False)

    def recommendation(s):
        if s >= 70:
            return "BUY"
        elif s >= 55:
            return "ACCUMULATE"
        elif s >= 40:
            return "HOLD"
        else:
            return "AVOID / REDUCE"

    scored["Recommendation"] = scored["Overall_Score"].apply(recommendation)
    return scored
