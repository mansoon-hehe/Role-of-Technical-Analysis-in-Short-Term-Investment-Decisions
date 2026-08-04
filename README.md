📊 An automated equity research pipeline that answers a simple question: does short-term 
technical trading add value on top of fundamentally sound stocks? Built for an MBA Summer 
Internship Project on 6 NIFTY-50 constituents (Reliance, TCS, HDFC Bank, Infosys, ICICI Bank, 
ITC), this repo pulls live NSE price data via yfinance, computes RSI/MACD/moving-average 
signals, backtests a rule-based strategy against buy-and-hold, screens the same universe on 
PE/ROE/Debt-Equity/growth, and produces a weighted Overall Investment Score — all wired into 
one command (`python main.py`) that regenerates every chart, table, and finding from scratch.
